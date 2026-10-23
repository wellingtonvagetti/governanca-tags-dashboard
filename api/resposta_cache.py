# -*- coding: utf-8 -*-
"""Respostas JSON grandes guardadas ja comprimidas (gzip), montadas uma vez por versao dos dados.

A lista do mes (~3 MB) e o historico (~2 MB) eram convertidos para JSON e comprimidos de novo a cada pedido;
com varios usuarios ao mesmo tempo isso prendia a CPU do plano B1 em 100%. Aqui a resposta e montada so quando a
`marca` muda (versao da competencia + identidade da lista em memoria) e depois so os bytes sao devolvidos.

Vale para 1 worker (como o app roda): a versao das recomendacoes e contada dentro do processo.
"""
import gzip
import json
import threading

from fastapi.encoders import jsonable_encoder
from fastapi.responses import Response

_CACHE = {}
_LOCK = threading.Lock()
_TRAVAS = {}  # uma trava por chave: montar a lista nao faz o historico (nem outro perfil) esperar


def _trava(chave):
    with _LOCK:
        return _TRAVAS.setdefault(chave, threading.Lock())


def json_gz(request, chave, marca, montar):
    """Devolve a resposta de `montar()` comprimida; refaz so quando `marca` muda para essa `chave`."""
    item = _CACHE.get(chave)
    if item is None or item[0] != marca:
        with _trava(chave):
            item = _CACHE.get(chave)
            if item is None or item[0] != marca:  # quem esperou na trava aproveita o que o outro montou
                corpo = json.dumps(jsonable_encoder(montar()), ensure_ascii=False, separators=(",", ":")).encode("utf-8")
                item = (marca, gzip.compress(corpo, compresslevel=5))
                _CACHE[chave] = item
    gz = item[1]
    aceita = "gzip" in ((request.headers.get("accept-encoding") if request is not None else "") or "").lower()
    if aceita:
        return Response(content=gz, media_type="application/json",
                        headers={"Content-Encoding": "gzip", "Vary": "Accept-Encoding", "Cache-Control": "no-cache"})
    return Response(content=gzip.decompress(gz), media_type="application/json", headers={"Cache-Control": "no-cache"})


def limpar():
    with _LOCK:
        _CACHE.clear()
        _TRAVAS.clear()
