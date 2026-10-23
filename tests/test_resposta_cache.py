# -*- coding: utf-8 -*-
"""Resposta JSON guardada ja comprimida: monta uma vez por marca, separa por chave e respeita o Accept-Encoding.

Rodar: python -m unittest discover -s tests -v
"""
import gzip
import importlib.util
import json
import os
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

TEM_FASTAPI = importlib.util.find_spec("fastapi") is not None
if TEM_FASTAPI:
    from api import resposta_cache  # noqa: E402


class _Req:
    def __init__(self, enc):
        self.headers = {"accept-encoding": enc}


@unittest.skipUnless(TEM_FASTAPI, "fastapi nao instalado (CI roda so a logica)")
class RespostaCache(unittest.TestCase):
    def setUp(self):
        resposta_cache.limpar()
        self.montagens = 0

    def montar(self, valor):
        def f():
            self.montagens += 1
            return {"v": valor, "ç": "ã"}
        return f

    def test_monta_uma_vez_por_marca(self):
        r1 = resposta_cache.json_gz(_Req("gzip, br"), ("lista", "2026-10", ("todas",)), (1, 10), self.montar(1))
        r2 = resposta_cache.json_gz(_Req("gzip"), ("lista", "2026-10", ("todas",)), (1, 10), self.montar(2))
        self.assertEqual(self.montagens, 1)
        self.assertEqual(r1.headers["content-encoding"], "gzip")
        self.assertEqual(json.loads(gzip.decompress(r2.body)), {"v": 1, "ç": "ã"})
        # versao nova (escrita no banco) refaz
        r3 = resposta_cache.json_gz(_Req("gzip"), ("lista", "2026-10", ("todas",)), (2, 10), self.montar(3))
        self.assertEqual(self.montagens, 2)
        self.assertEqual(json.loads(gzip.decompress(r3.body))["v"], 3)

    def test_chaves_separadas_e_sem_gzip(self):
        resposta_cache.json_gz(_Req("gzip"), ("lista", "2026-10", ("todas",)), (1,), self.montar("adm"))
        r = resposta_cache.json_gz(_Req(""), ("lista", "2026-10", ("squad", "squad bancos")), (1,), self.montar("sq"))
        self.assertEqual(self.montagens, 2)
        self.assertNotIn("content-encoding", r.headers)
        self.assertEqual(json.loads(r.body)["v"], "sq")


if __name__ == "__main__":
    unittest.main()
