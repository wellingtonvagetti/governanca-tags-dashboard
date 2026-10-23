# -*- coding: utf-8 -*-
"""RDC em PDF: campos preenchidos, paginacao da tabela e totais.

Rodar: python -m unittest discover -s tests -v
"""
import importlib.util
import io
import os
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _banco_temp  # noqa: E402,F401  (define FINOPS_DB_PATH temporario antes de api.db)

TEM_LIBS = all(importlib.util.find_spec(m) for m in ("reportlab", "pypdf"))


@unittest.skipUnless(TEM_LIBS, "reportlab/pypdf nao instalados")
class RdcPdf(unittest.TestCase):
    def gerar(self, n):
        from api.rdc_pdf import gerar_rdc
        from pypdf import PdfReader
        itens = [{"id": "FINOPS-%06d" % (i + 1), "recomendacao": "Right-size", "recurso": "vm-%d · PRD" % i,
                  "categoria": "Rightsizing", "mensal": 1000.5 + i} for i in range(n)]
        pdf = gerar_rdc({"identificacao": {"numero": "RDC-2026-10-X", "bu": "BANCOS"}, "itens": itens,
                         "justificativa": "FINOPS-000001: motivo → teste"})
        r = PdfReader(io.BytesIO(pdf))
        return r, {k: v.get("/V") for k, v in r.get_fields().items()}

    def test_campos_preenchidos_e_totais(self):
        r, f = self.gerar(3)
        self.assertEqual(len(r.pages), 2)
        self.assertEqual(f["ident_numero"], "RDC-2026-10-X")
        self.assertEqual(f["rec2_id"], "FINOPS-000002")
        self.assertEqual(f["rec1_mensal"], "R$ 1.000,50")
        self.assertEqual(f["rec1_anual"], "R$ 12.006,00")
        self.assertEqual(f["total_mensal"], "R$ 3.004,50")
        self.assertEqual(f["total_anual"], "R$ 36.054,00")
        self.assertIn("motivo -> teste", f["justificativa"])
        self.assertFalse(f.get("ident_diretor"))   # preenchido na reuniao
        self.assertIn("/CO", r.trailer["/Root"]["/AcroForm"])

    def test_tabela_continua_na_pagina_seguinte(self):
        r, f = self.gerar(14)
        self.assertEqual(len(r.pages), 3)
        self.assertEqual(f["rec14_id"], "FINOPS-000014")



@unittest.skipUnless(TEM_LIBS and all(importlib.util.find_spec(m) for m in ("fastapi", "httpx")), "fastapi/httpx ausentes")
class NumeroRdc(unittest.TestCase):
    def test_ordem_da_primeira_reprovacao_e_numero_fixo(self):
        from fastapi.testclient import TestClient
        from api import db, main
        with db.conectar() as con:
            for oid, quando in (("FINOPS-800001", "2027-05-19 10:00:00"), ("FINOPS-800002", "2027-05-15 09:00:00")):
                con.execute("INSERT INTO recommendation_audit (competencia, opportunity_id, campo, valor_anterior, "
                            "valor_novo, usuario, alterado_em) VALUES ('2027-05', ?, 'analise', 'Adiada', 'Reprovada', "
                            "'t', ?)", (oid, quando))
            con.commit()
        c = TestClient(main.app)
        url = "/api/rdc/2027-05/numeros"
        r = c.post(url, json={"squads": {"Squad A": ["FINOPS-800001"], "Squad B": ["FINOPS-800002"]}}).json()
        self.assertEqual(r, {"Squad B": "RDC-2027-05-0001", "Squad A": "RDC-2027-05-0002"})
        # squad nova entra depois; as anteriores nao mudam
        r = c.post(url, json={"squads": {"Squad C": ["FINOPS-800009"], "Squad A": ["FINOPS-800001"]}}).json()
        self.assertEqual((r["Squad B"], r["Squad A"], r["Squad C"]), ("RDC-2027-05-0001", "RDC-2027-05-0002", "RDC-2027-05-0003"))
        # mes seguinte continua a sequencia (numero nunca se repete entre competencias)
        r = c.post("/api/rdc/2027-06/numeros", json={"squads": {"Squad A": ["FINOPS-800001"]}}).json()
        self.assertEqual(r, {"Squad A": "RDC-2027-06-0004"})

    def test_meses_antes_de_outubro_2026_nao_numeram_nem_contam(self):
        from fastapi.testclient import TestClient
        from api import db, main
        with db.conectar() as con:
            con.execute("DELETE FROM app_state WHERE state_key LIKE 'rdc_numeros:%'")
            con.commit()
        c = TestClient(main.app)
        r = c.post("/api/rdc/2026-09/numeros", json={"squads": {"Squad X": ["FINOPS-900001"]}}).json()
        self.assertEqual(r, {})
        r = c.post("/api/rdc/2026-10/numeros", json={"squads": {"Squad Y": ["FINOPS-900002"]}}).json()
        self.assertEqual(r, {"Squad Y": "RDC-2026-10-0001"})
        with db.conectar() as con:
            con.execute("DELETE FROM app_state WHERE state_key LIKE 'rdc_numeros:%'")
            con.commit()


if __name__ == "__main__":
    unittest.main()
