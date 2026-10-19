from fastapi import (
    Body,
    FastAPI,
    HTTPException,
    Query,
    Request,
)
from starlette.middleware.gzip import GZipMiddleware

from fastapi.responses import RedirectResponse, Response
from starlette.staticfiles import StaticFiles

import os
from contextlib import asynccontextmanager
from pathlib import Path

from api.db import (
    DB_PATH,
    USUARIO_ATUAL,
    conectar,
    contar_por_competencia,
    listar_recomendacoes_cache,
    listar_recomendacoes_db,
    total_competencia,
    buscar_recomendacao,
    historico_recomendacao,
    origem_ids_competencia,
    padronizar_recomendado_por,
    salvar_recomendacoes_lote,
)

from api.sqldb import (
    USE_AZURE_SQL,
    colunas_da_tabela,
    upsert as _finops_upsert_sql,
)

from api.cost_service import (
    contar_cost_records,
    cost_records_etag,
    costs_payload_gzip,
    linhas_produto,
    resumo_cost_records,
    salvar_cost_record,
)

from api import status as _status
from api import modulo_tags as _modulo_tags
from api import modulo_tags_rotas as _modulo_tags_rotas
from api import modulo_auditoria_vms_rotas as _modulo_auditoria_vms_rotas
from api.email_service import (
    enviar_email as enviar_email_servico,
)


BASE_DIR = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

FRONTEND_DIR = BASE_DIR / "frontend"


@asynccontextmanager
async def _lifespan(_app):
    # Tarefas de startup (as funcoes ficam mais abaixo; rodam so ao subir o app).
    _finops_aquecer_custos_v402()
    _finops_aquecer_recomendacoes_v404()
    _finops_backup_startup_v322()
    yield


app = FastAPI(
    title="FinOps API",
    version="0.6.0",
    lifespan=_lifespan
)

# V401: comprime as respostas grandes (o JSON de custos passa de 90 MB).
app.add_middleware(
    GZipMiddleware,
    minimum_size=1024,
    compresslevel=4
)


@app.middleware("http")
async def _finops_usuario_middleware_v322(request, call_next):
    nome = (request.headers.get("x-ms-client-principal-name") or "").strip()
    if not nome and os.getenv("FINOPS_REQUIRE_AUTH", "") == "1":
        return Response(content="Autenticacao necessaria", status_code=401)
    token = USUARIO_ATUAL.set((nome or "dev-local")[:120])
    try:
        return await call_next(request)
    finally:
        USUARIO_ATUAL.reset(token)


def _finops_aquecer_custos_v402():
    # Monta o JSON de custos em segundo plano para o 1o usuario nao esperar.
    import threading as _th_v402

    def _aquecer():
        try:
            costs_payload_gzip(cost_records_etag())
        except Exception:
            pass

    _th_v402.Thread(target=_aquecer, daemon=True).start()


def _finops_aquecer_recomendacoes_v404():
    # Azure SQL: le as 2 competencias mais recentes em segundo plano, para a
    # 1a abertura depois do deploy nao pagar a leitura fria (~2 s cada).
    if not USE_AZURE_SQL:
        return

    import threading as _th_v404

    def _aquecer():
        try:
            for comp in sorted(
                contar_por_competencia()
            )[-2:]:
                listar_recomendacoes_cache(comp)
        except Exception:
            pass

    _th_v404.Thread(target=_aquecer, daemon=True).start()


def _finops_backup_startup_v322():
    if USE_AZURE_SQL:
        return
    from api.backup_service import iniciar_backup_periodico
    iniciar_backup_periodico(DB_PATH)


# Plataforma: pagina inicial com os modulos; cada modulo tem a sua rota.
#   /                inicio (frontend/inicio.html)
#   /recomendacoes   modulo Recomendacoes FinOps (frontend/index.html)
#   /tags            modulo Governanca de Tags
#   /auditoria-vms   modulo Auditoria de Tags de VMs (mesma fotografia de Tags)
app.mount(
    "/plataforma",
    StaticFiles(directory=FRONTEND_DIR / "plataforma"),
    name="plataforma"
)
app.mount(
    "/tags/assets",
    StaticFiles(directory=_modulo_tags.ASSETS_DIR),
    name="tags-assets"
)
app.include_router(_modulo_tags_rotas.router)
app.include_router(_modulo_auditoria_vms_rotas.router)
app.add_exception_handler(_modulo_tags.ErroTags, _modulo_tags_rotas.tratar_erro_tags)


def _pagina_frontend(nome):

    caminho = FRONTEND_DIR / nome

    if not caminho.exists():

        raise HTTPException(
            status_code=404,
            detail=f"frontend/{nome} não encontrado"
        )

    return Response(content=caminho.read_bytes(), media_type="text/html; charset=utf-8")


@app.get(
    "/",
    include_in_schema=False
)
def inicio():
    return _pagina_frontend("inicio.html")


@app.get(
    "/recomendacoes",
    include_in_schema=False
)
def dashboard():
    return _pagina_frontend("index.html")


@app.get(
    "/recomendacoes/",
    include_in_schema=False
)
def dashboard_barra():
    return RedirectResponse("/recomendacoes", status_code=308)


@app.get("/api/health")
def health():

    if USE_AZURE_SQL:
        try:
            with conectar() as _con_h:
                _con_h.execute("SELECT 1").fetchone()
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail="Azure SQL indisponivel: %s" % exc
            )
    elif not DB_PATH.exists():

        raise HTTPException(
            status_code=500,
            detail=(
                "Banco SQLite não encontrado: "
                "confira FINOPS_DB_PATH"
            )
        )

    return {
        "status": "ok",
        "api_version": "0.6.0",
        "database": "azure-sql" if USE_AZURE_SQL else "sqlite",
        "competencias":
            contar_por_competencia()
    }


@app.get(
    "/api/recomendacoes/{competencia}"
)
def listar_recomendacoes(
    competencia: str,

    q: str | None = Query(
        default=None
    ),

    provider: str | None = Query(
        default=None
    ),

    bu: str | None = Query(
        default=None
    ),

    squad: str | None = Query(
        default=None
    ),

    categoria: str | None = Query(
        default=None
    ),

    analise: str | None = Query(
        default=None
    ),

    ambiente: str | None = Query(
        default=None
    ),
):

    sem_filtros = not any((
        q, provider, bu, squad,
        categoria, analise, ambiente,
    ))

    if USE_AZURE_SQL and sem_filtros:

        # Azure SQL: uma unica leitura (cache em memoria, invalidado por
        # escrita), em vez de COUNT + SELECT em conexoes separadas.
        dados, _ = listar_recomendacoes_cache(
            competencia
        )

        total = len(dados)

        if total == 0:

            raise HTTPException(
                status_code=404,
                detail=(
                    "Competência não encontrada"
                )
            )

        return {
            "competencia": competencia,
            "total_base": total,
            "total_filtrado": total,
            "recomendacoes": dados,
        }

    total = total_competencia(
        competencia
    )

    if total == 0:

        raise HTTPException(
            status_code=404,
            detail=(
                "Competência não encontrada"
            )
        )

    dados = listar_recomendacoes_db(
        competencia=competencia,
        q=q,
        provider=provider,
        bu=bu,
        squad=squad,
        categoria=categoria,
        analise=analise,
        ambiente=ambiente,
    )

    return {
        "competencia": competencia,
        "total_base": total,
        "total_filtrado": len(dados),
        "recomendacoes": dados,
    }


@app.post("/api/email/send")
def enviar_email(
    payload: dict
):

    return enviar_email_servico(
        payload
    )


@app.get(
    "/api/recomendacoes/{competencia}/origem-ids"
)
def obter_origem_ids(
    competencia: str
):
    # Indicadores "Novas recomendacoes" e "Tempo medio de tratamento" (frontend).
    origem = origem_ids_competencia(
        competencia
    )

    return {
        "competencia": competencia,
        "total": len(origem),
        "origem": origem,
    }


@app.get(
    "/api/recomendacoes/{competencia}/{opportunity_id}/historico"
)
def obter_historico_recomendacao(
    competencia: str,
    opportunity_id: str
):
    registro = buscar_recomendacao(
        competencia,
        opportunity_id
    )

    if registro is None:
        raise HTTPException(
            status_code=404,
            detail="Recomendação não encontrada"
        )

    historico = historico_recomendacao(
        competencia,
        opportunity_id
    )

    return {
        "competencia": competencia,
        "finOpsOpportunityId": opportunity_id,
        "total": len(historico),
        "historico": historico
    }


@app.middleware("http")
async def adicionar_charset_utf8_json(
    request,
    call_next
):
    response = await call_next(request)

    content_type = response.headers.get(
        "content-type",
        ""
    )

    if (
        content_type.startswith(
            "application/json"
        )
        and "charset=" not in content_type.lower()
    ):
        response.headers[
            "content-type"
        ] = (
            "application/json; "
            "charset=utf-8"
        )

    return response


@app.post(
    "/api/recomendacoes/{competencia}/importar"
)
def importar_recomendacoes(
    competencia: str,
    registros: list[dict]
):
    try:
        total = salvar_recomendacoes_lote(
            competencia,
            registros
        )

    except ValueError as erro:
        raise HTTPException(
            status_code=400,
            detail=str(erro)
        )

    return {
        "status": "ok",
        "competencia": competencia,
        "registros_processados": total,
        "total_banco":
            total_competencia(
                competencia
            )
    }


@app.get(
    "/favicon.ico",
    include_in_schema=False
)
def favicon():
    return Response(
        status_code=204
    )


@app.get("/api/custos/resumo")
def custos_resumo():
    # Aba Custos Cloud: arquivo, tipo e data de gravacao de cada export (sem o CSV).
    try:
        return {"records": resumo_cost_records()}
    except Exception as erro:
        raise HTTPException(
            status_code=500,
            detail="Falha ao listar custos: " + str(erro)
        )


@app.post("/api/custos/produto/linhas")
def custos_produto_linhas(payload: dict = Body(...)):
    # Linhas da base de produto de um mes so para os componentes pedidos (ex.: operacoes de disco).
    try:
        return {"rows": linhas_produto(
            payload.get("provider"), payload.get("year"), payload.get("month"), payload.get("termos"))}
    except Exception as erro:
        raise HTTPException(
            status_code=500,
            detail="Falha ao ler a base de produto: " + str(erro)
        )


@app.get("/api/custos/persistidos")
def custos_persistidos(request: Request):
    # V401: ETag barato (so chave + data de gravacao). Se nada mudou, responde
    # 304 sem ler os CSVs (dezenas de MB) do banco.
    try:
        etag = cost_records_etag()
    except Exception as erro:
        raise HTTPException(
            status_code=500,
            detail=(
                "Falha ao carregar custos DEV: "
                + str(erro)
            )
        )

    cabecalhos = {
        "ETag": etag,
        "Cache-Control": "no-cache",
    }

    recebidos = [
        x.strip()
        for x in (
            request.headers.get("if-none-match") or ""
        ).split(",")
    ]

    if etag in recebidos:
        return Response(
            status_code=304,
            headers=cabecalhos
        )

    try:
        gz = costs_payload_gzip(etag)

    except Exception as erro:
        raise HTTPException(
            status_code=500,
            detail=(
                "Falha ao carregar custos DEV: "
                + str(erro)
            )
        )

    aceita_gzip = "gzip" in (
        request.headers.get("accept-encoding") or ""
    ).lower()

    if aceita_gzip:
        return Response(
            content=gz,
            media_type="application/json",
            headers={
                **cabecalhos,
                "Content-Encoding": "gzip",
                "Vary": "Accept-Encoding",
            }
        )

    import gzip as _gzip_v402
    return Response(
        content=_gzip_v402.decompress(gz),
        media_type="application/json",
        headers=cabecalhos
    )


# FINOPS V214 - COST RECORDS API

@app.post("/api/custos/persistidos")
def salvar_custo_persistido(
    registro: dict
):
    try:
        salvo = salvar_cost_record(
            registro
        )

        total = contar_cost_records()

    except ValueError as erro:
        raise HTTPException(
            status_code=400,
            detail=str(erro)
        )

    except Exception as erro:
        raise HTTPException(
            status_code=500,
            detail=(
                "Falha ao persistir custo: "
                + str(erro)
            )
        )

    return {
        "status": "ok",
        "total": total,
        "costRecord": salvo,
    }


# FINOPS V196 - PERSISTENCIA TOTAL
import contextvars as _finops_contextvars_v404
import logging as _finops_logging_v404
import time as _finops_time_v404
import json as _finops_json_v196
from datetime import datetime as _finops_datetime_v196


def _finops_json_value_v196(v):

    if isinstance(v, (dict, list)):
        return _finops_json_v196.dumps(
            v,
            ensure_ascii=False,
            separators=(",", ":")
        )

    if isinstance(v, bool):
        return int(v)

    return v


def _finops_camel_v196(name):

    parts = str(name).split("_")

    if not parts:
        return name

    return (
        parts[0]
        + "".join(
            x[:1].upper() + x[1:]
            for x in parts[1:]
        )
    )


def _finops_row_value_v196(
    column,
    row,
    competencia
):

    aliases = {

        "competencia":
            competencia,

        "opportunity_id":
            (
                row.get("finOpsOpportunityId")
                or row.get("opportunity_id")
            ),

        "provider":
            row.get("provider"),

        "item":
            row.get("item"),

        "subscription":
            row.get("subscription"),

        "bu":
            row.get("bu"),

        "squad":
            row.get("squad"),

        "categoria":
            row.get("categoria"),

        "recomendado_por":
            padronizar_recomendado_por(row.get("recomendadoPor")),

        "analise":
            row.get("analise", ""),

        "realizado":
            int(
                bool(
                    row.get(
                        "realizado",
                        False
                    )
                )
            ),

        "ticket":
            row.get("ticket", ""),

        "data_prevista":
            row.get("dataPrevista", ""),

        "data_efetivada":
            row.get("dataEfetivada", ""),

        "data_recomendada":
            row.get("dataRecomendada", ""),

        "data_atualizacao":
            row.get("dataAtualizacao", ""),

        "observacao":
            row.get("observacao", ""),

        "responsavel":
            row.get("responsavel", ""),

        "responsavel_tecnico":
            row.get(
                "responsavelTecnico",
                ""
            ),

        "saving_est":
            row.get("savingEst"),

        "saving":
            row.get("saving"),

        "rescaldo_previsto":
            row.get("rescaldoPrevisto"),

        "payload_json":
            _finops_json_v196.dumps(
                row,
                ensure_ascii=False,
                separators=(",", ":")
            ),
    }

    if column in aliases:
        return aliases[column]

    if column in row:
        return _finops_json_value_v196(
            row[column]
        )

    camel = _finops_camel_v196(
        column
    )

    if camel in row:
        return _finops_json_value_v196(
            row[camel]
        )

    return None


_FINOPS_COLS_CONGELADAS_V320 = (
    "saving_est", "realizado", "saving",
    "saving_efetivo", "rescaldo_previsto"
)


def _finops_competencia_fechada_v320(con, competencia):
    try:
        r = con.execute(
            "SELECT 1 FROM competencias_fechadas "
            "WHERE competencia = ? AND fechada = 1",
            (competencia,)
        ).fetchone()
        return bool(r)
    except Exception:
        return False



def _finops_valor_igual_v404(a, b):
    if a is None or b is None:
        return a is None and b is None
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return float(a) == float(b)
    try:
        # Decimal (pymssql) e numericos em geral
        if not isinstance(a, str) and not isinstance(b, str):
            return float(a) == float(b)
    except (TypeError, ValueError):
        pass
    return str(a) == str(b)


def _finops_colunas_diferentes_v404(
    con,
    competencia,
    opportunity_id,
    novos
):
    """Colunas de `novos` cujo valor difere do que a linha guarda.
    Lista vazia = nada a gravar. Qualquer duvida -> ["?"] (grava)."""

    cols = list(novos)

    if not cols:
        return ["?"]

    try:
        ctx = _LOTE_CTX_V404.get()
        atual = (
            ctx["pre"].get(opportunity_id)
            if ctx is not None
            else None
        )

        if atual is None:
            atual = con.execute(
                "SELECT "
                + ", ".join(f'"{c}"' for c in cols)
                + " FROM recommendations"
                " WHERE competencia = ? AND opportunity_id = ?",
                (competencia, opportunity_id)
            ).fetchone()

        if atual is None:
            return ["?"]

        diff = [
            c for c in cols
            if not _finops_valor_igual_v404(atual[c], novos[c])
        ]

        return diff

    except Exception:
        return ["?"]


def _finops_linha_ja_igual_v404(
    con,
    competencia,
    opportunity_id,
    novos
):
    return not _finops_colunas_diferentes_v404(
        con,
        competencia,
        opportunity_id,
        novos
    )


_LOTE_CTX_V404 = _finops_contextvars_v404.ContextVar(
    "finops_lote_ctx_v404", default=None
)


def _finops_id_da_linha_v404(row):

    opportunity_id = str(
        row.get(
            "finOpsOpportunityId",
            ""
        )
        or row.get(
            "opportunity_id",
            ""
        )
    ).strip()

    if not opportunity_id:
        raise ValueError(
            "Recomendacao sem FinOpsOpportunityId"
        )

    return opportunity_id


def _finops_fechada_v404(con, competencia):
    ctx = _LOTE_CTX_V404.get()

    if ctx is None:
        return _finops_competencia_fechada_v320(
            con, competencia
        )

    if "fechada" not in ctx:
        ctx["fechada"] = _finops_competencia_fechada_v320(
            con, competencia
        )

    return ctx["fechada"]


def _finops_colunas_v404(con):
    ctx = _LOTE_CTX_V404.get()

    if ctx is None:
        return colunas_da_tabela(con, "recommendations")

    if "cols" not in ctx:
        ctx["cols"] = colunas_da_tabela(con, "recommendations")

    return ctx["cols"]


def _finops_montar_valores_v404(
    con,
    competencia,
    row,
    existing
):
    """Valores (coluna -> valor) que o upsert gravaria para esta linha."""

    opportunity_id = _finops_id_da_linha_v404(row)

    columns = _finops_colunas_v404(con)

    values = {}

    for col in columns:

        value = _finops_row_value_v196(
            col,
            row,
            competencia
        )

        if (
            col in {
                "competencia",
                "opportunity_id",
                "payload_json"
            }
            or value is not None
        ):
            values[col] = value

    values["competencia"] = competencia
    values["opportunity_id"] = opportunity_id

    fechada = _finops_fechada_v404(con, competencia)

    # V320: competencia fechada nao aceita mudanca financeira
    if fechada:
        if not existing:
            raise ValueError(
                "Competencia fechada: nao e possivel criar recomendacao"
            )
        for _c in _FINOPS_COLS_CONGELADAS_V320:
            values.pop(_c, None)

    # Status oficial (api/status.py): valores antigos viram os novos.
    # Em competencia fechada o realizado esta congelado: o status segue o que
    # esta gravado no banco, nao o que o navegador mandou.
    if "analise" in values:
        realizado = values.get("realizado")
        ticket = values.get("ticket")
        if fechada:
            atual = con.execute(
                "SELECT realizado, ticket FROM recommendations "
                "WHERE competencia = ? AND opportunity_id = ?",
                (competencia, opportunity_id)
            ).fetchone()
            if atual is not None:
                realizado = atual[0]
        values["analise"] = _status.normalizar(
            values.get("analise"),
            bool(realizado),
            ticket
        )

    return opportunity_id, values


_FINOPS_COLS_PROTEGIDAS_V404 = {
    "competencia",
    "opportunity_id",
}


def _finops_upsert_row_v196(
    con,
    competencia,
    row
):

    opportunity_id = _finops_id_da_linha_v404(row)

    ctx = _LOTE_CTX_V404.get()

    if ctx is not None and opportunity_id in ctx["pre"]:
        existing = True
    else:
        existing = con.execute(
            """
            SELECT 1
            FROM recommendations
            WHERE competencia = ?
              AND opportunity_id = ?
            """,
            (
                competencia,
                opportunity_id
            )
        ).fetchone()

    protected = _FINOPS_COLS_PROTEGIDAS_V404

    opportunity_id, values = _finops_montar_valores_v404(
        con,
        competencia,
        row,
        existing
    )

    if existing:

        updates = [
            col
            for col in values
            if col not in protected
        ]

        # V404: nao reescreve a linha (nem sobe a versao do cache) quando todas
        # as colunas ja guardam exatamente estes valores.
        if updates and _finops_linha_ja_igual_v404(
            con,
            competencia,
            opportunity_id,
            {col: values[col] for col in updates}
        ):
            updates = []

        if updates:

            sql = (
                "UPDATE recommendations SET "
                + ", ".join(
                    f'"{col}" = ?'
                    for col in updates
                )
                + " WHERE competencia = ? "
                  "AND opportunity_id = ?"
            )

            args = [
                values[col]
                for col in updates
            ]

            args.extend([
                competencia,
                opportunity_id
            ])

            con.execute(
                sql,
                args
            )

    else:

        insert_cols = list(
            values.keys()
        )

        sql = (
            "INSERT INTO recommendations ("
            + ", ".join(
                f'"{col}"'
                for col in insert_cols
            )
            + ") VALUES ("
            + ", ".join(
                "?"
                for _ in insert_cols
            )
            + ")"
        )

        con.execute(
            sql,
            [
                values[col]
                for col in insert_cols
            ]
        )

    return opportunity_id


@app.get("/api/app-state")
def finops_app_state_v196():

    with conectar() as con:

        rows = con.execute("""
            SELECT
                state_key,
                state_value
            FROM app_state
            ORDER BY state_key
        """).fetchall()

    items = {
        row["state_key"]:
            row["state_value"]
        for row in rows
    }

    return {
        "count": len(items),
        "items": items
    }


@app.post("/api/app-state/bulk")
async def finops_app_state_bulk_v196(
    request: Request
):

    payload = await request.json()

    items = (
        payload.get("items")
        if isinstance(payload, dict)
        else {}
    )

    if not isinstance(items, dict):
        raise HTTPException(
            status_code=400,
            detail="items deve ser um objeto"
        )

    now = (
        _finops_datetime_v196
        .now()
        .isoformat(
            timespec="seconds"
        )
    )

    with conectar() as con:

        for key, value in items.items():

            _finops_upsert_sql(
                con,
                "app_state",
                ["state_key"],
                {
                    "state_key": str(key),
                    "state_value": str(value),
                    "updated_at": now,
                }
            )

        con.commit()

    return {
        "ok": True,
        "saved": len(items)
    }


@app.post("/api/app-state/item")
async def finops_app_state_item_v196(
    request: Request
):

    payload = await request.json()

    key = str(
        payload.get("key", "")
    ).strip()

    if not key:
        raise HTTPException(
            status_code=400,
            detail="key obrigatoria"
        )

    value = str(
        payload.get("value", "")
    )

    now = (
        _finops_datetime_v196
        .now()
        .isoformat(
            timespec="seconds"
        )
    )

    with conectar() as con:

        _finops_upsert_sql(
            con,
            "app_state",
            ["state_key"],
            {
                "state_key": key,
                "state_value": value,
                "updated_at": now,
            }
        )

        con.commit()

    return {
        "ok": True,
        "key": key
    }


@app.post("/api/app-state/delete")
async def finops_app_state_delete_v196(
    request: Request
):

    payload = await request.json()

    key = str(
        payload.get("key", "")
    ).strip()

    if not key:
        raise HTTPException(
            status_code=400,
            detail="key obrigatoria"
        )

    with conectar() as con:

        con.execute(
            """
            DELETE FROM app_state
            WHERE state_key = ?
            """,
            (key,)
        )

        con.commit()

    return {
        "ok": True,
        "key": key
    }


# FINOPS - FULL STATE AUDIT
_FINOPS_AUDIT_FIELDS_V227 = (
    ("analise", "analise"),
    ("realizado", "realizado"),
    ("ticket", "ticket"),
    ("dataPrevista", "data_prevista"),
    ("dataEfetivada", "data_efetivada"),
    ("observacao", "observacao"),
    ("squad", "squad"),
    ("responsavel", "responsavel"),
    ("responsavelTecnico", "responsavel_tecnico"),
)


def _finops_audit_full_state_v227(
    con,
    competencia,
    opportunity_id,
    row,
    usuario=None,
):
    usuario = usuario or USUARIO_ATUAL.get()
    columns = ", ".join(
        db_field
        for _, db_field
        in _FINOPS_AUDIT_FIELDS_V227
    )

    current = con.execute(
        f"""
        SELECT {columns}
        FROM recommendations
        WHERE competencia = ?
          AND opportunity_id = ?
        """,
        (
            competencia,
            opportunity_id,
        )
    ).fetchone()

    if current is None:
        return 0

    changed = 0

    for index, (api_field, _) in enumerate(
        _FINOPS_AUDIT_FIELDS_V227
    ):
        if api_field not in row:
            continue

        old_value = current[index]
        new_value = row.get(api_field)

        if api_field == "realizado":
            new_value = (
                1
                if bool(new_value)
                else 0
            )

        if old_value == new_value:
            continue

        con.execute(
            """
            INSERT INTO recommendation_audit (
                competencia,
                opportunity_id,
                campo,
                valor_anterior,
                valor_novo,
                usuario
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                competencia,
                opportunity_id,
                api_field,
                (
                    None
                    if old_value is None
                    else str(old_value)
                ),
                (
                    None
                    if new_value is None
                    else str(new_value)
                ),
                usuario,
            )
        )

        changed += 1

    return changed


def _finops_gravar_estado_completo_v403(
    con,
    competencia,
    opportunity_id,
    row
):
    """Grava auditoria + upsert + calc_method de UMA recomendacao na
    conexao/transacao recebida (quem chama faz BEGIN e commit)."""

    # V404: dentro de um lote o estado atual ja foi lido de uma vez; linha que
    # nao muda nada nao faz nenhuma outra consulta (nem auditoria nem upsert).
    ctx = _LOTE_CTX_V404.get()

    if ctx is not None and opportunity_id in ctx["pre"]:

        try:
            _, valores = _finops_montar_valores_v404(
                con, competencia, row, True
            )

            novos = {
                c: v for c, v in valores.items()
                if c not in _FINOPS_COLS_PROTEGIDAS_V404
            }

            calc = str(
                row.get("calcMethodV18") or ""
            ).strip()

            if calc:
                novos["calc_method"] = calc

            if novos and not _finops_colunas_diferentes_v404(
                con,
                competencia,
                opportunity_id,
                novos
            ):
                return 0

        except Exception:
            pass  # qualquer duvida: caminho completo

        ctx["pre"].pop(opportunity_id, None)

    if ctx is not None:
        ctx["gravadas"] = ctx.get("gravadas", 0) + 1

    audit_changes = (
        _finops_audit_full_state_v227(
            con,
            competencia,
            opportunity_id,
            row
        )
    )

    _finops_upsert_row_v196(
        con,
        competencia,
        row
    )

    # FINOPS V299B - PERSIST CALC METHOD
    calc_method_v299b = str(
        row.get("calcMethodV18")
        or ""
    ).strip()

    if calc_method_v299b and not _finops_linha_ja_igual_v404(
        con,
        competencia,
        opportunity_id,
        {"calc_method": calc_method_v299b}
    ):
        con.execute(
            """
            UPDATE recommendations
            SET calc_method = ?
            WHERE competencia = ?
              AND opportunity_id = ?
            """,
            (
                calc_method_v299b,
                competencia,
                opportunity_id,
            )
        )

    return audit_changes


def _finops_pre_carregar_v404(con, competencia, ids):
    """Estado atual (coluna -> valor) das linhas existentes, por opportunity_id.
    Em caso de qualquer falha devolve o que conseguiu; o resto cai no caminho
    normal (consulta por linha)."""

    pre = {}

    try:
        cols = _finops_colunas_v404(con)

        if not cols:
            return pre

        unicos = list(dict.fromkeys(ids))

        for i in range(0, len(unicos), 400):

            bloco = unicos[i:i + 400]

            linhas = con.execute(
                "SELECT "
                + ", ".join(f'"{c}"' for c in cols)
                + " FROM recommendations WHERE competencia = ?"
                + " AND opportunity_id IN ("
                + ", ".join("?" for _ in bloco)
                + ")",
                [competencia] + bloco
            ).fetchall()

            for linha in linhas:
                pre[linha["opportunity_id"]] = {
                    c: linha[c] for c in cols
                }

    except Exception:
        return {}

    return pre


def _finops_gravar_lote_v403(competencia, rows):

    results = []

    inicio = _finops_time_v404.perf_counter()
    gravadas = 0

    with conectar() as con:

        con.execute(
            "BEGIN IMMEDIATE"
        )

        # V404: le o estado atual de TODAS as linhas do lote de uma vez
        # (dentro da transacao) em vez de consultar linha por linha.
        _ctx_lote = {"pre": {}}
        token_ctx = _LOTE_CTX_V404.set(_ctx_lote)

        _ctx_lote["pre"] = _finops_pre_carregar_v404(
            con,
            competencia,
            [i for i, _ in rows]
        )

        try:

            for opportunity_id, row in rows:

                audit_changes = (
                    _finops_gravar_estado_completo_v403(
                        con,
                        competencia,
                        opportunity_id,
                        row
                    )
                )

                results.append({
                    "finOpsOpportunityId":
                        opportunity_id,
                    "ok": True,
                    "auditChanges":
                        audit_changes
                })

        finally:
            gravadas = _ctx_lote.get("gravadas", 0)
            _LOTE_CTX_V404.reset(token_ctx)

        con.commit()

    _finops_logging_v404.getLogger("uvicorn.error").info(
        "[lote] %s: %d recebidas, %d gravadas, %.2fs",
        competencia,
        len(rows),
        gravadas,
        _finops_time_v404.perf_counter() - inicio
    )

    return results


@app.post(
    "/api/recomendacoes/"
    "{competencia}/"
    "estado-completo-lote"
)
async def finops_estado_completo_lote_v403(
    competencia: str,
    request: Request
):
    """Grava varias recomendacoes numa unica transacao.

    Corpo: {"itens": [{"finOpsOpportunityId": "...", "recomendacao": {...}}]}
    Tudo ou nada: se uma falhar, nenhuma e gravada."""

    payload = await request.json()

    itens = (
        payload.get("itens")
        if isinstance(payload, dict)
        else None
    )

    if not isinstance(itens, list):
        raise HTTPException(
            status_code=400,
            detail="itens deve ser uma lista"
        )

    rows = []

    for item in itens:

        row = (
            item.get("recomendacao")
            if isinstance(item, dict)
            else None
        )

        opportunity_id = (
            str(item.get("finOpsOpportunityId") or "").strip()
            if isinstance(item, dict)
            else ""
        )

        if not isinstance(row, dict) or not opportunity_id:
            raise HTTPException(
                status_code=400,
                detail="item invalido no lote"
            )

        row = dict(row)
        row["finOpsOpportunityId"] = opportunity_id
        rows.append((opportunity_id, row))

    try:

        from starlette.concurrency import run_in_threadpool

        results = await run_in_threadpool(
            _finops_gravar_lote_v403,
            competencia,
            rows
        )

    except HTTPException:
        raise

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc)
        )

    return {
        "ok": True,
        "competencia": competencia,
        "saved": len(results),
        "results": results
    }


# FINOPS V295B - MONTHLY PENDING RECONCILIATION API

def _finops_is_pending_v295(row):

    # Pendente = ainda precisa de acao (ver api/status.py): rascunho,
    # identificada, validacao tecnica, adiada, planejada ou em implementacao.
    return _status.pendente(
        row.get("analise"),
        bool(row.get("realizado")),
        row.get("ticket")
    )


def _finops_next_competencia_v295(
    competencia
):

    parts = str(
        competencia or ""
    ).split("-")

    if len(parts) != 2:
        raise ValueError(
            "Competencia invalida."
        )

    year = int(
        parts[0]
    )

    month = int(
        parts[1]
    )

    if month < 1 or month > 12:
        raise ValueError(
            "Mes invalido."
        )

    if month == 12:
        return (
            f"{year + 1}-01"
        )

    return (
        f"{year}-"
        f"{month + 1:02d}"
    )


def _finops_listar_v404(competencia):
    """Listagem completa de uma competencia: pelo cache em memoria no Azure SQL
    (invalidado a cada escrita), direto do banco no SQLite."""

    if USE_AZURE_SQL:
        return listar_recomendacoes_cache(competencia)[0]

    return listar_recomendacoes_db(competencia)


def _finops_carry_row_v295(
    source,
    origem,
    destino
):

    row = dict(
        source
    )

    opportunity_id = str(
        row.get(
            "finOpsOpportunityId"
        )
        or ""
    ).strip()

    if not opportunity_id:
        raise ValueError(
            "Pendencia sem FinOpsOpportunityId."
        )

    status = _status.normalizar(
        row.get("analise"),
        bool(row.get("realizado")),
        row.get("ticket")
    )

    row[
        "finOpsOpportunityId"
    ] = opportunity_id

    row[
        "competencia"
    ] = destino

    row[
        "dataRecomendada"
    ] = (
        destino
        + "-01"
    )

    row[
        "dataAtualizacao"
    ] = ""

    row[
        "realizado"
    ] = False

    row[
        "ticket"
    ] = ""

    row[
        "dataEfetivada"
    ] = ""

    # Saving informado/estimado permanece.
    # Saving realizado do novo mes inicia zerado.
    row[
        "saving"
    ] = 0

    row[
        "savingEfetivo"
    ] = 0

    row[
        "rescaldoPrevisto"
    ] = 0

    row[
        "rescaldoHerdado"
    ] = 0

    row[
        "rescaldoNote"
    ] = ""

    row[
        "rescaldoHerdadoNote"
    ] = ""

    row[
        "calcNote"
    ] = (
        "Pendencia carregada automaticamente "
        f"de {origem} para {destino}. "
        "Execucao ainda nao confirmada."
    )

    row[
        "calcMethodV18"
    ] = (
        "carried_pending_previous_month"
    )

    if status == _status.VALIDACAO:
        row[
            "observacao"
        ] = ""

    row[
        "_carryFrom"
    ] = origem

    row[
        "_ticketCycleResponded"
    ] = False

    return row


@app.post(
    "/api/recomendacoes/"
    "{competencia_origem}/"
    "reconciliar-pendencias/"
    "{competencia_destino}"
)
def finops_reconciliar_pendencias_v295(
    competencia_origem: str,
    competencia_destino: str,
):

    try:

        esperado = (
            _finops_next_competencia_v295(
                competencia_origem
            )
        )

    except Exception as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )

    if competencia_destino != esperado:

        raise HTTPException(
            status_code=400,
            detail=(
                "Competencia destino deve ser "
                "o mes imediatamente seguinte."
            )
        )

    # Setembro fechado continua imutavel.
    if competencia_destino < "2026-10":

        return {
            "ok": True,
            "skipped": True,
            "motivo":
                "Competencia historica protegida.",
            "added": 0,
            "removed": 0,
        }

    origem_rows = (
        _finops_listar_v404(
            competencia_origem
        )
        or []
    )

    destino_rows = (
        _finops_listar_v404(
            competencia_destino
        )
        or []
    )

    pending = {
        str(
            row.get(
                "finOpsOpportunityId"
            )
            or ""
        ).strip():
            row

        for row in origem_rows

        if (
            _finops_is_pending_v295(
                row
            )
            and
            str(
                row.get(
                    "finOpsOpportunityId"
                )
                or ""
            ).strip()
        )
    }

    destino_by_id = {
        str(
            row.get(
                "finOpsOpportunityId"
            )
            or ""
        ).strip():
            row

        for row in destino_rows

        if str(
            row.get(
                "finOpsOpportunityId"
            )
            or ""
        ).strip()
    }

    additions = []

    for opportunity_id, source in pending.items():

        if opportunity_id in destino_by_id:
            continue

        additions.append(
            _finops_carry_row_v295(
                source,
                competencia_origem,
                competencia_destino
            )
        )

    # Remove somente carry antigo que deixou de ser
    # pendencia no mes anterior e ainda nao foi
    # realizado no mes atual.
    removals = []

    for opportunity_id, target in destino_by_id.items():

        carry_from = str(
            target.get(
                "_carryFrom"
            )
            or ""
        ).strip()

        if carry_from != competencia_origem:
            continue

        if opportunity_id in pending:
            continue

        if bool(
            target.get(
                "realizado"
            )
        ):
            continue

        removals.append(
            opportunity_id
        )

    if not additions and not removals:

        return {
            "ok": True,
            "competenciaOrigem":
                competencia_origem,
            "competenciaDestino":
                competencia_destino,
            "pending":
                len(pending),
            "added": 0,
            "removed": 0,
            "totalDestino":
                len(destino_rows),
        }

    try:

        with conectar() as con:

            con.execute(
                "BEGIN IMMEDIATE"
            )

            for row in additions:

                _finops_upsert_row_v196(
                    con,
                    competencia_destino,
                    row
                )

            if removals:

                con.executemany(
                    """
                    DELETE FROM recommendations
                    WHERE competencia = ?
                      AND opportunity_id = ?
                    """,
                    [
                        (
                            competencia_destino,
                            opportunity_id
                        )
                        for opportunity_id
                        in removals
                    ]
                )

            con.commit()

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc)
        )

    total_destino = len(
        listar_recomendacoes_db(
            competencia_destino
        )
        or []
    )

    return {
        "ok": True,
        "competenciaOrigem":
            competencia_origem,
        "competenciaDestino":
            competencia_destino,
        "pending":
            len(pending),
        "added":
            len(additions),
        "removed":
            len(removals),
        "addedIds": [
            row.get(
                "finOpsOpportunityId"
            )
            for row in additions
        ],
        "removedIds":
            removals,
        "totalDestino":
            total_destino,
    }



@app.post(
    "/api/recomendacoes/"
    "{competencia}/substituir"
)
async def finops_substituir_competencia_v196(
    competencia: str,
    request: Request
):

    payload = await request.json()

    rows = (
        payload.get("recomendacoes")
        if isinstance(payload, dict)
        else None
    )

    if not isinstance(rows, list):
        raise HTTPException(
            status_code=400,
            detail="recomendacoes deve ser uma lista"
        )

    incoming_ids = set()

    clean_rows = []

    for row in rows:

        if not isinstance(row, dict):
            continue

        opportunity_id = str(
            row.get(
                "finOpsOpportunityId",
                ""
            )
        ).strip()

        if not opportunity_id:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Existe recomendacao "
                    "sem FinOpsOpportunityId"
                )
            )

        if opportunity_id in incoming_ids:
            raise HTTPException(
                status_code=400,
                detail=(
                    "FinOpsOpportunityId "
                    f"duplicado: {opportunity_id}"
                )
            )

        incoming_ids.add(
            opportunity_id
        )

        clean_rows.append(
            dict(row)
        )

    try:

        with conectar() as con:

            con.execute(
                "BEGIN IMMEDIATE"
            )

            current = con.execute(
                """
                SELECT opportunity_id
                FROM recommendations
                WHERE competencia = ?
                """,
                (competencia,)
            ).fetchall()

            current_ids = {
                row["opportunity_id"]
                for row in current
            }

            for row in clean_rows:

                _finops_upsert_row_v196(
                    con,
                    competencia,
                    row
                )

            removed_ids = (
                current_ids
                - incoming_ids
            )

            if removed_ids:

                con.executemany(
                    """
                    DELETE FROM recommendations
                    WHERE competencia = ?
                      AND opportunity_id = ?
                    """,
                    [
                        (
                            competencia,
                            opportunity_id
                        )
                        for opportunity_id
                        in removed_ids
                    ]
                )

            con.commit()

    except HTTPException:
        raise

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc)
        )

    return {
        "ok": True,
        "competencia": competencia,
        "total": len(clean_rows),
        "removed": len(
            current_ids
            - incoming_ids
        )
    }


# FIM FINOPS V196

