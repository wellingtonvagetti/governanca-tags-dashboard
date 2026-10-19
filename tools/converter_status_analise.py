# -*- coding: utf-8 -*-
# converter_status_analise.py - converte o status (coluna analise) do SQLite para a lista nova. ASCII-only.
# Uso:
#   python tools\converter_status_analise.py SIMULAR <db>    (so mostra o que mudaria)
#   python tools\converter_status_analise.py APLICAR <db>    (faz backup, converte e confere)
# Regra (api/status.py): vazio->RASCUNHO; EM ANALISE->VALIDACAO TECNICA; ADIAR->ADIADA; REPROVADO->REPROVADA;
# APROVADO: realizado=Sim->CAPTURADO; com chamado (ticket)->EM IMPLEMENTACAO; senao PLANEJADA.
# Nao mexe em nenhuma coluna financeira: antes e depois, um hash dos valores financeiros tem que ser igual.
import sys, os, json, sqlite3, hashlib, datetime, collections
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from api import status as st


def financeiro(con):
    h = hashlib.sha256()
    n = 0
    for r in con.execute(
        "SELECT competencia, opportunity_id, realizado, saving_est, saving, saving_efetivo, rescaldo_previsto, "
        "COALESCE(data_efetivada,''), COALESCE(ticket,'') FROM recommendations ORDER BY competencia, opportunity_id"
    ):
        h.update(("|".join(str(round(x, 2)) if isinstance(x, float) else str(x) for x in r) + "\n").encode("utf-8"))
        n += 1
    return n, h.hexdigest()


def planejar(con):
    mudancas = []
    for comp, oid, analise, realizado, ticket, payload in con.execute(
        "SELECT competencia, opportunity_id, analise, realizado, ticket, payload_json FROM recommendations"
    ):
        novo = st.normalizar(analise, bool(realizado), ticket)
        if novo != (analise or ""):
            mudancas.append((comp, oid, analise or "", novo, payload))
    return mudancas


def resumo(mudancas):
    cont = collections.Counter((c, a or "(vazio)", n) for c, _, a, n, _ in mudancas)
    for (c, a, n), q in sorted(cont.items()):
        print("  %s  %-18s -> %-18s %6d" % (c, a, n.encode("ascii", "replace").decode(), q))
    print("  total a converter: %d" % len(mudancas))


def main():
    modo, db = sys.argv[1].upper(), sys.argv[2]
    if modo not in ("SIMULAR", "APLICAR") or not os.path.exists(db):
        print("uso: converter_status_analise.py SIMULAR|APLICAR <db>"); sys.exit(2)
    con = sqlite3.connect(db)
    n0, h0 = financeiro(con)
    mud = planejar(con)
    print("linhas: %d | hash financeiro antes: %s" % (n0, h0[:16]))
    resumo(mud)
    if modo == "SIMULAR" or not mud:
        print("SIMULAR: nada foi alterado." if modo == "SIMULAR" else "Nada a converter (ja esta na lista nova).")
        return
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    bk = os.path.join(os.path.dirname(os.path.abspath(db)), "finops_dev.before_status_%s.db" % ts)
    b = sqlite3.connect(bk); con.backup(b); b.close()
    print("backup:", bk)
    con.isolation_level = None
    con.execute("BEGIN IMMEDIATE")
    try:
        for comp, oid, _, novo, payload in mud:
            try:
                p = json.loads(payload) if payload else {}
                if isinstance(p, dict):
                    p["analise"] = novo
                    payload = json.dumps(p, ensure_ascii=False)
            except ValueError:
                pass
            con.execute(
                "UPDATE recommendations SET analise = ?, payload_json = ? WHERE competencia = ? AND opportunity_id = ?",
                (novo, payload, comp, oid),
            )
        n1, h1 = financeiro(con)
        if (n1, h1) != (n0, h0):
            raise RuntimeError("valores financeiros mudaram; desfeito")
        restantes = [a for (a,) in con.execute("SELECT DISTINCT COALESCE(analise,'') FROM recommendations") if a not in st.STATUS]
        if restantes:
            raise RuntimeError("sobraram status fora da lista: %r; desfeito" % restantes)
        con.execute("COMMIT")
    except Exception as e:
        con.execute("ROLLBACK")
        print("ERRO:", e, "- nada foi gravado."); sys.exit(1)
    print("OK: %d linhas convertidas; hash financeiro igual (%s)." % (len(mud), h1[:16]))
    print("Confira: python tools\\verifica_numeros.py VERIFICAR %s 2026-09" % db)


main()
