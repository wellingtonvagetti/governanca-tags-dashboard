# -*- coding: utf-8 -*-
# fechar_competencia.py - fecha (congela) uma competencia no SQLite local ou no Azure SQL. ASCII-only.
# Fechar = linha em competencias_fechadas; a API e os triggers passam a bloquear
# alteracao dos valores financeiros (saving_est, realizado, saving, saving_efetivo, rescaldo_previsto).
# Rodar so depois de importar os custos do mes inteiro (dia 1 ao ultimo dia) e conferir o dash.
# Uso:
#   python tools/fechar_competencia.py SIMULAR 2026-10    (mostra numeros, custos importados e o que falta)
#   python tools/fechar_competencia.py APLICAR 2026-10    (fecha e confere que os numeros nao mudaram)
# No Azure (FINOPS_SQL_* no ambiente) os triggers ja existem (migrador --triggers).
# No SQLite local os triggers sao criados por tools/freeze_competencia.py.
import sys, os, decimal
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from api.db import conectar
from api.sqldb import eh_azure


def num(x):
    if isinstance(x, bool):
        return int(x)
    if isinstance(x, decimal.Decimal):
        return float(x)
    return x


def numeros(con, comp):
    r = con.execute(
        "SELECT COUNT(*), SUM(CASE WHEN realizado = 1 THEN 1 ELSE 0 END), COALESCE(SUM(saving_est),0), "
        "COALESCE(SUM(saving_efetivo),0), COALESCE(SUM(rescaldo_previsto),0) "
        "FROM recommendations WHERE competencia = ?", (comp,)).fetchone()
    return (int(num(r[0]) or 0), int(num(r[1]) or 0), round(num(r[2]), 2), round(num(r[3]), 2), round(num(r[4]), 2))


def main():
    modo, comp = sys.argv[1].upper(), sys.argv[2]
    ano, mes = int(comp[:4]), int(comp[5:7])
    con = conectar()
    try:
        azure = eh_azure(con)
        print("banco: %s" % ("Azure SQL" if azure else "SQLite local"))
        n = numeros(con, comp)
        print("competencia %s: linhas=%d realizadas=%d est=%.2f efetivo=%.2f rescaldo=%.2f" % ((comp,) + n))
        if not n[0]:
            print("ERRO: competencia sem recomendacoes."); sys.exit(2)
        custos = con.execute("SELECT provider, source_type, file_name, saved_at FROM cost_records "
                             "WHERE year = ? AND month = ? ORDER BY provider", (ano, mes)).fetchall()
        print("custos importados do mes: %d" % len(custos))
        for c in custos:
            print("  %-6s %-12s %s  (salvo em %s)" % (c[0], c[1], c[2], c[3]))
        if azure:
            trg = num(con.execute("SELECT COUNT(*) FROM sys.triggers WHERE name LIKE 'trg_fechamento%'").fetchone()[0])
        else:
            trg = num(con.execute("SELECT COUNT(*) FROM sqlite_master WHERE type = 'trigger' "
                                  "AND name LIKE 'trg_fechamento%'").fetchone()[0])
        print("triggers de fechamento no banco: %d" % trg)
        ja = con.execute("SELECT fechada, fechada_em FROM competencias_fechadas WHERE competencia = ?", (comp,)).fetchone()
        if ja and num(ja[0]) == 1:
            print("Ja estava fechada em %s. Nada a fazer." % ja[1]); return
        if not trg:
            print("ATENCAO: sem triggers; rode o migrador --triggers (Azure) ou tools/freeze_competencia.py (local).")
        if modo != "APLICAR":
            print("SIMULAR: nada gravado. Confira os custos (dia 1 ao ultimo dia) e os numeros no dash antes de APLICAR.")
            return
        if ja:
            con.execute("UPDATE competencias_fechadas SET fechada = 1 WHERE competencia = ?", (comp,))
        else:
            con.execute("INSERT INTO competencias_fechadas (competencia, fechada) VALUES (?, 1)", (comp,))
        con.commit()
        depois = numeros(con, comp)
        if depois != n:
            print("ERRO: numeros mudaram ao fechar: %s" % (depois,)); sys.exit(1)
        print("FECHADA: %s. Numeros identicos. Gere o golden: verifica_numeros.py GERAR <db|AZURE> %s" % (comp, comp))
    finally:
        con.close()


main()
