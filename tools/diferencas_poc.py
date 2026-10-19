# -*- coding: utf-8 -*-
"""Lista as alteracoes que existem SO no Azure SQL (POC) e nao no SQLite local. Somente leitura nos dois lados.

Uso (com FINOPS_SQL_SERVER, FINOPS_SQL_DB, FINOPS_SQL_USER e FINOPS_SQL_PASSWORD definidos):
    python tools\\diferencas_poc.py <banco_local.db>

Compara o historico de auditoria (recommendation_audit) pelo conteudo: competencia, ID, campo, valor novo e
horario. Codigo de saida: 0 = a POC nao tem nada que o local nao tenha; 3 = ha alteracoes so na POC.
"""
import os
import sqlite3
import sys

CAMPOS = "competencia, opportunity_id, campo, valor_novo, usuario, alterado_em"


def chave(linha):
    return tuple("" if v is None else str(v).strip() for v in linha)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    local = sqlite3.connect("file:%s?mode=ro" % sys.argv[1].replace("\\", "/"), uri=True)
    no_local = {chave(r) for r in local.execute("SELECT %s FROM recommendation_audit" % CAMPOS)}

    import pymssql
    poc = pymssql.connect(
        server=os.environ["FINOPS_SQL_SERVER"], user=os.environ["FINOPS_SQL_USER"],
        password=os.environ["FINOPS_SQL_PASSWORD"], database=os.environ["FINOPS_SQL_DB"],
        login_timeout=60, timeout=600, charset="UTF-8", tds_version=os.getenv("FINOPS_SQL_TDS", "7.4"),
    )
    cur = poc.cursor()
    cur.execute("SELECT %s FROM recommendation_audit" % CAMPOS)
    so_poc = [r for r in cur.fetchall() if chave(r) not in no_local]
    poc.close()

    if not so_poc:
        print("OK: a POC nao tem alteracoes que o local nao tenha.")
        return 0
    ids = sorted({(r[0], r[1]) for r in so_poc})
    print("ATENCAO: %d alteracao(oes) existem SO na POC, em %d recomendacao(oes):" % (len(so_poc), len(ids)))
    for r in sorted(so_poc, key=lambda x: str(x[5]))[-40:]:
        print("  %s  %s  %s  %s -> %s  (%s)" % (str(r[5])[:16], r[0], r[1], r[2], str(r[3])[:40], r[4]))
    if len(so_poc) > 40:
        print("  ... (mostrando as 40 mais recentes)")
    return 3


if __name__ == "__main__":
    sys.exit(main())
