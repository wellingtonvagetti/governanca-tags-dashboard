# -*- coding: utf-8 -*-
"""Monta um SQLite a partir da exportacao da empresa (tools/copia_empresa_exportar.py).

Uso:
    python tools/copia_empresa_carregar.py <empresa.json.gz> <destino.db>

Cria o banco do zero com database/schema.sql, copia as tabelas (so as colunas que existem dos dois lados),
recria as travas das competencias fechadas (tools/freeze_competencia.py) e mostra contagens e somas por
competencia para conferir com o dash da empresa. O destino nao pode existir (troque o arquivo depois).
Depois, para a POC ficar igual: infra/atualizar_poc_dados.ps1 (copia o banco local para o Azure SQL da POC).
"""
import gzip
import json
import os
import sqlite3
import subprocess
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main(origem, destino):
    if os.path.exists(destino):
        raise SystemExit("destino ja existe: %s" % destino)
    dados = json.loads(gzip.decompress(open(origem, "rb").read()).decode("utf-8"))
    print("exportado em", dados.get("exportado_em"), "de", dados.get("origem"))
    con = sqlite3.connect(destino)
    con.executescript(open(os.path.join(RAIZ, "database", "schema.sql"), encoding="utf-8-sig").read())
    for tabela, t in dados["tabelas"].items():
        cols_banco = [r[1] for r in con.execute("PRAGMA table_info(%s)" % tabela)]
        if not cols_banco:
            print("  (tabela %s nao existe no schema local; ignorada)" % tabela)
            continue
        idx = [(i, c) for i, c in enumerate(t["colunas"]) if c in cols_banco]
        sql = "INSERT INTO %s (%s) VALUES (%s)" % (tabela, ", ".join('"%s"' % c for _, c in idx),
                                                   ", ".join("?" for _ in idx))
        con.executemany(sql, ([linha[i] for i, _ in idx] for linha in t["linhas"]))
        fora = [c for c in t["colunas"] if c not in cols_banco]
        print("  %-22s %7d linhas%s" % (tabela, len(t["linhas"]), (" | colunas so na empresa: %s" % fora) if fora else ""))
    con.commit()
    fechadas = [r[0] for r in con.execute("SELECT competencia FROM competencias_fechadas WHERE fechada = 1")]
    con.close()
    pasta = os.path.dirname(os.path.abspath(destino))
    antes = set(os.listdir(pasta))
    for comp in fechadas:
        subprocess.run([sys.executable, os.path.join(RAIZ, "tools", "freeze_competencia.py"), "APLICAR", destino, comp],
                       check=True, capture_output=True)
        print("  trava recriada:", comp)
    # o freeze_competencia guarda um backup do banco antes de criar as travas; aqui o banco acabou de nascer
    for nome in set(os.listdir(pasta)) - antes:
        if ".before_freeze_" in nome:
            os.remove(os.path.join(pasta, nome))
    con = sqlite3.connect(destino)
    print("\ncompetencia | recomendacoes | saving est. | saving | saving efetivo")
    for r in con.execute("SELECT competencia, COUNT(*), ROUND(SUM(saving_est),2), ROUND(SUM(saving),2), "
                         "ROUND(SUM(saving_efetivo),2) FROM recommendations GROUP BY competencia ORDER BY 1"):
        print("  %s | %d | %s | %s | %s" % r)
    con.close()


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
