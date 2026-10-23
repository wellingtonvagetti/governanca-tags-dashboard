# -*- coding: utf-8 -*-
# restaurar_data_recomendada.py - devolve a data original as recomendacoes herdadas. ASCII-only.
# Regra do processo: a data recomendada e a da primeira vez que a recomendacao apareceu e
# nunca muda na heranca entre competencias. Ate a v5 a heranca gravava "<competencia>-01".
# Para cada linha da competencia cujo ID ja existia antes, grava a MENOR data das
# competencias anteriores (coluna e payload_json) e registra na auditoria.
# Funciona no SQLite local e no Azure SQL (FINOPS_SQL_* no ambiente), via api.db.conectar().
# Uso:
#   python tools/restaurar_data_recomendada.py SIMULAR 2026-10
#   python tools/restaurar_data_recomendada.py APLICAR 2026-10
# Nao mexe em nenhuma coluna financeira (confere antes e depois).
import sys, os, json, hashlib, collections
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from api.db import conectar

FIN = ("SELECT opportunity_id, realizado, saving_est, saving, saving_efetivo, rescaldo_previsto "
       "FROM recommendations WHERE competencia = ? ORDER BY opportunity_id")


def financeiro(con, comp):
    h = hashlib.sha256()
    for r in con.execute(FIN, (comp,)).fetchall():
        h.update(("|".join("%.2f" % float(x) if isinstance(x, float) else str(x) for x in r) + "\n").encode("utf-8"))
    return h.hexdigest()


def planejar(con, comp):
    original = {}
    for oid, data in con.execute(
        "SELECT opportunity_id, MIN(data_recomendada) FROM recommendations "
        "WHERE competencia < ? AND data_recomendada IS NOT NULL AND data_recomendada <> '' "
        "GROUP BY opportunity_id", (comp,)
    ).fetchall():
        original[str(oid)] = str(data)[:10]
    mudancas = []
    for oid, data, payload in con.execute(
        "SELECT opportunity_id, data_recomendada, payload_json FROM recommendations WHERE competencia = ?", (comp,)
    ).fetchall():
        alvo = original.get(str(oid))
        atual = str(data or "")[:10]
        if alvo and alvo != atual:
            mudancas.append((str(oid), atual, alvo, payload))
    return mudancas


def main():
    modo, comp = sys.argv[1].upper(), sys.argv[2]
    con = conectar()
    try:
        fech = con.execute("SELECT COUNT(*) FROM competencias_fechadas WHERE competencia = ? AND fechada = 1",
                           (comp,)).fetchone()[0]
        if fech:
            print("ERRO: %s esta fechada; nao altero competencia fechada." % comp); sys.exit(2)
        mudancas = planejar(con, comp)
        total = con.execute("SELECT COUNT(*) FROM recommendations WHERE competencia = ?", (comp,)).fetchone()[0]
        print("competencia %s: %d linhas, %d com data a restaurar" % (comp, total, len(mudancas)))
        por_par = collections.Counter((a, b) for _, a, b, _ in mudancas)
        for (a, b), n in por_par.most_common(12):
            print("  %-10s -> %-10s  %d" % (a or "(vazio)", b, n))
        for oid, a, b, _ in mudancas[:5]:
            print("  ex.: %s  %s -> %s" % (oid, a or "(vazio)", b))
        if modo != "APLICAR" or not mudancas:
            print("SIMULAR: nada gravado." if modo != "APLICAR" else "Nada a fazer.")
            return
        antes = financeiro(con, comp)
        for oid, a, b, payload in mudancas:
            try:
                p = json.loads(payload) if payload else {}
            except ValueError:
                p = {}
            p["dataRecomendada"] = b
            con.execute("UPDATE recommendations SET data_recomendada = ?, payload_json = ? "
                        "WHERE competencia = ? AND opportunity_id = ?",
                        (b, json.dumps(p, ensure_ascii=False), comp, oid))
            con.execute("INSERT INTO recommendation_audit (competencia, opportunity_id, campo, valor_anterior, "
                        "valor_novo, usuario) VALUES (?, ?, 'dataRecomendada', ?, ?, 'restaurar-data')",
                        (comp, oid, a, b))
        if financeiro(con, comp) != antes:
            con.rollback()
            print("ERRO: valores financeiros mudaram; nada gravado."); sys.exit(1)
        con.commit()
        resto = planejar(con, comp)
        print("APLICADO: %d datas restauradas; pendentes depois: %d; financeiro identico." % (len(mudancas), len(resto)))
        if resto:
            sys.exit(1)
    finally:
        con.close()


main()
