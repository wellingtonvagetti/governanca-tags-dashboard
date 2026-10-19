# -*- coding: utf-8 -*-
"""Copia o banco SQLite do dash para o Azure SQL, cria o esquema e confere o resultado.

Uso (PowerShell, na raiz do repo, com o .venv ativo):
    pip install pymssql
    $env:FINOPS_SQL_SERVER   = "sql-dash-recomendacao-rb.database.windows.net"
    $env:FINOPS_SQL_DB       = "finops"
    $env:FINOPS_SQL_USER     = "dashadmin"
    $env:FINOPS_SQL_PASSWORD = "<senha>"     # nao imprimir nem commitar
    python tools\\migrar_sqlite_para_azure_sql.py <origem.db> SIMULAR
    python tools\\migrar_sqlite_para_azure_sql.py <origem.db> APLICAR [--recriar] [--triggers]

SIMULAR: so le o SQLite e mostra o esquema T-SQL que seria criado (nao conecta).
APLICAR: cria as tabelas, copia os dados e confere contagens e somas.
  --recriar   apaga e recria as tabelas que ja existirem no Azure SQL
  --triggers  recria no Azure SQL os triggers que congelam competencia fechada
              (so depois de conferir a carga; teste primeiro sem)
O SQLite de origem e aberto somente para leitura.
"""
import hashlib
import json
import os
import sqlite3
import sys

MAX_LINHAS_LOTE = 200
MAX_BYTES_LOTE = 4 * 1024 * 1024


def q(nome):
    return "[%s]" % str(nome).replace("]", "")


def tipo_tsql(decl, tam_texto):
    d = (decl or "").upper()
    if "INT" in d:
        return "BIGINT"
    if any(x in d for x in ("REAL", "FLOA", "DOUB", "NUM", "DEC")):
        return "FLOAT"
    if "BLOB" in d:
        return "VARBINARY(MAX)"
    return "NVARCHAR(%s)" % tam_texto


def default_tsql(dflt):
    if dflt is None:
        return None
    t = str(dflt).strip()
    low = t.lower().replace(" ", "")
    if low in ("current_timestamp", "datetime('now')", "datetime('now','localtime')"):
        return "(CONVERT(NVARCHAR(19), SYSUTCDATETIME(), 120))"
    try:
        float(t)
        return "(%s)" % t
    except ValueError:
        pass
    if t.startswith("'") and t.endswith("'"):
        return "(N%s)" % t
    raise ValueError("DEFAULT nao suportado: %r" % dflt)


def ler_esquema(src):
    tabelas = {}
    for nome, sql in src.execute(
        "SELECT name, sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    ).fetchall():
        cols = src.execute("PRAGMA table_info(%s)" % nome).fetchall()
        # (cid, name, type, notnull, dflt_value, pk)
        pk = [c[1] for c in sorted((c for c in cols if c[5]), key=lambda c: c[5])]
        indices = []  # (nome, unico, [colunas])
        for _, iname, unico, origem, _p in src.execute("PRAGMA index_list(%s)" % nome).fetchall():
            if origem == "pk":
                continue
            icols = [r[2] for r in src.execute("PRAGMA index_info(%s)" % iname).fetchall()]
            indices.append((iname, bool(unico), icols))
        tabelas[nome] = {
            "sql": sql or "",
            "cols": cols,
            "pk": pk,
            "indices": indices,
        }
    return tabelas


def montar_ddl(nome, t):
    # colunas em PK/indice precisam de tamanho limitado (limite de 900 bytes da chave)
    indexadas = {}
    grupos = [t["pk"]] + [i[2] for i in t["indices"]]
    for g in grupos:
        for c in g:
            indexadas[c] = min(indexadas.get(c, 450), 450 if len(g) == 1 else 200)
    ident = (
        len(t["pk"]) == 1
        and "AUTOINCREMENT" in t["sql"].upper()
        and any(c[1] == t["pk"][0] and "INT" in (c[2] or "").upper() for c in t["cols"])
    )
    linhas = []
    for _cid, cn, decl, notnull, dflt, pk in t["cols"]:
        tam = indexadas.get(cn, "MAX")
        partes = [q(cn), tipo_tsql(decl, tam)]
        if ident and cn == t["pk"][0]:
            partes.append("IDENTITY(1,1)")
        if notnull or cn in t["pk"]:
            partes.append("NOT NULL")
        d = default_tsql(dflt)
        if d is not None:
            partes.append("DEFAULT " + d)
        linhas.append(" ".join(partes))
    if t["pk"]:
        linhas.append("CONSTRAINT %s PRIMARY KEY (%s)" % (q("pk_" + nome), ", ".join(q(c) for c in t["pk"])))
    ddl = ["CREATE TABLE %s (\n  %s\n)" % (q(nome), ",\n  ".join(linhas))]
    for iname, unico, icols in t["indices"]:
        ddl.append(
            "CREATE %sINDEX %s ON %s (%s)"
            % ("UNIQUE " if unico else "", q("ix_%s_%s" % (nome, "_".join(icols))), q(nome), ", ".join(q(c) for c in icols))
        )
    return ddl, ident


def sql_triggers():
    cols = [("saving_est", "FLOAT"), ("realizado", "BIGINT"), ("saving", "FLOAT"),
            ("saving_efetivo", "FLOAT"), ("rescaldo_previsto", "FLOAT")]
    fech_i = ("EXISTS (SELECT 1 FROM competencias_fechadas f "
              "WHERE f.competencia = {a}.competencia AND f.fechada = 1)")

    def conv(c, tipo, pref):
        v = "%s_%s" % (pref, c)
        return "CONVERT(NVARCHAR(50), %s%s)" % (v, ", 3" if tipo == "FLOAT" else "")

    decl = ", ".join("o_%s %s, n_%s %s" % (c, t, c, t) for c, t in cols)
    sel = ", ".join("d.%s, i.%s" % (c, c) for c, _ in cols)
    difs = " OR ".join("d.%s <> i.%s" % (c, c) for c, _ in cols)
    upd_any = " OR ".join("UPDATE(%s)" % c for c, _ in cols)
    audit = "\n".join(
        "  INSERT INTO recommendation_audit (competencia, opportunity_id, campo, valor_anterior, valor_novo, usuario)\n"
        "  SELECT competencia, opportunity_id, '%s', %s, %s, 'BLOQUEADO_FECHAMENTO' FROM @ch WHERE o_%s <> n_%s;"
        % (c, conv(c, t, "o"), conv(c, t, "n"), c, c) for c, t in cols
    )
    restore = "  UPDATE r SET %s\n  FROM recommendations r JOIN @ch c ON r.competencia = c.competencia AND r.opportunity_id = c.opportunity_id;" % (
        ", ".join("r.%s = c.o_%s" % (c, c) for c, _ in cols))
    t1 = """CREATE OR ALTER TRIGGER trg_fechamento_bloqueia_update ON recommendations AFTER UPDATE AS
BEGIN
  SET NOCOUNT ON;
  IF NOT (%s) RETURN;
  DECLARE @ch TABLE (competencia NVARCHAR(200), opportunity_id NVARCHAR(200), %s);
  INSERT INTO @ch
  SELECT i.competencia, i.opportunity_id, %s
  FROM inserted i JOIN deleted d ON d.competencia = i.competencia AND d.opportunity_id = i.opportunity_id
  WHERE %s AND (%s);
  IF NOT EXISTS (SELECT 1 FROM @ch) RETURN;
%s
%s
END""" % (upd_any, decl, sel, fech_i.format(a="i"), difs, audit, restore)

    t2 = """CREATE OR ALTER TRIGGER trg_fechamento_bloqueia_delete ON recommendations AFTER DELETE AS
BEGIN
  SET NOCOUNT ON;
  IF EXISTS (SELECT 1 FROM deleted d WHERE %s)
  BEGIN
    IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
    THROW 50001, 'COMPETENCIA FECHADA: exclusao bloqueada', 1;
  END
END""" % fech_i.format(a="d")

    t3 = """CREATE OR ALTER TRIGGER trg_fechamento_bloqueia_insert ON recommendations AFTER INSERT AS
BEGIN
  SET NOCOUNT ON;
  IF EXISTS (SELECT 1 FROM inserted i WHERE %s)
  BEGIN
    IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
    THROW 50002, 'COMPETENCIA FECHADA: insercao bloqueada', 1;
  END
END""" % fech_i.format(a="i")

    abertas = [("realizado", "BIGINT"), ("saving_efetivo", "FLOAT"), ("rescaldo_previsto", "FLOAT")]
    decl2 = ", ".join("o_%s %s, n_%s %s" % (c, t, c, t) for c, t in abertas)
    sel2 = ", ".join("d.%s, i.%s" % (c, c) for c, _ in abertas)
    difs2 = " OR ".join("d.%s <> i.%s" % (c, c) for c, _ in abertas)
    upd2 = " OR ".join("UPDATE(%s)" % c for c, _ in abertas)
    audit2 = "\n".join(
        "  INSERT INTO recommendation_audit (competencia, opportunity_id, campo, valor_anterior, valor_novo, usuario)\n"
        "  SELECT competencia, opportunity_id, 'db:%s', %s, %s, 'db-trigger' FROM @ch WHERE o_%s <> n_%s;"
        % (c, conv(c, t, "o"), conv(c, t, "n"), c, c) for c, t in abertas
    )
    t4 = """CREATE OR ALTER TRIGGER trg_audit_financeiro_aberta ON recommendations AFTER UPDATE AS
BEGIN
  SET NOCOUNT ON;
  IF NOT (%s) RETURN;
  DECLARE @ch TABLE (competencia NVARCHAR(200), opportunity_id NVARCHAR(200), %s);
  INSERT INTO @ch
  SELECT i.competencia, i.opportunity_id, %s
  FROM inserted i JOIN deleted d ON d.competencia = i.competencia AND d.opportunity_id = i.opportunity_id
  WHERE NOT %s AND (%s);
%s
END""" % (upd2, decl2, sel2, fech_i.format(a="i"), difs2, audit2)
    return [t1, t2, t3, t4]


# ---------------------------------------------------------------------------
def norm(v):
    if isinstance(v, float):
        return round(v, 6)
    if isinstance(v, bool):
        return int(v)
    return v


def assinatura(linhas):
    """Soma de hashes por linha (independe da ordem das linhas)."""
    total = 0
    n = 0
    for r in linhas:
        h = hashlib.sha1(json.dumps([norm(x) for x in r], ensure_ascii=False, default=str).encode("utf-8")).hexdigest()
        total = (total + int(h[:15], 16)) % (1 << 60)
        n += 1
    return n, total


def converter(valor, tipo_destino):
    if valor is None:
        return None
    if tipo_destino == "BIGINT":
        return int(valor)
    if tipo_destino == "FLOAT":
        return float(valor)
    if tipo_destino.startswith("NVARCHAR"):
        return valor if isinstance(valor, str) else str(valor)
    return valor


def main():
    if len(sys.argv) < 3 or sys.argv[2].upper() not in ("SIMULAR", "APLICAR"):
        print(__doc__)
        sys.exit(1)
    origem, modo = sys.argv[1], sys.argv[2].upper()
    recriar = "--recriar" in sys.argv
    triggers = "--triggers" in sys.argv

    src = sqlite3.connect("file:%s?mode=ro" % origem.replace("\\", "/"), uri=True)
    tabelas = ler_esquema(src)
    print("tabelas no SQLite: " + ", ".join("%s(%d)" % (n, src.execute("SELECT COUNT(*) FROM %s" % n).fetchone()[0]) for n in tabelas))

    ddls = {}
    for nome, t in tabelas.items():
        ddls[nome] = montar_ddl(nome, t)
    if modo == "SIMULAR":
        for nome, (ddl, ident) in ddls.items():
            print("\n-- %s%s" % (nome, " (IDENTITY)" if ident else ""))
            for d in ddl:
                print(d + ";")
        if "competencias_fechadas" in tabelas:
            print("\n-- triggers (com --triggers):")
            for tr in sql_triggers():
                print(tr + "\nGO")
        print("\nSIMULAR: nada foi criado nem copiado.")
        return

    import pymssql

    for v in ("FINOPS_SQL_SERVER", "FINOPS_SQL_DB", "FINOPS_SQL_USER", "FINOPS_SQL_PASSWORD"):
        if not os.getenv(v):
            print("ABORTADO: variavel %s nao definida" % v)
            sys.exit(1)
    dst = pymssql.connect(
        server=os.environ["FINOPS_SQL_SERVER"], user=os.environ["FINOPS_SQL_USER"],
        password=os.environ["FINOPS_SQL_PASSWORD"], database=os.environ["FINOPS_SQL_DB"],
        login_timeout=60, timeout=1800, charset="UTF-8", tds_version=os.getenv("FINOPS_SQL_TDS", "7.4"),
        autocommit=False,
    )
    cur = dst.cursor()

    cur.execute("SELECT name FROM sys.tables")
    existentes = {r[0] for r in cur.fetchall()}
    conflito = [n for n in tabelas if n in existentes]
    if conflito and not recriar:
        print("ABORTADO: tabelas ja existem no Azure SQL: %s. Use --recriar para apagar e recriar." % ", ".join(conflito))
        sys.exit(1)
    for n in conflito:
        cur.execute("DROP TABLE %s" % q(n))
    dst.commit()

    for nome, (ddl, _ident) in ddls.items():
        for d in ddl:
            cur.execute(d)
    dst.commit()
    print("esquema criado")

    for nome, t in tabelas.items():
        ident = ddls[nome][1]
        cols = [c[1] for c in t["cols"]]
        dest_tipos = [tipo_tsql(c[2], "X") for c in t["cols"]]
        dest_tipos = ["NVARCHAR" if x == "NVARCHAR(X)" else x for x in dest_tipos]
        if ident:
            cur.execute("SET IDENTITY_INSERT %s ON" % q(nome))
        total = 0
        lote, bytes_lote = [], 0

        def flush():
            nonlocal lote, bytes_lote, total
            if not lote:
                return
            placeholders = "(" + ",".join(["%s"] * len(cols)) + ")"
            sql = "INSERT INTO %s (%s) VALUES %s" % (q(nome), ", ".join(q(c) for c in cols), ",".join([placeholders] * len(lote)))
            params = tuple(v for linha in lote for v in linha)
            cur.execute(sql, params)
            total += len(lote)
            lote, bytes_lote = [], 0

        for linha in src.execute("SELECT %s FROM %s" % (", ".join('"%s"' % c for c in cols), nome)):
            try:
                conv = [converter(v, dest_tipos[i]) for i, v in enumerate(linha)]
            except (TypeError, ValueError) as exc:
                print("ABORTADO: valor invalido em %s: %s" % (nome, exc))
                dst.rollback()
                sys.exit(1)
            tam = sum(len(x) for x in conv if isinstance(x, str))
            if lote and (len(lote) >= MAX_LINHAS_LOTE or bytes_lote + tam > MAX_BYTES_LOTE):
                flush()
            lote.append(conv)
            bytes_lote += tam
        flush()
        if ident:
            cur.execute("SET IDENTITY_INSERT %s OFF" % q(nome))
        dst.commit()
        print("copiado %s: %d linhas" % (nome, total))

    # --- conferencia ---------------------------------------------------
    print("\nconferindo (contagem + assinatura do conteudo de cada tabela)...")
    ok = True
    for nome, t in tabelas.items():
        cols = [c[1] for c in t["cols"]]
        sel_src = "SELECT %s FROM %s" % (", ".join('"%s"' % c for c in cols), nome)
        n1, h1 = assinatura(src.execute(sel_src))
        cur.execute("SELECT %s FROM %s" % (", ".join(q(c) for c in cols), q(nome)))
        n2, h2 = assinatura(cur.fetchall())
        igual = (n1 == n2 and h1 == h2)
        ok = ok and igual
        print("  %-24s origem=%d destino=%d  %s" % (nome, n1, n2, "OK" if igual else "DIFERENTE"))
    if "recommendations" in tabelas:
        print("\nsomas por competencia (origem x destino):")
        agg = ("competencia, COUNT(*), ROUND(SUM(saving_est),2), SUM(realizado), ROUND(SUM(saving),2), "
               "ROUND(SUM(saving_efetivo),2), ROUND(SUM(rescaldo_previsto),2)")
        a = src.execute("SELECT %s FROM recommendations GROUP BY competencia ORDER BY competencia" % agg).fetchall()
        cur.execute("SELECT %s FROM recommendations GROUP BY competencia ORDER BY competencia" % agg)
        b = cur.fetchall()
        for ra, rb in zip(a, b):
            igual = ra[0] == rb[0] and all(abs(float(x) - float(y)) < 0.01 for x, y in zip(ra[1:], rb[1:]))
            ok = ok and igual
            print("  %s  n=%s  saving_efetivo=%s  rescaldo=%s  %s" % (ra[0], ra[1], ra[5], ra[6], "OK" if igual else "DIFERENTE %s" % (rb,)))
        ok = ok and len(a) == len(b)

    if not ok:
        print("\nATENCAO: a conferencia encontrou diferencas. Triggers NAO foram criados.")
        sys.exit(2)

    if triggers and "competencias_fechadas" in tabelas:
        for tr in sql_triggers():
            cur.execute(tr)
        dst.commit()
        print("\ntriggers de competencia fechada criados")
    print("\nOK: migracao concluida e conferida")
    dst.close()


if __name__ == "__main__":
    main()
