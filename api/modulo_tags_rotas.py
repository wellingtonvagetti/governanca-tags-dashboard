"""Rotas HTTP do modulo Governanca de Tags (regras em api/modulo_tags.py)."""

import json

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, Response
from starlette.concurrency import run_in_threadpool

from api.modulo_tags import (
    MAX_BODY,
    ErroTags,
    _erro,
    baseline,
    diretorio_dados,
    excluir_fotografia,
    gravar_configuracao,
    gravar_fotografia,
    ler_configuracao,
    listar_fotografias,
    pagina,
)

router = APIRouter()


async def _corpo_json(request: Request):
    partes, tamanho = [], 0
    async for parte in request.stream():
        tamanho += len(parte)
        if tamanho > MAX_BODY:
            raise _erro(413, "Arquivo excede o limite de 30 MB")
        partes.append(parte)
    try:
        return json.loads(b"".join(partes).decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        raise _erro(400, "Conteúdo JSON inválido")


@router.get("/tags", include_in_schema=False)
@router.get("/tags/", include_in_schema=False)
def tags_pagina():
    conteudo = pagina(diretorio_dados())
    return Response(content=conteudo, media_type="text/html; charset=utf-8",
                    headers={"Cache-Control": "no-store"})


@router.get("/api/tags/snapshots")
def tags_listar():
    pasta = diretorio_dados()
    return {"snapshots": listar_fotografias(pasta, baseline(pasta))}


@router.post("/api/tags/snapshots", status_code=201)
async def tags_gravar(request: Request):
    corpo = await _corpo_json(request)
    snapshot = corpo.get("snapshot") if isinstance(corpo, dict) else None
    meta = await run_in_threadpool(gravar_fotografia, diretorio_dados(), snapshot)
    return {"ok": True, "snapshot": meta}


@router.delete("/api/tags/snapshots/{ident}")
def tags_excluir(ident: str):
    excluir_fotografia(diretorio_dados(), ident)
    return {"ok": True}


@router.get("/api/tags/governance-config")
def tags_config():
    return ler_configuracao(diretorio_dados())


@router.put("/api/tags/governance-config")
async def tags_config_gravar(request: Request):
    corpo = await _corpo_json(request)
    return await run_in_threadpool(gravar_configuracao, diretorio_dados(), corpo)


async def tratar_erro_tags(_request, exc: ErroTags):
    # A tela de tags le "error" (mesmo formato do server.js original).
    return JSONResponse(status_code=exc.status, content={"ok": False, "error": exc.mensagem})
