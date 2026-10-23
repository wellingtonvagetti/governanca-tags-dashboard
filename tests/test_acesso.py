# -*- coding: utf-8 -*-
"""Perfis de acesso (api/acesso.py): admin, responsavel de squad e bloqueado.

Rodar: python -m unittest discover -s tests -v
"""
import importlib.util
import json
import os
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _banco_temp  # noqa: E402,F401  (define FINOPS_DB_PATH temporario antes de api.db)

TEM_FASTAPI = all(importlib.util.find_spec(m) for m in ("fastapi", "httpx"))


def rec(oid, squad, analise="Validação Técnica"):
    return {"finOpsOpportunityId": oid, "recommendation": "R", "item": oid.lower(), "provider": "AZURE",
            "squad": squad, "savingEst": 100, "analise": analise, "realizado": False}


@unittest.skipUnless(TEM_FASTAPI, "fastapi/httpx nao instalados")
class Acesso(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from fastapi.testclient import TestClient
        from api import db, main
        cls.db = db
        db.salvar_recomendacoes_lote("2028-01", [rec("FINOPS-700001", "Squad Bancos"), rec("FINOPS-700002", "Squad Fundos")])
        cfg = {"squad bancos": {"name": "Squad Bancos", "emailSquad": "champ@x.com", "emailGestor": "gestor@x.com; outro@x.com"},
               "squad fundos": {"name": "Squad Fundos", "emailSquad": "fundos@x.com"}}
        with db.conectar() as con:
            con.execute("INSERT INTO app_state (state_key, state_value, updated_at) VALUES ('finops_squad_config_v111', ?, 'x')",
                        (json.dumps(cfg),))
            con.commit()
        cls.c = TestClient(main.app)
        cls.antes = os.environ.get("FINOPS_ADMINS")
        os.environ["FINOPS_ADMINS"] = "finops@x.com"

    @classmethod
    def tearDownClass(cls):
        # o banco temporario e compartilhado entre os arquivos de teste: limpa o que este criou
        with cls.db.conectar() as con:
            con.execute("DELETE FROM recommendations WHERE competencia = '2028-01'")
            con.execute("DELETE FROM recommendation_audit WHERE competencia = '2028-01'")
            con.execute("DELETE FROM app_state WHERE state_key = 'finops_squad_config_v111'")
            con.commit()
        if cls.antes is None:
            os.environ.pop("FINOPS_ADMINS", None)
        else:
            os.environ["FINOPS_ADMINS"] = cls.antes

    def get(self, url, email):
        return self.c.get(url, headers={"X-MS-CLIENT-PRINCIPAL-NAME": email})

    def post(self, url, email, corpo):
        return self.c.post(url, json=corpo, headers={"X-MS-CLIENT-PRINCIPAL-NAME": email})

    def test_perfis(self):
        self.assertEqual(self.get("/api/acesso/eu", "FinOps@x.com").json()["papel"], "admin")
        eu = self.get("/api/acesso/eu", "outro@x.com").json()
        self.assertEqual((eu["papel"], eu["squads"]), ("squad", ["Squad Bancos"]))
        self.assertEqual(self.get("/api/acesso/eu", "ninguem@x.com").json()["papel"], "bloqueado")
        self.assertEqual(self.get("/api/recomendacoes/2028-01", "ninguem@x.com").status_code, 403)

    def test_squad_ve_e_grava_so_o_permitido(self):
        ids = [r["finOpsOpportunityId"] for r in self.get("/api/recomendacoes/2028-01", "champ@x.com").json()["recomendacoes"]]
        self.assertEqual(ids, ["FINOPS-700001"])
        url = "/api/recomendacoes/2028-01/estado-completo-lote"
        r = self.post(url, "champ@x.com", {"itens": [{"finOpsOpportunityId": "FINOPS-700002", "recomendacao": {"analise": "Reprovada"}}]})
        self.assertEqual(r.status_code, 422)
        r = self.post(url, "champ@x.com", {"itens": [{"finOpsOpportunityId": "FINOPS-700001", "recomendacao": {"analise": "Reprovada"}}]})
        self.assertEqual(r.status_code, 422)   # sem observacao
        r = self.post(url, "champ@x.com", {"itens": [{"finOpsOpportunityId": "FINOPS-700001", "recomendacao": {
            "analise": "Reprovada", "realizado": False, "observacao": "motivo", "savingEst": 999999, "squad": "Squad Fundos"}}]})
        self.assertEqual(r.status_code, 200, r.text)
        atual = self.db.buscar_recomendacao("2028-01", "FINOPS-700001")
        self.assertEqual((atual["analise"], atual["observacao"], atual["savingEst"], atual["squad"]),
                         ("Reprovada", "motivo", 100, "Squad Bancos"))
        self.assertEqual(self.post("/api/app-state/item", "champ@x.com", {"key": "finops_x", "value": "1"}).status_code, 403)
        r = self.post(url, "champ@x.com", {"itens": [{"finOpsOpportunityId": "FINOPS-700001", "recomendacao": {
            "squadNaoResponsavel": True, "squadNaoResponsavelMotivo": "recurso do time X"}}]})
        self.assertEqual(r.status_code, 200, r.text)
        atual = self.db.buscar_recomendacao("2028-01", "FINOPS-700001")
        self.assertEqual((atual["squadNaoResponsavel"], atual["squadNaoResponsavelPor"], atual["analise"]),
                         (True, "champ@x.com", "Reprovada"))

    def test_sem_lista_de_admins_todos_sao_admin(self):
        os.environ["FINOPS_ADMINS"] = ""
        try:
            self.assertEqual(self.get("/api/acesso/eu", "ninguem@x.com").json()["papel"], "admin")
        finally:
            os.environ["FINOPS_ADMINS"] = "finops@x.com"


if __name__ == "__main__":
    unittest.main()
