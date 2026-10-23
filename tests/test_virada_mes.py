# -*- coding: utf-8 -*-
"""Virada de mes: heranca das pendencias, historico das competencias anteriores
e restauracao da data original (tools/restaurar_data_recomendada.py).

Rodar: python -m unittest discover -s tests -v
"""
import importlib.util
import os
import subprocess
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _banco_temp  # noqa: E402,F401  (define FINOPS_DB_PATH temporario antes de api.db)

TEM_FASTAPI = all(importlib.util.find_spec(m) for m in ("fastapi", "httpx"))


def rec(oid, analise, data, **k):
    return dict({"finOpsOpportunityId": oid, "recommendation": "R", "item": oid.lower(), "provider": "AZURE",
                 "squad": "Squad SRE", "savingEst": 100, "analise": analise, "dataRecomendada": data}, **k)


@unittest.skipUnless(TEM_FASTAPI, "fastapi/httpx nao instalados (CI roda so a logica)")
class ViradaDeMes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from fastapi.testclient import TestClient
        from api import db, main
        cls.db = db
        cls.c = TestClient(main.app)
        db.salvar_recomendacoes_lote("2027-01", [
            rec("FINOPS-900001", "Validação Técnica", "2026-12-03"),
            rec("FINOPS-900002", "Capturado", "2026-12-04", realizado=True),
            rec("FINOPS-900003", "Reprovada", "2027-01-02"),
            rec("FINOPS-900004", "Adiada", ""),
        ])
        db.salvar_recomendacoes_lote("2026-12", [rec("FINOPS-900001", "Identificada", "2026-12-03")])

    def test_01_heranca_mantem_a_data_original(self):
        r = self.c.post("/api/recomendacoes/2027-01/reconciliar-pendencias/2027-02")
        self.assertEqual(r.status_code, 200, r.text)
        fev = {x["finOpsOpportunityId"]: x for x in self.db.listar_recomendacoes_db("2027-02")}
        self.assertEqual(sorted(fev), ["FINOPS-900001", "FINOPS-900004"])   # capturada e reprovada nao vem
        self.assertEqual(fev["FINOPS-900001"]["dataRecomendada"], "2026-12-03")
        self.assertEqual(fev["FINOPS-900004"]["dataRecomendada"], "2027-02-01")  # sem data: 1o dia do destino
        # rodar de novo nao duplica nada
        self.c.post("/api/recomendacoes/2027-01/reconciliar-pendencias/2027-02")
        self.assertEqual(self.db.total_competencia("2027-02"), 2)

    def test_02_historico_das_competencias_anteriores(self):
        h = self.c.get("/api/recomendacoes/2027-02/historico").json()
        self.assertEqual(h["competencias"][-2:], ["2026-12", "2027-01"])
        ids = {x["finOpsOpportunityId"]: x for x in h["recomendacoes"]}
        self.assertEqual(ids["FINOPS-900001"]["competencia"], "2027-01")    # a versao mais recente vale
        self.assertEqual(ids["FINOPS-900003"]["analise"], "Reprovada")
        self.assertNotIn("FINOPS-900005", ids)
        # a rota por ID continua respondendo (nao foi sombreada pela nova)
        self.assertEqual(self.c.get("/api/recomendacoes/2027-01/FINOPS-900001/historico").status_code, 200)

    def test_03_restaura_data_original(self):
        self.db.salvar_recomendacoes_lote("2027-03", [rec("FINOPS-900001", "Validação Técnica", "2027-03-01"),
                                                      rec("FINOPS-900009", "Rascunho", "2027-03-01")])
        ferramenta = os.path.join(RAIZ, "tools", "restaurar_data_recomendada.py")
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        s = subprocess.run([sys.executable, ferramenta, "SIMULAR", "2027-03"], env=env, capture_output=True, text=True)
        self.assertIn("1 com data a restaurar", s.stdout, s.stderr)
        self.assertEqual(self.db.buscar_recomendacao("2027-03", "FINOPS-900001")["dataRecomendada"], "2027-03-01")
        s = subprocess.run([sys.executable, ferramenta, "APLICAR", "2027-03"], env=env, capture_output=True, text=True)
        self.assertEqual(s.returncode, 0, s.stdout + s.stderr)
        self.assertEqual(self.db.buscar_recomendacao("2027-03", "FINOPS-900001")["dataRecomendada"], "2026-12-03")
        self.assertEqual(self.db.buscar_recomendacao("2027-03", "FINOPS-900009")["dataRecomendada"], "2027-03-01")


if __name__ == "__main__":
    unittest.main()
