# -*- coding: utf-8 -*-
"""Todos os testes usam um banco temporario.

FINOPS_DB_PATH precisa existir ANTES de qualquer "import api.db" (o caminho e lido
uma unica vez, na importacao). Importe este modulo primeiro: `import _banco_temp`.
"""
import atexit
import os
import tempfile

if "FINOPS_DB_PATH" not in os.environ:
    _dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
    os.environ["FINOPS_DB_PATH"] = os.path.join(_dir.name, "teste.db")
    atexit.register(_dir.cleanup)
os.environ.pop("FINOPS_SQL_SERVER", None)
