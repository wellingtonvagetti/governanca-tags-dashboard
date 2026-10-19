"""Rotas HTTP do modulo Auditoria de Tags de VMs.

O modulo consulta a mesma fotografia persistida pelo modulo Governanca de Tags.
Ele nao grava inventario proprio nem replica configuracoes corporativas.
"""

from fastapi import APIRouter
from fastapi.responses import RedirectResponse, Response

from api.modulo_tags import diretorio_dados, pagina_auditoria_vms


router = APIRouter()


@router.get("/auditoria-vms", include_in_schema=False)
def auditoria_vms_pagina():
    return Response(
        content=pagina_auditoria_vms(diretorio_dados()),
        media_type="text/html; charset=utf-8",
        headers={"Cache-Control": "no-store"},
    )


@router.get("/auditoria-vms/", include_in_schema=False)
def auditoria_vms_barra():
    return RedirectResponse("/auditoria-vms", status_code=308)
