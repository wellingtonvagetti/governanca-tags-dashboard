# -*- coding: utf-8 -*-
"""Versao da tabela recommendations (Azure SQL) e cache da listagem.

Nao precisa de banco nem de FastAPI: usa uma conexao falsa no lugar do pymssql.
Rodar: python -m unittest discover -s tests -v
"""
import os
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _banco_temp  # noqa: E402,F401  (define FINOPS_DB_PATH temporario antes de api.db)

from api import db, sqldb  # noqa: E402


class _CursorFalso:
    description = None
    rowcount = 0

    def execute(self, *a, **k):
        pass

    def executemany(self, *a, **k):
        pass

    def fetchall(self):
        return []

    def fetchone(self):
        return None


class _RawFalso:
    def cursor(self):
        return _CursorFalso()

    def commit(self):
        pass

    def rollback(self):
        pass

    def close(self):
        pass


def _versao_apos(sql, finalizar="commit", **k):
    con = sqldb.AzConnection(_RawFalso())
    antes = sqldb.versao_recomendacoes()
    con.execute(sql, k.get("params"))
    getattr(con, finalizar)()
    return sqldb.versao_recomendacoes() - antes


class VersaoRecomendacoes(unittest.TestCase):
    def test_leitura_nao_sobe_versao(self):
        self.assertEqual(_versao_apos("SELECT * FROM recommendations WHERE competencia = ?", params=("2026-10",)), 0)

    def test_escritas_sobem_versao_so_no_commit(self):
        for sql in (
            "UPDATE recommendations SET saving = ? WHERE competencia = ?",
            "INSERT INTO recommendations (competencia) VALUES (?)",
            "DELETE FROM recommendations WHERE competencia = ?",
            'MERGE "recommendations" AS t USING (SELECT 1) AS s ON 1=1',
        ):
            self.assertEqual(_versao_apos(sql, params=(1, 2)), 1, sql)
            self.assertEqual(_versao_apos(sql, finalizar="rollback", params=(1, 2)), 0, sql)

    def test_outras_tabelas_nao_sobem_versao(self):
        self.assertEqual(_versao_apos("INSERT INTO recommendation_audit (x) VALUES (?)", params=(1,)), 0)
        self.assertEqual(_versao_apos("UPDATE app_state SET state_value = ?", params=("a",)), 0)

    def test_with_sem_erro_confirma_e_com_erro_nao(self):
        antes = sqldb.versao_recomendacoes()
        with sqldb.AzConnection(_RawFalso()) as con:
            con.execute("UPDATE recommendations SET saving = ?", (1,))
        self.assertEqual(sqldb.versao_recomendacoes() - antes, 1)
        try:
            with sqldb.AzConnection(_RawFalso()) as con:
                con.execute("UPDATE recommendations SET saving = ?", (1,))
                raise RuntimeError("falha")
        except RuntimeError:
            pass
        self.assertEqual(sqldb.versao_recomendacoes() - antes, 1)


class CacheListagem(unittest.TestCase):
    def setUp(self):
        self.chamadas = 0
        self._orig = db.listar_recomendacoes_db

        def falso(competencia, **k):
            self.chamadas += 1
            return [{"id": self.chamadas}]

        db.listar_recomendacoes_db = falso
        db._RECS_CACHE.clear()
        db._RECS_RELENDO.clear()

    def tearDown(self):
        db.listar_recomendacoes_db = self._orig
        db._RECS_CACHE.clear()

    def test_segunda_leitura_vem_do_cache(self):
        a, c1 = db.listar_recomendacoes_cache("2026-10")
        b, c2 = db.listar_recomendacoes_cache("2026-10")
        self.assertEqual((c1, c2, self.chamadas), (False, True, 1))
        self.assertEqual(a, b)

    def test_escrita_invalida_o_cache(self):
        db.listar_recomendacoes_cache("2026-10")
        _versao_apos("UPDATE recommendations SET saving = ?", params=(1,))
        _, veio = db.listar_recomendacoes_cache("2026-10")
        self.assertFalse(veio)
        self.assertEqual(self.chamadas, 2)

    def test_competencias_sao_independentes(self):
        db.listar_recomendacoes_cache("2026-10")
        _, veio = db.listar_recomendacoes_cache("2026-09")
        self.assertFalse(veio)

    def test_ttl_vencido_serve_o_que_tem_e_atualiza_em_segundo_plano(self):
        import time

        a, _ = db.listar_recomendacoes_cache("2026-10")
        antigo = db.RECS_CACHE_TTL_S
        db.RECS_CACHE_TTL_S = -1
        try:
            b, veio = db.listar_recomendacoes_cache("2026-10")
            self.assertTrue(veio)          # nao espera a releitura
            self.assertEqual(a, b)         # serve o que estava em memoria
            for _ in range(200):           # a releitura roda em segundo plano
                if db._RECS_CACHE["2026-10"][2] == [{"id": 2}]:
                    break
                time.sleep(0.01)
            self.assertEqual(self.chamadas, 2)
            db.RECS_CACHE_TTL_S = antigo
            c, veio = db.listar_recomendacoes_cache("2026-10")
            self.assertTrue(veio)
            self.assertEqual(c, [{"id": 2}])  # proxima leitura ja vem atualizada
        finally:
            db.RECS_CACHE_TTL_S = antigo

    def test_versao_nova_nunca_serve_dado_velho_mesmo_dentro_do_ttl(self):
        db.listar_recomendacoes_cache("2026-10")
        _versao_apos("UPDATE recommendations SET saving = ?", params=(1,))
        dados, veio = db.listar_recomendacoes_cache("2026-10")
        self.assertFalse(veio)
        self.assertEqual(dados, [{"id": 2}])


class VersaoPorCompetencia(unittest.TestCase):
    def test_escrita_de_outubro_nao_invalida_setembro(self):
        set_antes, out_antes = sqldb.versao_competencia("2026-09"), sqldb.versao_competencia("2026-10")
        _versao_apos("UPDATE recommendations SET analise = ? WHERE competencia = ? AND opportunity_id = ?",
                     params=("Capturado", "2026-10", "FINOPS-1"))
        self.assertEqual(sqldb.versao_competencia("2026-09"), set_antes)
        self.assertNotEqual(sqldb.versao_competencia("2026-10"), out_antes)

    def test_escrita_sem_competencia_invalida_todas(self):
        antes = sqldb.versao_competencia("2026-09")
        _versao_apos("UPDATE recommendations SET saving = ?", params=(1,))
        self.assertNotEqual(sqldb.versao_competencia("2026-09"), antes)

    def test_data_completa_nao_e_competencia(self):
        antes = sqldb.versao_competencia("2026-09")
        _versao_apos("UPDATE recommendations SET data_prevista = ? WHERE opportunity_id = ?", params=("2026-10-15", "X"))
        self.assertNotEqual(sqldb.versao_competencia("2026-09"), antes)  # sem AAAA-MM: invalida todas (seguro)


class AtualizacaoParcial(unittest.TestCase):
    def setUp(self):
        self._orig = (db.listar_recomendacoes_db, db.buscar_recomendacao)
        self.leituras = 0

        def listar(competencia, **k):
            self.leituras += 1
            return [{"finOpsOpportunityId": "A", "savingEst": 10, "analise": "x"},
                    {"finOpsOpportunityId": "B", "savingEst": 5, "analise": "x"}]

        db.listar_recomendacoes_db = listar
        db.buscar_recomendacao = lambda c, oid: {"finOpsOpportunityId": oid, "savingEst": 5, "analise": "Capturado"}
        db._RECS_CACHE.clear()

    def tearDown(self):
        db.listar_recomendacoes_db, db.buscar_recomendacao = self._orig
        db._RECS_CACHE.clear()

    def gravar_b(self):
        _versao_apos("UPDATE recommendations SET analise = ? WHERE competencia = ? AND opportunity_id = ?",
                     params=("Capturado", "2027-01", "B"))

    def test_troca_so_a_linha_gravada_sem_reler(self):
        db.listar_recomendacoes_cache("2027-01")
        antes = sqldb.versao_competencia("2027-01")
        self.gravar_b()
        self.assertTrue(db.atualizar_cache_linhas("2027-01", ["B"], antes))
        dados, veio = db.listar_recomendacoes_cache("2027-01")
        self.assertTrue(veio)
        self.assertEqual(self.leituras, 1)
        self.assertEqual([d["analise"] for d in dados], ["x", "Capturado"])

    def test_outra_escrita_no_meio_rele_tudo(self):
        db.listar_recomendacoes_cache("2027-01")
        antes = sqldb.versao_competencia("2027-01")
        self.gravar_b()
        self.gravar_b()
        self.assertFalse(db.atualizar_cache_linhas("2027-01", ["B"], antes))
        db.listar_recomendacoes_cache("2027-01")
        self.assertEqual(self.leituras, 2)


if __name__ == "__main__":
    unittest.main()
