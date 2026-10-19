# -*- coding: utf-8 -*-
"""Camada de dialeto: SQLite (padrao) ou Azure SQL (opcional).

O Azure SQL so e usado quando FINOPS_SQL_SERVER esta definido. Sem a variavel,
nada muda: o dash continua em SQLite exatamente como antes.

Variaveis (Azure SQL):
  FINOPS_SQL_SERVER    ex.: sql-dash-recomendacao-rb.database.windows.net
  FINOPS_SQL_DB        ex.: finops
  FINOPS_SQL_USER      ex.: dashadmin
  FINOPS_SQL_PASSWORD  (appsetting; nunca no repositorio)
  FINOPS_SQL_RETRIES   tentativas de conexao (padrao 6; cobre banco serverless pausado)
  FINOPS_SQL_RETRY_S   espera entre tentativas em segundos (padrao 10)
  FINOPS_SQL_TDS       versao do protocolo TDS (padrao 7.4)
"""
import os
import re
import threading
import time

SQL_SERVER = os.getenv("FINOPS_SQL_SERVER", "").strip()
USE_AZURE_SQL = bool(SQL_SERVER)


# --------------------------------------------------------------------------
# Versao da tabela recommendations (so Azure SQL): sobe a cada COMMIT de uma
# conexao que escreveu nela. Serve para invalidar caches em memoria.
# --------------------------------------------------------------------------
_RE_ESCREVE_RECS = re.compile(
    r"^\s*(INSERT|UPDATE|DELETE|MERGE)\b[^;]*?\brecommendations\b", re.I | re.S
)
_RECS_LOCK = threading.Lock()
_RECS_VERSAO = 0


def versao_recomendacoes():
    return _RECS_VERSAO


def _subir_versao_recomendacoes():
    global _RECS_VERSAO
    with _RECS_LOCK:
        _RECS_VERSAO += 1


# --------------------------------------------------------------------------
# Traducao de SQL (dialeto SQLite -> T-SQL), usada so no caminho Azure SQL
# --------------------------------------------------------------------------
_RE_CREATE_IF = re.compile(
    r"^\s*CREATE\s+(UNIQUE\s+)?(TABLE|INDEX)\s+IF\s+NOT\s+EXISTS\b", re.I
)
_RE_BEGIN_IMM = re.compile(r"^\s*BEGIN\s+(IMMEDIATE|EXCLUSIVE|DEFERRED)\b", re.I)
_RE_PRAGMA = re.compile(r"^\s*PRAGMA\b", re.I)
_RE_LENGTH = re.compile(r"\bLENGTH\s*\(", re.I)


def traduzir_sql(sql, com_params):
    """Devolve o SQL em T-SQL, ou None quando o comando deve ser ignorado.

    - ignora BEGIN IMMEDIATE, PRAGMA e CREATE ... IF NOT EXISTS (o esquema vem
      de tools/migrar_sqlite_para_azure_sql.py);
    - ? -> %s (pymssql); % literal -> %% quando ha parametros;
    - "identificador" -> [identificador];
    - LENGTH( -> LEN(.
    """
    if _RE_BEGIN_IMM.match(sql) or _RE_PRAGMA.match(sql) or _RE_CREATE_IF.match(sql):
        return None
    out = []
    in_sq = False
    in_dq = False
    for ch in sql:
        if in_sq:
            if ch == "'":
                in_sq = False
            out.append("%%" if (ch == "%" and com_params) else ch)
        elif in_dq:
            if ch == '"':
                in_dq = False
                out.append("]")
            else:
                out.append(ch)
        elif ch == "'":
            in_sq = True
            out.append(ch)
        elif ch == '"':
            in_dq = True
            out.append("[")
        elif ch == "?":
            out.append("%s")
        elif ch == "%" and com_params:
            out.append("%%")
        else:
            out.append(ch)
    return _RE_LENGTH.sub("LEN(", "".join(out))


# --------------------------------------------------------------------------
# Objetos compativeis com o uso que o dash faz do sqlite3
# --------------------------------------------------------------------------
class AzRow(tuple):
    """Linha acessivel por indice e por nome, como sqlite3.Row."""

    def __new__(cls, values, names):
        obj = super().__new__(cls, values)
        obj._names = list(names)
        obj._idx = {n: i for i, n in enumerate(obj._names)}
        return obj

    def __getitem__(self, key):
        if isinstance(key, str):
            return tuple.__getitem__(self, self._idx[key])
        return tuple.__getitem__(self, key)

    def keys(self):
        return list(self._names)


class AzCursor:
    def __init__(self, cur):
        self._c = cur

    def _names(self):
        d = self._c.description
        return [x[0] for x in d] if d else []

    def fetchone(self):
        r = self._c.fetchone()
        return None if r is None else AzRow(r, self._names())

    def fetchall(self):
        names = self._names()
        return [AzRow(r, names) for r in (self._c.fetchall() or [])]

    def __iter__(self):
        return iter(self.fetchall())

    @property
    def rowcount(self):
        return self._c.rowcount


class AzConnection:
    is_azure = True

    def __init__(self, raw):
        self._raw = raw
        self._escreveu_recs = False

    def _marcar(self, sql):
        if _RE_ESCREVE_RECS.match(sql):
            self._escreveu_recs = True

    def _confirmar_versao(self):
        if self._escreveu_recs:
            self._escreveu_recs = False
            _subir_versao_recomendacoes()

    def execute(self, sql, params=None):
        self._marcar(sql)
        com_params = params is not None and len(params) > 0
        t = traduzir_sql(sql, com_params)
        cur = self._raw.cursor()
        if t is not None:
            cur.execute(t, tuple(params) if com_params else None)
        return AzCursor(cur)

    def executemany(self, sql, seq):
        self._marcar(sql)
        seq = [tuple(p) for p in seq]
        t = traduzir_sql(sql, True)
        cur = self._raw.cursor()
        if t is not None and seq:
            cur.executemany(t, seq)
        return AzCursor(cur)

    def commit(self):
        self._raw.commit()
        self._confirmar_versao()

    def rollback(self):
        self._raw.rollback()
        self._escreveu_recs = False

    def close(self):
        try:
            self._raw.close()
        except Exception:
            pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        try:
            if exc_type is None:
                self._raw.commit()
                self._confirmar_versao()
            else:
                self._raw.rollback()
                self._escreveu_recs = False
        finally:
            self.close()
        return False


def conectar_azure():
    import pymssql  # so e importado quando o Azure SQL esta configurado

    tentativas = max(1, int(os.getenv("FINOPS_SQL_RETRIES", "6")))
    espera = float(os.getenv("FINOPS_SQL_RETRY_S", "10"))
    ultimo = None
    for i in range(tentativas):
        try:
            raw = pymssql.connect(
                server=SQL_SERVER,
                user=os.getenv("FINOPS_SQL_USER", ""),
                password=os.getenv("FINOPS_SQL_PASSWORD", ""),
                database=os.getenv("FINOPS_SQL_DB", ""),
                port=int(os.getenv("FINOPS_SQL_PORT", "1433")),
                login_timeout=30,
                timeout=120,
                charset="UTF-8",
                appname="finops-dash",
                tds_version=os.getenv("FINOPS_SQL_TDS", "7.4"),
                autocommit=False,
            )
            return AzConnection(raw)
        except Exception as exc:  # banco pausado/indisponivel: tenta de novo
            ultimo = exc
            if i < tentativas - 1:
                time.sleep(espera)
    raise ultimo


# --------------------------------------------------------------------------
# Auxiliares que escondem as diferencas de dialeto
# --------------------------------------------------------------------------
def eh_azure(con):
    return bool(getattr(con, "is_azure", False))


def _ident(nome):
    return '"%s"' % str(nome).replace('"', "")


def upsert(con, tabela, chaves, dados, atualizar=None):
    """INSERT ... ON CONFLICT DO UPDATE (SQLite) / MERGE (Azure SQL).

    chaves: colunas que identificam a linha.
    dados: dict coluna -> valor (inclui as chaves).
    atualizar: colunas a atualizar quando a linha existe (padrao: todas menos as chaves).
    """
    cols = list(dados.keys())
    if atualizar is None:
        atualizar = [c for c in cols if c not in chaves]
    valores = [dados[c] for c in cols]

    if not eh_azure(con):
        sql = "INSERT INTO %s (%s) VALUES (%s) ON CONFLICT (%s) " % (
            tabela,
            ", ".join(cols),
            ", ".join("?" for _ in cols),
            ", ".join(chaves),
        )
        if atualizar:
            sql += "DO UPDATE SET " + ", ".join(
                "%s = excluded.%s" % (c, c) for c in atualizar
            )
        else:
            sql += "DO NOTHING"
        con.execute(sql, valores)
        return

    fonte = ", ".join("? AS %s" % _ident(c) for c in cols)
    on = " AND ".join("tgt.%s = src.%s" % (_ident(k), _ident(k)) for k in chaves)
    sql = "MERGE %s WITH (HOLDLOCK) AS tgt USING (SELECT %s) AS src ON (%s) " % (
        tabela,
        fonte,
        on,
    )
    if atualizar:
        sql += "WHEN MATCHED THEN UPDATE SET " + ", ".join(
            "tgt.%s = src.%s" % (_ident(c), _ident(c)) for c in atualizar
        ) + " "
    sql += "WHEN NOT MATCHED THEN INSERT (%s) VALUES (%s);" % (
        ", ".join(_ident(c) for c in cols),
        ", ".join("src.%s" % _ident(c) for c in cols),
    )
    con.execute(sql, valores)


_COLUNAS_AZURE = {}


def colunas_da_tabela(con, tabela):
    """Nomes das colunas da tabela, na ordem."""
    if eh_azure(con):
        # No Azure o esquema so muda por migracao (novo deploy/restart): guarda.
        if tabela in _COLUNAS_AZURE:
            return list(_COLUNAS_AZURE[tabela])
        rows = con.execute(
            "SELECT COLUMN_NAME AS name FROM INFORMATION_SCHEMA.COLUMNS "
            "WHERE TABLE_NAME = ? ORDER BY ORDINAL_POSITION",
            (tabela,),
        ).fetchall()
        nomes = [r["name"] for r in rows]
        if nomes:
            _COLUNAS_AZURE[tabela] = nomes
        return nomes
    else:
        rows = con.execute("PRAGMA table_info(%s)" % tabela).fetchall()
    return [r["name"] for r in rows]
