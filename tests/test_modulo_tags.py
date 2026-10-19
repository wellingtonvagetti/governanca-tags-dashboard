# -*- coding: utf-8 -*-
import gzip
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from api import modulo_tags as mt  # noqa: E402


def fotografia(data="2026-10-08", ids=("a", "b", "c")):
    n = len(ids)
    return {
        "meta": {"date": data, "fullFile": "completo.csv", "scopeFile": "governanca.csv", "eligibilityApplied": True},
        "dict": {"BU": ["BANCOS", "FUNDOS"], "CLIENTE": ["INDEFINIDO", "X"]},
        "subs": [{"inScope": True}],
        "R": {"id": list(ids), "s": [0] * n, "g": list(range(n)), "sc": [1] * (n - 1) + [0],
              "BU": [0] * (n - 1) + [-1], "CLIENTE": [0] + [1] * (n - 1)},
    }


class TestModuloTags(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.pasta = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_sem_dados_abre_com_fotografia_vazia(self):
        base = mt.baseline(self.pasta)
        self.assertEqual(base["R"]["id"], [])
        lista = mt.listar_fotografias(self.pasta, base)
        self.assertEqual([x["id"] for x in lista], ["baseline"])
        self.assertEqual(mt.ler_configuracao(self.pasta)["subscriptions"], [])

    def test_resumo(self):
        r = mt.resumir(fotografia())
        self.assertEqual(r["complete"]["resources"], 3)
        self.assertEqual(r["governance"]["resources"], 2)
        self.assertEqual(r["outside"]["resources"], 1)
        self.assertEqual(r["complete"]["tags"]["BU"], {"filled": 2, "classified": 2, "total": 3})
        self.assertEqual(r["complete"]["tags"]["CLIENTE"], {"filled": 3, "classified": 2, "total": 3})

    def test_gravar_listar_atual_excluir(self):
        base = mt.baseline(self.pasta)
        t = mt.USUARIO_ATUAL.set("teste@evertec")
        try:
            m1 = mt.gravar_fotografia(self.pasta, fotografia("2026-10-08"))
            m2 = mt.gravar_fotografia(self.pasta, fotografia("2026-10-15", ids=("x",)))
        finally:
            mt.USUARIO_ATUAL.reset(t)
        self.assertEqual(m1["savedBy"], "teste@evertec")
        self.assertEqual(mt.fotografia_atual(self.pasta, base)["meta"]["date"], "2026-10-15")
        self.assertEqual(len(mt.listar_fotografias(self.pasta, base)), 3)
        mt.excluir_fotografia(self.pasta, m2["id"])
        self.assertEqual(mt.fotografia_atual(self.pasta, base)["meta"]["date"], "2026-10-08")
        mt.excluir_fotografia(self.pasta, m1["id"])
        self.assertFalse((self.pasta / "latest.txt").exists())
        self.assertEqual(mt.fotografia_atual(self.pasta, base), base)

    def test_validacoes(self):
        for ruim in (None, {"meta": {}}, {"meta": {"date": "08/10/2026"}, "R": {"id": []}}):
            with self.assertRaises(mt.ErroTags) as e:
                mt.gravar_fotografia(self.pasta, ruim)
            self.assertEqual(e.exception.status, 400)
        sem_eleg = fotografia()
        sem_eleg["meta"]["eligibilityApplied"] = False
        sem_eleg["R"]["CLASSE_INVENTARIO"] = [0, 0, 0]
        with self.assertRaises(mt.ErroTags):
            mt.gravar_fotografia(self.pasta, sem_eleg)
        for ident, status in (("baseline", 400), ("../x", 400), ("a b", 400), ("nao-existe", 404)):
            with self.assertRaises(mt.ErroTags) as e:
                mt.excluir_fotografia(self.pasta, ident)
            self.assertEqual(e.exception.status, status)

    def test_latest_invalido_volta_para_baseline(self):
        (self.pasta / "latest.txt").write_text("../../etc/passwd", "utf-8")
        base = mt.baseline(self.pasta)
        self.assertIs(mt.fotografia_atual(self.pasta, base), base)

    def test_normalizar_elegibilidade(self):
        snap = {"meta": {"eligibilityApplied": False},
                "dict": {"CLASSE_INVENTARIO": ["ELEGIVEL_OPERACIONAL", "EXCLUIDO_REGRA_ATUAL"]},
                "subs": [{"inScope": True}, {"inScope": True}],
                "R": {"id": ["a", "b", "c"], "s": [0, 1, 0], "g": [0, 1, 2], "CLASSE_INVENTARIO": [0, 1, 0], "BU": [0, 1, 0]}}
        n = mt.normalizar_elegibilidade(snap)
        self.assertEqual(n["R"]["id"], ["a", "c"])
        self.assertTrue(n["meta"]["eligibilityApplied"])
        self.assertTrue(n["meta"]["eligibilityRecoveredFromInventoryClass"])
        self.assertFalse(n["subs"][1]["inScope"])
        self.assertEqual(snap["R"]["id"], ["a", "b", "c"])

    def test_configuracao_limpa_campos(self):
        (self.pasta / "subscriptions-master.json").write_text(json.dumps([{"name": "s", "id": "x"}]), "utf-8")
        self.assertEqual(len(mt.ler_configuracao(self.pasta)["subscriptions"]), 1)
        sub = "0" * 8 + "-0000-0000-0000-" + "0" * 12
        limpo = mt.gravar_configuracao(self.pasta, {
            "officialMap": [{"CC": " 10 ", "BU": "BANCOS", "CCOWNER": "Fulano", "extra": 1}, {"CC": "", "BU": "X"}],
            "actions": [{"date": "2026-10-01", "action": "a" * 300, "processed": "12"}, {"date": "x", "action": "b"}],
            "subscriptions": [{"name": "sub", "id": sub.upper(), "inScope": "sim"}, {"name": "sem id", "id": "1"}],
        })
        self.assertEqual(limpo["officialMap"], [{"CC": "10", "BU": "BANCOS", "CCOWNER": "Fulano"}])
        self.assertEqual(len(limpo["actions"]), 1)
        self.assertEqual(len(limpo["actions"][0]["action"]), 160)
        self.assertEqual(limpo["actions"][0]["processed"], 12)
        self.assertEqual(limpo["subscriptions"], [{"name": "sub", "id": sub, "managementGroup": "", "status": "", "inScope": False}])
        self.assertEqual(mt.ler_configuracao(self.pasta)["officialMap"][0]["CC"], "10")

    def test_pagina_injeta_dados_sem_quebrar_script(self):
        snap = fotografia()
        snap["meta"]["fullFile"] = "</script><script>alert(1)</script>"
        with gzip.open(self.pasta / "baseline.json.gz", "wb") as f:
            f.write(json.dumps(snap).encode("utf-8"))
        html = mt.pagina(self.pasta)
        self.assertNotIn("__TAGS_SNAPSHOT__", html)
        self.assertNotIn("__TAGS_HISTORICO__", html)
        self.assertNotIn("</script><script>alert(1)", html)
        self.assertIn('data-mod-seletor="tags"', html)
        self.assertIn("/api/tags/snapshots", html)

    def test_modulo_sem_inventario_no_repositorio(self):
        import re
        for arq in [mt.MODULO_DIR / "index.html", mt.ASSETS_DIR / "dashboard-v2.js"]:
            texto = arq.read_text("utf-8")
            self.assertNotRegex(texto, r"/subscriptions/[0-9a-f]{8}-[0-9a-f]{4}-")
            self.assertLess(len(texto), 600_000, arq)
        self.assertFalse(re.search(r"'/api/(snapshots|governance-config)", (mt.MODULO_DIR / "index.html").read_text("utf-8")))


TEM_FASTAPI = all(importlib.util.find_spec(m) for m in ("fastapi", "httpx"))


@unittest.skipUnless(TEM_FASTAPI, "fastapi/httpx nao instalados (CI roda so a logica)")
class TestRotasTags(unittest.TestCase):
    def setUp(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from api import modulo_tags_rotas as rotas
        self.tmp = tempfile.TemporaryDirectory()
        self.antes = mt.os.environ.get("FINOPS_TAGS_DATA_DIR")
        mt.os.environ["FINOPS_TAGS_DATA_DIR"] = self.tmp.name
        app = FastAPI()
        app.include_router(rotas.router)
        app.add_exception_handler(mt.ErroTags, rotas.tratar_erro_tags)
        self.c = TestClient(app)

    def tearDown(self):
        if self.antes is None:
            mt.os.environ.pop("FINOPS_TAGS_DATA_DIR", None)
        else:
            mt.os.environ["FINOPS_TAGS_DATA_DIR"] = self.antes
        self.tmp.cleanup()

    def test_fluxo_http(self):
        self.assertEqual(self.c.get("/tags").status_code, 200)
        r = self.c.post("/api/tags/snapshots", json={"snapshot": {"meta": {}}})
        self.assertEqual((r.status_code, r.json()["error"]), (400, "Fotografia inválida ou sem Data de Coleta"))
        r = self.c.post("/api/tags/snapshots", content=b"xx")
        self.assertEqual((r.status_code, r.json()["error"]), (400, "Conteúdo JSON inválido"))
        r = self.c.post("/api/tags/snapshots", json={"snapshot": fotografia()})
        self.assertEqual(r.status_code, 201)
        ident = r.json()["snapshot"]["id"]
        self.assertEqual(len(self.c.get("/api/tags/snapshots").json()["snapshots"]), 2)
        self.assertIn('"date":"2026-10-08"', self.c.get("/tags").text)
        self.assertEqual(self.c.delete("/api/tags/snapshots/" + ident).json(), {"ok": True})
        self.assertEqual(self.c.put("/api/tags/governance-config", json={}).status_code, 200)


if __name__ == "__main__":
    unittest.main()
