# -*- coding: utf-8 -*-
"""Regressao da camada de dados (SQLite) sem depender do FastAPI.

Rodar: python -m unittest discover -s tests -v
"""
import os
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _banco_temp  # noqa: E402,F401  (define FINOPS_DB_PATH temporario antes de api.db)


class RegressaoDados(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # O banco temporario nasce vazio: a 1a conexao aplica database/schema.sql.
        from api import db, cost_service
        cls.db, cls.cost = db, cost_service

    def test_01_lote_insere_e_atualiza_sem_sobrescrever_financeiro(self):
        regs = [
            {"finOpsOpportunityId": "FINOPS-000001", "recommendation": "A", "item": "vm1", "provider": "AZURE",
             "squad": "Squad SRE", "savingEst": 100.5, "analise": "APROVADO", "realizado": True,
             "saving": 10, "savingEfetivo": 5, "rescaldoPrevisto": 2, "bu": "BANCOS"},
            {"finOpsOpportunityId": "FINOPS-000002", "recommendation": "B", "item": "vm2", "provider": "AWS",
             "squad": "Squad Bancos", "savingEst": 50, "analise": "", "bu": "DIGITAL"},
        ]
        self.assertEqual(self.db.salvar_recomendacoes_lote("2026-10", regs), 2)
        novo = [dict(regs[0], savingEst=999, saving=777, item="vm1-novo", squad="Squad X"), regs[1]]
        self.db.salvar_recomendacoes_lote("2026-10", novo)
        r = self.db.buscar_recomendacao("2026-10", "FINOPS-000001")
        self.assertEqual(r["item"], "vm1-novo")        # atualizado
        self.assertEqual(r["savingEst"], 999)          # atualizado
        self.assertEqual(r["saving"], 10)              # financeiro preservado
        self.assertEqual(r["savingEfetivo"], 5)        # financeiro preservado
        self.assertTrue(r["realizado"])
        self.assertEqual(self.db.total_competencia("2026-10"), 2)

    def test_02_consultas(self):
        self.assertEqual(self.db.contar_por_competencia(), {"2026-10": 2})
        ids = [x["finOpsOpportunityId"] for x in self.db.listar_recomendacoes_db("2026-10", q="vm", provider="azure")]
        self.assertEqual(ids, ["FINOPS-000001"])

    def test_03_historico_de_auditoria(self):
        with self.db.conectar() as con:
            for campo, novo in (("analise", "APROVADO"), ("ticket", "T-1")):
                con.execute("INSERT INTO recommendation_audit (competencia, opportunity_id, campo, valor_anterior, "
                            "valor_novo, usuario) VALUES ('2026-10', 'FINOPS-000002', ?, NULL, ?, 'tester')", (campo, novo))
            con.commit()
        hist = self.db.historico_recomendacao("2026-10", "FINOPS-000002")
        self.assertEqual([h["campo"] for h in hist], ["ticket", "analise"])   # mais recente primeiro
        self.assertEqual({h["usuario"] for h in hist}, {"tester"})
        self.assertEqual(self.db.historico_recomendacao("2026-10", "FINOPS-000001"), [])

    def test_03b_origem_dos_ids(self):
        # ID herdado de setembro (data trocada para 01/10 na consolidacao) x ID novo de outubro
        self.db.salvar_recomendacoes_lote("2026-09", [
            {"finOpsOpportunityId": "FINOPS-000901", "recommendation": "A", "item": "x", "provider": "AZURE",
             "dataRecomendada": "2026-09-16"}])
        self.db.salvar_recomendacoes_lote("2026-10", [
            {"finOpsOpportunityId": "FINOPS-000901", "recommendation": "A", "item": "x", "provider": "AZURE",
             "dataRecomendada": "2026-10-01"},
            {"finOpsOpportunityId": "FINOPS-000902", "recommendation": "B", "item": "y", "provider": "AWS",
             "dataRecomendada": "2026-10-05"}])
        o = self.db.origem_ids_competencia("2026-10")
        self.assertEqual(o["FINOPS-000901"], {"primeiraCompetencia": "2026-09", "primeiraData": "2026-09-16"})
        self.assertEqual(o["FINOPS-000902"], {"primeiraCompetencia": "2026-10", "primeiraData": "2026-10-05"})
        self.assertNotIn("FINOPS-000902", self.db.origem_ids_competencia("2026-09"))

    def test_03c_recomendado_por_padronizado(self):
        p = self.db.padronizar_recomendado_por
        casos = {"DEDALUS": "Dedalus", "EVERTEC": "Evertec", "FINOPS SOLO": "Solo", "LATAM": "Evertec Latam",
                 "EVERTEC - LATAM": "Evertec Latam", "DEDALUS - LATAM": "Evertec Latam",
                 "Solo - LATAM": "Evertec Latam", "Evertec-LATAM": "Evertec Latam", "Evertec Latam": "Evertec Latam",
                 "OUTRO": "OUTRO"}
        for de, para in casos.items():
            self.assertEqual(p(de), para, de)
        # de-para na importacao: grava e devolve no padrao novo
        self.db.salvar_recomendacoes_lote("2026-11", [
            {"finOpsOpportunityId": "FINOPS-009901", "recommendation": "A", "item": "x", "provider": "AZURE",
             "recomendadoPor": "EVERTEC - LATAM"}])
        reg = self.db.buscar_recomendacao("2026-11", "FINOPS-009901")
        self.assertEqual(reg["recomendadoPor"], "Evertec Latam")

    def test_03d_categoria_pelo_catalogo(self):
        c = self.db.categoria_do_catalogo
        self.assertEqual(c("Instances supported for switching to AMD type", "RIGHTSIZING"), "ARCHITECTURE")
        self.assertEqual(c("Cache clusters with no read/write operations"), "WASTE")
        self.assertEqual(c("recommendations to right size underutilized virtual machines"), "RIGHTSIZING")
        self.assertEqual(c("Fora do catalogo", "WASTE"), "WASTE")
        self.db.salvar_recomendacoes_lote("2026-11", [
            {"finOpsOpportunityId": "FINOPS-009902", "recommendation": "Orphaned Managed Disks", "item": "d",
             "provider": "AZURE", "categoria": "DATA_OPTIMIZATION"}])
        self.assertEqual(self.db.buscar_recomendacao("2026-11", "FINOPS-009902")["categoria"], "WASTE")

    def test_04_custos(self):
        base = {"provider": "azure", "year": 2026, "month": 10, "savedAt": "2026-10-09T00:00:00Z"}
        self.cost.salvar_cost_record(dict(base, text="abc", fileName="f.csv"))
        self.cost.salvar_cost_record(dict(base, text="def", fileName="g.csv", sourceType="PRODUCT"))
        self.cost.salvar_cost_record(dict(base, text="novo", fileName="h.csv"))   # upsert do mesmo periodo
        recs = {c["key"]: c for c in self.cost.carregar_cost_records()}
        self.assertEqual(set(recs), {"AZURE|2026-10", "AZURE|PRODUCT|2026-10"})
        self.assertEqual(recs["AZURE|2026-10"]["text"], "novo")
        self.assertEqual(recs["AZURE|PRODUCT|2026-10"]["text"], "def")

    def test_04a_linhas_produto_por_componente(self):
        texto = ('"Provider","Product","SKU/Type","Component","Details","Cost","AVG Cost/day"\n'
                 '"Azure x","Virtual Machines: Disks","Standard SSD Managed Disks","(128 GB) - DISCO_A","E4 LRS Disk Operations","1.013,11","2,62"\n'
                 '"Azure x","Virtual Machines: Disks","Standard SSD Managed Disks","(128 GB) - DISCO_B","E10 LRS Disk","10,62","2,12"\n')
        self.cost.salvar_cost_record({"provider": "azure", "year": 2026, "month": 12, "sourceType": "PRODUCT",
                                      "savedAt": "2026-12-05T00:00:00Z", "text": texto, "fileName": "p.csv"})
        linhas = self.cost.linhas_produto("AZURE", 2026, 12, ["disco_a"])
        self.assertEqual(len(linhas), 1)
        self.assertEqual(linhas[0]["details"], "E4 LRS Disk Operations")
        self.assertAlmostEqual(linhas[0]["cost"], 1013.11)
        self.assertAlmostEqual(linhas[0]["avgCostDay"], 2.62)
        self.assertEqual(linhas[0]["unit"], "")
        self.assertEqual(self.cost.linhas_produto("AZURE", 2026, 12, []), [])

    def test_04b_resumo_de_custos_sem_conteudo(self):
        # aba Custos Cloud: lista arquivo, tipo e data de gravacao, sem o CSV
        resumo = [r for r in self.cost.resumo_cost_records() if r["year"] == 2026 and r["month"] == 10]
        tipos = {r["sourceType"]: r for r in resumo if r["provider"] == "AZURE"}
        self.assertEqual(set(tipos), {"ID_HISTORY", "PRODUCT"})
        self.assertEqual(tipos["ID_HISTORY"]["fileName"], "h.csv")
        self.assertEqual(tipos["PRODUCT"]["savedAt"], "2026-10-09T00:00:00Z")
        self.assertNotIn("text", tipos["PRODUCT"])

    def test_05_etag_e_contagem_de_custos_sem_ler_conteudo(self):
        c = self.cost
        antes = c.cost_records_etag()
        n0 = c.contar_cost_records()
        c.salvar_cost_record({"provider": "AZURE", "year": 2026, "month": 12, "text": "a,b\n1,2", "savedAt": "2026-10-09T10:00:00Z"})
        e1 = c.cost_records_etag()
        self.assertNotEqual(antes, e1)                         # gravar muda o ETag
        self.assertEqual(c.cost_records_etag(), e1)            # sem mudanca, ETag estavel
        self.assertEqual(c.contar_cost_records(), n0 + 1)
        c.salvar_cost_record({"provider": "AZURE", "year": 2026, "month": 12, "text": "a,b\n1,3", "savedAt": "2026-10-09T11:00:00Z"})
        self.assertNotEqual(c.cost_records_etag(), e1)         # regravar muda o ETag
        self.assertEqual(c.contar_cost_records(), n0 + 1)      # mesma chave: nao duplica
        self.assertTrue(e1.startswith('W/"'))

    def test_06_payload_gzip_em_cache_por_etag(self):
        import gzip, json
        c = self.cost
        c.salvar_cost_record({"provider": "GCP", "year": 2026, "month": 10, "text": "x,y\n1,2", "savedAt": "2026-10-09T12:00:00Z"})
        e1 = c.cost_records_etag()
        g1 = c.costs_payload_gzip(e1)
        self.assertIs(c.costs_payload_gzip(e1), g1)            # mesmo ETag: reaproveita, sem reconstruir
        dados = json.loads(gzip.decompress(g1).decode("utf-8"))
        self.assertEqual(dados["status"], "ok")
        self.assertEqual(dados["total"], len(dados["costRecords"]))
        c.salvar_cost_record({"provider": "GCP", "year": 2026, "month": 10, "text": "x,y\n1,9", "savedAt": "2026-10-09T13:00:00Z"})
        e2 = c.cost_records_etag()
        self.assertNotEqual(e1, e2)
        g2 = c.costs_payload_gzip(e2)
        self.assertIsNot(g2, g1)                                # ETag novo: reconstroi
        textos = [r["text"] for r in json.loads(gzip.decompress(g2))["costRecords"] if r["provider"] == "GCP"]
        self.assertIn("x,y\n1,9", textos)

    def test_07_banco_novo_recebe_o_schema_completo(self):
        # Arquivo inexistente: a 1a conexao cria todas as tabelas, inclusive
        # cost_records com source_type e a UNIQUE de 4 colunas que o upsert usa.
        import tempfile
        from unittest import mock
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as d:
            with mock.patch.object(self.db, "DB_PATH", self.db.Path(d) / "novo.db"):
                with self.db.conectar() as con:
                    tabelas = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                self.assertLessEqual({"recommendations", "recommendation_audit", "app_state", "cost_records",
                                      "competencias_fechadas", "database_metadata"}, tabelas)
                base = {"provider": "AWS", "year": 2026, "month": 11, "text": "a", "savedAt": "2026-11-01T00:00:00Z"}
                self.cost.salvar_cost_record(base)
                self.cost.salvar_cost_record(dict(base, sourceType="PRODUCT"))
                self.cost.salvar_cost_record(dict(base, text="b"))
                recs = {c["key"]: c["text"] for c in self.cost.carregar_cost_records()}
                self.assertEqual(recs, {"AWS|2026-11": "b", "AWS|PRODUCT|2026-11": "a"})


if __name__ == "__main__":
    unittest.main()
