# -*- coding: utf-8 -*-
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from api import status as st  # noqa: E402


class TestNormalizar(unittest.TestCase):
    def test_regra_do_aprovado(self):
        self.assertEqual(st.normalizar("APROVADO", True, ""), st.CAPTURADO)
        self.assertEqual(st.normalizar("APROVADO", False, "CHG123"), st.PLANEJADA)
        self.assertEqual(st.normalizar("APROVADO", False, "CHG123", "Chamado Dedalus - SR-437072"), st.IMPLEMENTACAO)
        self.assertEqual(st.normalizar("APROVADO", True, "CHG123", "Chamado Dedalus - SR-437072"), st.CAPTURADO)
        self.assertEqual(st.normalizar("APROVADO", False, "", "Dedalus responsável pela execução, ticket aberto SR-453663"), st.IMPLEMENTACAO)
        self.assertEqual(st.normalizar("APROVADO", False, "", "aguardando janela"), st.PLANEJADA)
        self.assertEqual(st.normalizar("APROVADO", False, "  "), st.PLANEJADA)
        self.assertEqual(st.normalizar("aprovado", 1, "CHG123"), st.CAPTURADO)

    def test_demais_antigos(self):
        self.assertEqual(st.normalizar("EM ANÁLISE"), st.VALIDACAO)
        self.assertEqual(st.normalizar("em analise"), st.VALIDACAO)
        self.assertEqual(st.normalizar("ADIAR"), st.ADIADA)
        self.assertEqual(st.normalizar("REPROVADO"), st.REPROVADA)
        self.assertEqual(st.normalizar(""), st.RASCUNHO)
        self.assertEqual(st.normalizar(None), st.RASCUNHO)

    def test_coerencia_com_realizado(self):
        self.assertEqual(st.normalizar(st.PLANEJADA, True), st.CAPTURADO)
        self.assertEqual(st.normalizar(st.IMPLEMENTACAO, True), st.CAPTURADO)
        self.assertEqual(st.normalizar(st.CAPTURADO, False, ""), st.PLANEJADA)
        self.assertEqual(st.normalizar(st.CAPTURADO, False, "CHG1"), st.PLANEJADA)
        self.assertEqual(st.normalizar(st.CAPTURADO, True), st.CAPTURADO)

    def test_idempotente(self):
        for s in st.STATUS:
            for realizado in (False, True):
                a = st.normalizar(s, realizado, "CHG1")
                self.assertEqual(st.normalizar(a, realizado, "CHG1"), a)

    def test_pendente_equivale_a_regra_antiga(self):
        # antigo: EM ANALISE, ADIAR ou APROVADO nao realizado
        self.assertTrue(st.pendente("EM ANÁLISE"))
        self.assertTrue(st.pendente("ADIAR"))
        self.assertTrue(st.pendente("APROVADO", False))
        self.assertFalse(st.pendente("APROVADO", True))
        self.assertFalse(st.pendente("REPROVADO"))
        self.assertFalse(st.pendente(st.CAPTURADO, True))
        self.assertTrue(st.pendente(st.PLANEJADA))
        self.assertTrue(st.pendente(st.IMPLEMENTACAO))

    def test_legado_nos_dois_vocabularios(self):
        for novo, antigo in [
            (st.CAPTURADO, "APROVADO"), (st.PLANEJADA, "APROVADO"), (st.IMPLEMENTACAO, "APROVADO"),
            (st.VALIDACAO, "EM ANÁLISE"), (st.ADIADA, "ADIAR"), (st.REPROVADA, "REPROVADO"),
            (st.RASCUNHO, ""), (st.IDENTIFICADA, ""),
        ]:
            self.assertEqual(st.legado(novo), antigo)
            self.assertEqual(st.legado(antigo), antigo)

    def test_aprovado(self):
        self.assertTrue(st.aprovado(st.PLANEJADA))
        self.assertTrue(st.aprovado("APROVADO"))
        self.assertFalse(st.aprovado(st.VALIDACAO))
        self.assertFalse(st.aprovado(st.REPROVADA))


class TestConversaoDoBanco(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory()
        self.db = os.path.join(self.pasta.name, "finops_dev.db")
        con = sqlite3.connect(self.db)
        con.executescript((RAIZ / "database" / "schema.sql").read_text(encoding="utf-8-sig"))
        linhas = [
            ("2026-09", "A1", "APROVADO", 1, "", 100.0, 100.0),
            ("2026-09", "A2", "APROVADO", 0, "CHG9", 50.0, 0.0),
            ("2026-09", "A3", "APROVADO", 0, "", 20.0, 0.0),
            ("2026-09", "A4", "EM ANÁLISE", 0, "", 10.0, 0.0),
            ("2026-09", "A5", "ADIAR", 0, "", 5.0, 0.0),
            ("2026-09", "A6", "REPROVADO", 0, "", 7.0, 0.0),
            ("2026-10", "B1", "", 0, "", 3.0, 0.0),
        ]
        for comp, oid, an, real, tk, est, ef in linhas:
            con.execute(
                "INSERT INTO recommendations (competencia, opportunity_id, analise, realizado, ticket, saving_est, saving_efetivo, payload_json) "
                "VALUES (?,?,?,?,?,?,?,?)",
                (comp, oid, an, real, tk, est, ef, '{"analise": "%s", "x": 1}' % an),
            )
        con.commit()
        con.close()

    def tearDown(self):
        self.pasta.cleanup()

    def rodar(self, *args):
        return subprocess.run(
            [sys.executable, "-I", str(RAIZ / "tools" / "converter_status_analise.py"), *args],
            capture_output=True, text=True, encoding="utf-8",
        )

    def lidos(self):
        con = sqlite3.connect(self.db)
        r = dict(con.execute("SELECT opportunity_id, analise FROM recommendations"))
        pay = con.execute("SELECT payload_json FROM recommendations WHERE opportunity_id='A1'").fetchone()[0]
        con.close()
        return r, pay

    def test_simular_nao_altera(self):
        r = self.rodar("SIMULAR", self.db)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.lidos()[0]["A1"], "APROVADO")

    def test_aplicar_converte_e_e_idempotente(self):
        # congela setembro com os triggers reais
        r0 = subprocess.run(
            [sys.executable, "-I", str(RAIZ / "tools" / "freeze_competencia.py"), "APLICAR", self.db, "2026-09"],
            capture_output=True, text=True, encoding="utf-8",
        )
        self.assertEqual(r0.returncode, 0, r0.stdout + r0.stderr)
        r = self.rodar("APLICAR", self.db)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        novo, payload = self.lidos()
        self.assertEqual(novo["A1"], st.CAPTURADO)
        self.assertEqual(novo["A2"], st.PLANEJADA)
        self.assertEqual(novo["A3"], st.PLANEJADA)
        self.assertEqual(novo["A4"], st.VALIDACAO)
        self.assertEqual(novo["A5"], st.ADIADA)
        self.assertEqual(novo["A6"], st.REPROVADA)
        self.assertEqual(novo["B1"], st.RASCUNHO)
        self.assertIn("Capturado", payload)
        self.assertIn('"x": 1', payload)
        self.assertTrue(any(n.startswith("finops_dev.before_status_") for n in os.listdir(self.pasta.name)))
        r2 = self.rodar("APLICAR", self.db)
        self.assertEqual(r2.returncode, 0, r2.stdout + r2.stderr)
        self.assertIn("Nada a converter", r2.stdout)


if __name__ == "__main__":
    unittest.main()
