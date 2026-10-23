# -*- coding: utf-8 -*-
# verifica_numeros.py - confere os numeros de referencia das competencias FECHADAS (somente leitura). ASCII-only.
# Uso:
#   python tools\verifica_numeros.py GERAR     database\finops_dev.db 2026-09   (grava docs\golden_numeros.json)
#   python tools\verifica_numeros.py VERIFICAR database\finops_dev.db 2026-09   (compara com o golden; codigo de saida 1 se divergir)
import sys, os, json, sqlite3, hashlib, decimal
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from api.status import legado  # status novos e antigos contam como a mesma classe (so o nome mudou)

REF = {"2026-09": {"saving_efetivo": 143944.70, "rescaldo_previsto": 44842.05}}  # numeros fechados informados
GOLDEN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "docs", "golden_numeros.json")

def num(x):
    # Azure SQL devolve Decimal e bit (bool); normaliza para o mesmo formato do SQLite
    if isinstance(x, bool):
        return int(x)
    if isinstance(x, decimal.Decimal):
        return float(x)
    return x

def medir(db, comp):
    azure = db.upper() == "AZURE"
    if azure:
        from api.db import conectar
        c = conectar()
    else:
        c = sqlite3.connect("file:%s?mode=ro" % db.replace("\\", "/"), uri=True)
    q = lambda sql, *a: num(c.execute(sql, a).fetchone()[0])
    m = {
        "competencia": comp,
        "linhas": q("SELECT COUNT(*) FROM recommendations WHERE competencia=?", comp),
        "linhas_nao_reprovadas": sum(1 for (a,) in c.execute("SELECT COALESCE(analise,'') FROM recommendations WHERE competencia=?", (comp,)) if legado(a) != "REPROVADO"),
        "realizadas": q("SELECT COUNT(*) FROM recommendations WHERE competencia=? AND realizado=1", comp),
        "saving_est": round(q("SELECT COALESCE(SUM(saving_est),0) FROM recommendations WHERE competencia=?", comp), 2),
        "saving": round(q("SELECT COALESCE(SUM(saving),0) FROM recommendations WHERE competencia=?", comp), 2),
        "saving_efetivo": round(q("SELECT COALESCE(SUM(saving_efetivo),0) FROM recommendations WHERE competencia=?", comp), 2),
        "rescaldo_previsto": round(q("SELECT COALESCE(SUM(rescaldo_previsto),0) FROM recommendations WHERE competencia=?", comp), 2),
    }
    h = hashlib.sha256()
    for r in c.execute("SELECT opportunity_id, realizado, saving_est, saving, saving_efetivo, rescaldo_previsto, COALESCE(data_efetivada,''), COALESCE(analise,'') "
                       "FROM recommendations WHERE competencia=? ORDER BY opportunity_id", (comp,)):
        r = tuple(num(x) for x in r[:-1]) + (legado(r[-1]),)
        h.update(("|".join(str(round(x, 2)) if isinstance(x, float) else str(x) for x in r) + "\n").encode("utf-8"))
    m["hash_linhas"] = h.hexdigest()
    try:
        m["fechada"] = q("SELECT COALESCE(MAX(fechada),0) FROM competencias_fechadas WHERE competencia=?", comp)
        m["triggers_fechamento"] = q("SELECT COUNT(*) FROM sys.triggers WHERE name LIKE 'trg_fechamento%'" if azure else
                                     "SELECT COUNT(*) FROM sqlite_master WHERE type='trigger' AND name LIKE 'trg_fechamento%'")
    except Exception:
        m["fechada"] = None; m["triggers_fechamento"] = None
    c.close()
    return m

def main():
    modo, db, comp = sys.argv[1].upper(), sys.argv[2], sys.argv[3]
    if db.upper() != "AZURE" and not os.path.exists(db):
        print("ERRO: banco nao encontrado: " + db); sys.exit(2)
    m = medir(db, comp)
    for k, v in m.items():
        print("  %-22s %s" % (k, v))
    ref = REF.get(comp)
    if ref:
        for k, v in ref.items():
            ok = abs(m[k] - v) < 0.005
            print("  referencia %-18s %s (informado %.2f, banco %.2f)" % (k, "OK" if ok else "DIVERGE", v, m[k]))
    if modo == "GERAR":
        g = json.load(open(GOLDEN, encoding="utf-8")) if os.path.exists(GOLDEN) else {}
        g[comp] = m
        os.makedirs(os.path.dirname(GOLDEN), exist_ok=True)
        json.dump(g, open(GOLDEN, "w", encoding="utf-8"), indent=2, ensure_ascii=True)
        print("GOLDEN gravado em docs\\golden_numeros.json")
        return
    if not os.path.exists(GOLDEN):
        print("ERRO: rode GERAR primeiro (docs\\golden_numeros.json nao existe)"); sys.exit(2)
    g = json.load(open(GOLDEN, encoding="utf-8")).get(comp)
    if not g:
        print("ERRO: sem golden para " + comp); sys.exit(2)
    # SQLite e Azure tem quantidades diferentes de triggers de fechamento (o Azure tambem bloqueia INSERT)
    dif = [k for k in g if g[k] != m.get(k) and not (k == "triggers_fechamento" and db.upper() == "AZURE")]
    if dif:
        print("DIVERGE em: " + ", ".join(dif))
        for k in dif: print("   %s: golden=%s atual=%s" % (k, g[k], m.get(k)))
        sys.exit(1)
    print("OK - numeros e hash das linhas identicos ao golden")

main()
