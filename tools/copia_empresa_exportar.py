# -*- coding: utf-8 -*-
"""Exporta o banco da EMPRESA (Azure SQL) para um .json.gz e envia para um link SAS (so escrita).

Roda no Cloud Shell da empresa (conta -p), que e o unico lugar que alcanca o banco. So LE o banco.
O arquivo vai para o storage pessoal e e carregado no local/POC por tools/copia_empresa_carregar.py.

Uso no Cloud Shell (o script e colado; nao ha upload de arquivo no BeyondTrust):
    $env:SQLPW   = <senha do FINOPS_SQL_PASSWORD do app da empresa>
    $env:COPIA_SAS = <URL SAS de escrita do blob, gerada no lado pessoal>
    python3 copia_empresa_exportar.py
"""
import datetime
import decimal
import gzip
import json
import os
import urllib.request

import pymssql

TABELAS = ("recommendations", "recommendation_audit", "app_state", "cost_records",
           "competencias_fechadas", "database_metadata")


def valor(v):
    if isinstance(v, decimal.Decimal):
        return float(v)
    if isinstance(v, (datetime.datetime, datetime.date)):
        return v.isoformat(sep=" ") if isinstance(v, datetime.datetime) else v.isoformat()
    if isinstance(v, (bytes, bytearray)):
        return v.decode("utf-8", "replace")
    return v


def main():
    con = pymssql.connect(server="sql-dash-rec-finops.database.windows.net", user="dashadmin",
                          password=os.environ["SQLPW"], database="sqldb-dash-rec-finops")
    cur = con.cursor()
    saida = {"origem": "sqldb-dash-rec-finops", "exportado_em": datetime.datetime.utcnow().isoformat() + "Z",
             "tabelas": {}}
    for t in TABELAS:
        cur.execute("SELECT * FROM %s" % t)
        cols = [d[0] for d in cur.description]
        linhas = [[valor(v) for v in r] for r in cur.fetchall()]
        saida["tabelas"][t] = {"colunas": cols, "linhas": linhas}
        print("%-22s %7d linhas" % (t, len(linhas)))
    con.close()
    corpo = gzip.compress(json.dumps(saida, ensure_ascii=False).encode("utf-8"), 6)
    req = urllib.request.Request(os.environ["COPIA_SAS"], data=corpo, method="PUT",
                                 headers={"x-ms-blob-type": "BlockBlob", "Content-Type": "application/gzip"})
    with urllib.request.urlopen(req, timeout=300) as r:
        print("enviado: %.1f MB (HTTP %s)" % (len(corpo) / 1e6, r.status))


if __name__ == "__main__":
    main()
