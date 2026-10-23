from pathlib import Path
import contextvars
import sqlite3
import json
import os
import unicodedata

import threading
import time

from api.sqldb import USE_AZURE_SQL, conectar_azure, upsert, versao_competencia, versao_recomendacoes


BASE_DIR = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

DEFAULT_DB_PATH = (
    BASE_DIR
    / "database"
    / "finops_dev.db"
)

DB_PATH = Path(
    os.getenv(
        "FINOPS_DB_PATH",
        str(DEFAULT_DB_PATH),
    )
).expanduser().resolve()

SCHEMA_PATH = BASE_DIR / "database" / "schema.sql"

# Arquivos SQLite em que o schema.sql ja foi aplicado neste processo.
_ESQUEMA_APLICADO = set()
_ESQUEMA_LOCK = threading.Lock()

USUARIO_ATUAL = contextvars.ContextVar("usuario_atual", default="dev-local")


CAMPO_DB_PARA_API = {
    "opportunity_id": "finOpsOpportunityId",
    "recommendation": "recommendation",
    "item": "item",
    "ambiente": "ambiente",
    "rg": "rg",
    "subscription": "subscription",
    "bu": "bu",
    "categoria": "categoria",
    "fonte": "fonte",
    "recomendado_por": "recomendadoPor",
    "data_recomendada": "dataRecomendada",
    "data_atualizacao": "dataAtualizacao",
    "saving_est": "savingEst",
    "realizado": "realizado",
    "ticket": "ticket",
    "data_prevista": "dataPrevista",
    "data_efetivada": "dataEfetivada",
    "saving": "saving",
    "saving_efetivo": "savingEfetivo",
    "rescaldo_previsto": "rescaldoPrevisto",
    "analise": "analise",
    "observacao": "observacao",
    "squad": "squad",
    "responsavel": "responsavel",
    "responsavel_tecnico": "responsavelTecnico",
    "provider": "provider",
    "calc_note": "calcNote",
    "calc_method": "calcMethodV18",
}


def conectar():
    # Azure SQL (opcional): so quando FINOPS_SQL_SERVER esta definido.
    if USE_AZURE_SQL:
        return conectar_azure()

    # Em ambiente novo (ex.: App Service recem-criado) a pasta do banco pode
    # nao existir; o SQLite nao a cria sozinho.
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    conexao = sqlite3.connect(
        str(DB_PATH),
        timeout=30,
    )

    conexao.row_factory = sqlite3.Row

    conexao.execute(
        "PRAGMA busy_timeout=10000"
    )

    # Banco novo ou antigo: o schema.sql (so CREATE ... IF NOT EXISTS) cria o
    # que faltar. Uma vez por arquivo, na primeira conexao do processo.
    with _ESQUEMA_LOCK:
        if DB_PATH not in _ESQUEMA_APLICADO:
            conexao.executescript(
                SCHEMA_PATH.read_text(encoding="utf-8-sig")
            )
            _ESQUEMA_APLICADO.add(DB_PATH)

    return conexao


# Padrao do campo "Identificado por" (coluna recomendado_por), a partir de Outubro/2026:
# Evertec, Solo, Dedalus e Evertec Latam. Qualquer LATAM (sozinho ou junto de
# Evertec, Dedalus ou Solo) vira Evertec Latam.
RECOMENDADO_POR_PADRAO = ("Evertec", "Solo", "Dedalus", "Evertec Latam")


def padronizar_recomendado_por(valor):
    texto = str(valor or "").strip()
    if not texto:
        return valor
    chave = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().upper()
    if "LATAM" in chave:
        return "Evertec Latam"
    if "DEDALUS" in chave:
        return "Dedalus"
    if "SOLO" in chave:
        return "Solo"
    if "EVERTEC" in chave:
        return "Evertec"
    return texto


# Catalogo oficial Classificacao -> Categoria (coluna recommendation -> categoria).
# Categorias guardadas pelo codigo; o nome de exibicao fica em CATEGORIA_NOME.
CATEGORIA_NOME = {
    "ARCHITECTURE": "Architectural Optimization",
    "COMMITMENT": "Commitment Optimization",
    "ELASTICITY": "Elasticity",
    "RIGHTSIZING": "Rightsizing",
    "DATA_OPTIMIZATION": "Storage & Data Optimization",
    "WASTE": "Waste Elimination",
    "OFFBOARDING": "Customer Offboarding",
}

_CATALOGO_POR_CATEGORIA = {
    "ARCHITECTURE": (
        "Using superseded volume types",
        "Using superseded instance types",
        "Using old instance types",
        "Services with billed public IP addresses",
        "Instances with billed public IP addresses",
        "Instances supported for switching to Ampere (ARM) type",
        "Instances supported for switching to AMD type",
        "Databases with extended support coming soon",
        "Compute Optimizer recommendations for Fargate services",
        "Compute Optimizer recommendations for switching to Graviton",
        "Kubernetes Clusters with extended support",
        "Recommendations to migrate public IPv4 addresses to IPv6",
    ),
    "COMMITMENT": (
        "Recommendations to purchase a savings plan",
        "Recommendations to buy Virtual Machine reserved instances",
        "Recommendations to buy Storage Account reserved instances",
        "Recommendations to buy PostgreSQL Flexible Server reserved instances",
        "Recommendations to buy MySQL reserved instances",
        "Recommendations to buy Managed Disk reserved instances",
        "Recommendations to buy Cosmos DB reserved instances",
        "Recommendations to buy Cache for Redis reserved instances",
        "Recommendations to buy Azure SQL Database reserved instances",
        "Recommendations to buy Azure Microsoft Fabric reserved instances",
        "Recommendations to buy Azure Files reserved instances",
        "Recommendations to buy App Service reserved instances",
        "Considering refund reserved instances",
    ),
    "ELASTICITY": (
        "Virtual machine scale sets (including Kubernetes) with overprovisioning disabled",
        "Recommendations to shutdown underutilized VM instances",
        "Instances with low CPU usage that can be stopped on weekends",
    ),
    "RIGHTSIZING": (
        "Recommendations to right-size underutilized Virtual Machines",
        "Recommendations to right-size underutilized databases",
        "Recommendations to right-size underutilized App Service plans",
        "Provisioned IOPS",
        "Low number of connections for databases",
    ),
    "DATA_OPTIMIZATION": (
        "Recommendations to change storage tier",
        "Recommendations to change storage redundance for non production storages",
        "Recommendations for migrating to premium Storage Accounts",
        "Buckets / Storage Accounts with long retention for soft delete",
        "Azure Snapshots with Premium Storage",
        "Change Managed Disk storage tier",
    ),
    "WASTE": (
        "Volumes on stopped instances",
        "Recommendations for unused/empty App Service plans",
        "Virtual Machines stopped but not deallocated",
        "Public IP Addresses without association",
        "Old Snapshots",
        "Low number of connections for cache clusters",
        "Instances with low network traffic",
        "Instances stopped for a long time",
        "Detached volumes",
        "Cache Clusters without keys",
        "Cache clusters with no read/write operations",
        "Orphaned Managed Disks",
        "Orphaned SQL elastic pools",
        "Azure SQL Databases with no activity",
        "Orphaned Load Balancers",
    ),
    # remocao dos recursos de clientes com distrato (contrato encerrado)
    "OFFBOARDING": (
        "Decommission resources of terminated customers",
    ),
}


def _chave_classificacao(valor):
    texto = unicodedata.normalize("NFKD", str(valor or "")).encode("ascii", "ignore").decode().lower()
    return " ".join("".join(c if c.isalnum() else " " for c in texto).split())


CATALOGO_CLASSIFICACAO = {
    _chave_classificacao(classificacao): categoria
    for categoria, lista in _CATALOGO_POR_CATEGORIA.items()
    for classificacao in lista
}


def categoria_do_catalogo(classificacao, atual=None):
    """Categoria do catalogo para a Classificacao; fora do catalogo mantem a atual."""
    return CATALOGO_CLASSIFICACAO.get(_chave_classificacao(classificacao), atual)


def row_para_registro(row):
    registro = {}

    payload = row["payload_json"]

    if payload:
        try:
            registro = json.loads(payload)
        except json.JSONDecodeError:
            registro = {}

    for campo_db, campo_api in CAMPO_DB_PARA_API.items():
        valor = row[campo_db]

        if campo_api == "realizado":
            valor = bool(valor)

        registro[campo_api] = valor

    registro["recomendadoPor"] = padronizar_recomendado_por(registro.get("recomendadoPor"))

    return registro


def contar_por_competencia():
    with conectar() as conexao:
        linhas = conexao.execute(
            """
            SELECT competencia, COUNT(*) AS total
            FROM recommendations
            GROUP BY competencia
            ORDER BY competencia
            """
        ).fetchall()

    return {
        linha["competencia"]: linha["total"]
        for linha in linhas
    }


def total_competencia(competencia):
    with conectar() as conexao:
        linha = conexao.execute(
            """
            SELECT COUNT(*) AS total
            FROM recommendations
            WHERE competencia = ?
            """,
            (competencia,)
        ).fetchone()

    return linha["total"]


def listar_recomendacoes_db(
    competencia,
    q=None,
    provider=None,
    bu=None,
    squad=None,
    categoria=None,
    analise=None,
    ambiente=None,
):
    sql = """
        SELECT *
        FROM recommendations
        WHERE competencia = ?
    """

    parametros = [competencia]

    filtros = {
        "provider": provider,
        "bu": bu,
        "squad": squad,
        "categoria": categoria,
        "analise": analise,
        "ambiente": ambiente,
    }

    for coluna, valor in filtros.items():
        if valor:
            sql += f" AND LOWER({coluna}) = LOWER(?)"
            parametros.append(valor)

    if q:
        busca = f"%{q}%"

        sql += """
        AND (
            opportunity_id LIKE ?
            OR item LIKE ?
            OR rg LIKE ?
            OR subscription LIKE ?
            OR responsavel LIKE ?
            OR responsavel_tecnico LIKE ?
        )
        """

        parametros.extend([busca] * 6)

    sql += """
        ORDER BY saving_est DESC, opportunity_id ASC
    """

    with conectar() as conexao:
        linhas = conexao.execute(
            sql,
            parametros
        ).fetchall()

    return [
        row_para_registro(linha)
        for linha in linhas
    ]


# Cache em memoria da listagem completa de uma competencia (so Azure SQL).
# A leitura do Azure SQL Basic e lenta (~2 s por competencia); como o app roda
# com 1 worker e toda escrita em recommendations passa por AzConnection, a
# versao (versao_recomendacoes) invalida o cache a cada commit: com versao
# diferente a leitura e SEMPRE refeita na hora, nunca se serve dado velho.
#
# O TTL cobre so alteracoes feitas fora do app (migracao, SQL manual) e funciona
# como "revalida em segundo plano": passado o TTL, a requisicao ainda recebe o
# que esta em memoria (rapido) e uma releitura atualiza o cache para a proxima.
# Assim ninguem paga a leitura fria depois de um intervalo sem uso.
_RECS_CACHE = {}
_RECS_CACHE_LOCK = threading.Lock()
_RECS_RELENDO = set()
RECS_CACHE_TTL_S = float(os.getenv("FINOPS_RECS_CACHE_TTL_S", "300"))


def _recs_reler(competencia, versao):
    try:
        dados = listar_recomendacoes_db(competencia=competencia)

        with _RECS_CACHE_LOCK:
            _RECS_CACHE[competencia] = (versao, time.monotonic(), dados)
    except Exception:
        pass  # mantem o que ja esta em memoria; a proxima tentativa refaz
    finally:
        with _RECS_CACHE_LOCK:
            _RECS_RELENDO.discard(competencia)


def listar_recomendacoes_cache(competencia):
    """Devolve (registros, veio_do_cache). Sem filtros; so faz sentido no Azure SQL."""
    agora = time.monotonic()
    versao = versao_competencia(competencia)  # lida ANTES da consulta

    with _RECS_CACHE_LOCK:
        item = _RECS_CACHE.get(competencia)

        if item and item[0] == versao:
            vencido = agora - item[1] >= RECS_CACHE_TTL_S

            if vencido and competencia not in _RECS_RELENDO:
                _RECS_RELENDO.add(competencia)
                threading.Thread(
                    target=_recs_reler,
                    args=(competencia, versao),
                    daemon=True,
                ).start()

            return item[2], True

    dados = listar_recomendacoes_db(competencia=competencia)

    with _RECS_CACHE_LOCK:
        _RECS_CACHE[competencia] = (versao, time.monotonic(), dados)

    return dados, False


def atualizar_cache_linhas(competencia, ids, versao_antes):
    """Depois de gravar um lote, troca no cache so as linhas gravadas em vez de reler a competencia inteira.

    So vale se a unica escrita desde `versao_antes` foi este lote (versao subiu exatamente 1) e o cache estava
    nessa versao; em qualquer outro caso nao faz nada e a proxima leitura rele tudo (comportamento antigo).
    """
    ids = [str(i) for i in ids if str(i).strip()]
    depois = versao_competencia(competencia)
    if not ids or len(ids) > 50 or depois != (versao_antes[0], versao_antes[1] + 1):
        return False
    with _RECS_CACHE_LOCK:
        item = _RECS_CACHE.get(competencia)
    if not item or item[0] != versao_antes:
        return False
    novos = {}
    for oid in ids:
        reg = buscar_recomendacao(competencia, oid)
        if reg is None:
            return False
        novos[oid] = reg
    atuais = {str(r.get("finOpsOpportunityId")): r for r in item[2]}
    if any(oid not in atuais for oid in novos):
        return False  # linha nova: rele tudo
    lista = [novos.get(str(r.get("finOpsOpportunityId")), r) for r in item[2]]
    lista.sort(key=lambda r: (-float(r.get("savingEst") or 0), str(r.get("finOpsOpportunityId") or "")))
    with _RECS_CACHE_LOCK:
        atual = _RECS_CACHE.get(competencia)
        if atual is not item or versao_competencia(competencia) != depois:
            return False
        _RECS_CACHE[competencia] = (depois, item[1], lista)
    return True


def buscar_recomendacao(
    competencia,
    opportunity_id
):
    with conectar() as conexao:
        linha = conexao.execute(
            """
            SELECT *
            FROM recommendations
            WHERE competencia = ?
              AND opportunity_id = ?
            """,
            (
                competencia,
                opportunity_id,
            )
        ).fetchone()

    if linha is None:
        return None

    return row_para_registro(linha)


def historico_recomendacao(
    competencia,
    opportunity_id
):
    with conectar() as conexao:
        linhas = conexao.execute(
            """
            SELECT
                id,
                campo,
                valor_anterior,
                valor_novo,
                usuario,
                alterado_em
            FROM recommendation_audit
            WHERE competencia = ?
              AND opportunity_id = ?
            ORDER BY id DESC
            """,
            (
                competencia,
                opportunity_id,
            )
        ).fetchall()

    return [
        dict(linha)
        for linha in linhas
    ]


def origem_ids_competencia(competencia):
    """Para cada ID da competencia: a 1a competencia em que apareceu e a menor data_recomendada
    ate esta competencia. Base de "Novas recomendacoes" e do tempo medio de tratamento: itens
    herdados podem ter a data_recomendada trocada para o mes atual na consolidacao."""
    with conectar() as conexao:
        linhas = conexao.execute(
            """
            SELECT
                opportunity_id,
                MIN(competencia) AS primeira_competencia,
                MIN(data_recomendada) AS primeira_data
            FROM recommendations
            WHERE competencia <= ?
              AND opportunity_id IN (
                  SELECT opportunity_id
                  FROM recommendations
                  WHERE competencia = ?
              )
            GROUP BY opportunity_id
            """,
            (competencia, competencia)
        ).fetchall()

    return {
        linha["opportunity_id"]: {
            "primeiraCompetencia": linha["primeira_competencia"],
            "primeiraData": linha["primeira_data"] or "",
        }
        for linha in linhas
    }


def salvar_recomendacoes_lote(
    competencia,
    registros
):
    # Colunas atualizadas quando a recomendacao ja existe (as financeiras
    # realizado/saving/saving_efetivo/rescaldo_previsto NAO sao sobrescritas).
    atualizar = [
        "recommendation",
        "item",
        "ambiente",
        "rg",
        "subscription",
        "bu",
        "categoria",
        "fonte",
        "recomendado_por",
        "data_recomendada",
        "data_atualizacao",
        "saving_est",
        "ticket",
        "data_prevista",
        "data_efetivada",
        "analise",
        "observacao",
        "squad",
        "responsavel",
        "responsavel_tecnico",
        "provider",
        "calc_note",
        "calc_method",
        "payload_json",
    ]

    with conectar() as conexao:

        for item in registros:

            opportunity_id = str(
                item.get("finOpsOpportunityId")
                or ""
            ).strip()

            if not opportunity_id:
                raise ValueError(
                    "Recomendação sem FinOpsOpportunityId"
                )

            if item.get("recomendadoPor"):
                item = dict(item, recomendadoPor=padronizar_recomendado_por(item.get("recomendadoPor")))

            # Categoria editada na tela (categoriaManual) vence o catalogo.
            categoria = item.get("categoria") if item.get("categoriaManual") else \
                categoria_do_catalogo(item.get("recommendation"), item.get("categoria"))
            if categoria != item.get("categoria"):
                item = dict(item, categoria=categoria)

            payload_json = json.dumps(
                item,
                ensure_ascii=False
            )

            dados = {
                "competencia": competencia,
                "opportunity_id": opportunity_id,
                "recommendation": item.get("recommendation"),
                "item": item.get("item"),
                "ambiente": item.get("ambiente"),
                "rg": item.get("rg"),
                "subscription": item.get("subscription"),
                "bu": item.get("bu"),
                "categoria": item.get("categoria"),
                "fonte": item.get("fonte"),
                "recomendado_por": item.get("recomendadoPor"),
                "data_recomendada": item.get("dataRecomendada"),
                "data_atualizacao": item.get("dataAtualizacao"),
                "saving_est": float(
                    item.get("savingEst")
                    or 0
                ),
                "realizado": (
                    1
                    if item.get("realizado")
                    else 0
                ),
                "ticket": item.get("ticket"),
                "data_prevista": item.get("dataPrevista"),
                "data_efetivada": item.get("dataEfetivada"),
                "saving": float(
                    item.get("saving")
                    or 0
                ),
                "saving_efetivo": float(
                    item.get("savingEfetivo")
                    or 0
                ),
                "rescaldo_previsto": float(
                    item.get("rescaldoPrevisto")
                    or 0
                ),
                "analise": item.get("analise"),
                "observacao": item.get("observacao"),
                "squad": item.get("squad"),
                "responsavel": item.get("responsavel"),
                "responsavel_tecnico": item.get(
                    "responsavelTecnico"
                ),
                "provider": item.get("provider"),
                "calc_note": item.get("calcNote"),
                "calc_method": item.get("calcMethodV18"),
                "payload_json": payload_json,
            }

            upsert(
                conexao,
                "recommendations",
                ["competencia", "opportunity_id"],
                dados,
                atualizar,
            )

        conexao.commit()

    return len(registros)
