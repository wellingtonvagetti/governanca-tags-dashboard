# FINOPS V214 - COST RECORDS SQLITE

import gzip
import json
import logging
import threading
import time
from datetime import datetime, timezone
from api.db import conectar
from api.sqldb import upsert as _upsert_sql


# FINOPS V232 - COST MULTI SOURCE

def _normalize_cost_source_type(
    value
):
    source_type = str(
        value
        or "ID_HISTORY"
    ).strip().upper()

    aliases = {
        "ID": "ID_HISTORY",
        "HISTORY": "ID_HISTORY",
        "ID+HISTORY": "ID_HISTORY",
        "ID_HISTORY": "ID_HISTORY",
        "PRODUCT": "PRODUCT",
        "PRODUCTS": "PRODUCT",
    }

    source_type = aliases.get(
        source_type,
        source_type
    )

    if source_type not in {
        "ID_HISTORY",
        "PRODUCT",
    }:
        raise ValueError(
            "sourceType invalido"
        )

    return source_type


def _normalize_cost_record(
    record
):
    if not isinstance(
        record,
        dict
    ):
        raise ValueError(
            "costRecord deve ser um objeto"
        )

    provider = str(
        record.get("provider")
        or ""
    ).strip().upper()

    if not provider:
        raise ValueError(
            "provider obrigatorio"
        )

    try:
        year = int(
            record.get("year")
        )

        month = int(
            record.get("month")
        )

    except Exception:
        raise ValueError(
            "year/month invalidos"
        )

    if year < 2000 or year > 2100:
        raise ValueError(
            "year invalido"
        )

    if month < 1 or month > 12:
        raise ValueError(
            "month invalido"
        )

    source_type = (
        _normalize_cost_source_type(
            record.get("sourceType")
            or record.get("source_type")
            or "ID_HISTORY"
        )
    )

    content_text = str(
        record.get("text")
        or ""
    )

    if not content_text:
        raise ValueError(
            "text obrigatorio"
        )

    file_name = str(
        record.get("fileName")
        or ""
    ).strip()

    saved_at = str(
        record.get("savedAt")
        or ""
    ).strip()

    if not saved_at:
        saved_at = (
            datetime.now(
                timezone.utc
            )
            .isoformat()
            .replace(
                "+00:00",
                "Z"
            )
        )

    if source_type == "ID_HISTORY":
        record_key = (
            f"{provider}|"
            f"{year:04d}-"
            f"{month:02d}"
        )
    else:
        record_key = (
            f"{provider}|"
            f"{source_type}|"
            f"{year:04d}-"
            f"{month:02d}"
        )

    return {
        "key": record_key,
        "provider": provider,
        "year": year,
        "month": month,
        "sourceType": source_type,
        "fileName": file_name,
        "text": content_text,
        "savedAt": saved_at,
    }


def _upsert_cost_record(
    con,
    record
):
    r = _normalize_cost_record(
        record
    )

    _upsert_sql(
        con,
        "cost_records",
        ["provider", "year", "month", "source_type"],
        {
            "record_key": r["key"],
            "provider": r["provider"],
            "year": r["year"],
            "month": r["month"],
            "source_type": r["sourceType"],
            "file_name": r["fileName"],
            "content_text": r["text"],
            "saved_at": r["savedAt"],
        },
        ["record_key", "file_name", "content_text", "saved_at"]
    )

    return r


def salvar_cost_record(
    record
):

    with conectar() as con:

        result = _upsert_cost_record(
            con,
            record
        )

        con.commit()

    return result


def carregar_cost_records():

    with conectar() as con:

        rows = con.execute("""
            SELECT
                record_key,
                provider,
                year,
                month,
                source_type,
                file_name,
                content_text,
                saved_at
            FROM cost_records
            ORDER BY
                year,
                month,
                provider,
                source_type
        """).fetchall()

    return [
        {
            "key":
                row["record_key"],

            "provider":
                row["provider"],

            "year":
                int(
                    row["year"]
                ),

            "month":
                int(
                    row["month"]
                ),

            "sourceType":
                row["source_type"]
                or "ID_HISTORY",

            "fileName":
                row["file_name"],

            "text":
                row["content_text"],

            "savedAt":
                row["saved_at"],
        }
        for row in rows
    ]


# FINOPS V401 - ETAG E CONTAGEM LEVES (sem ler content_text)

def cost_records_etag():
    """Assinatura barata do estado de cost_records (so chave e data de gravacao).

    Permite responder 304 em /api/custos/persistidos sem ler os CSVs.
    """
    import hashlib
    with conectar() as con:
        rows = con.execute("""
            SELECT record_key, saved_at
            FROM cost_records
            ORDER BY record_key
        """).fetchall()
    h = hashlib.sha1()
    for r in rows:
        h.update(("%s|%s;" % (r[0], r[1])).encode("utf-8"))
    return 'W/"%d-%s"' % (len(rows), h.hexdigest()[:20])


def resumo_cost_records():
    """Lista os exports salvos sem o conteudo (aba Custos Cloud)."""
    with conectar() as con:
        rows = con.execute("""
            SELECT provider, year, month, source_type, file_name, saved_at
            FROM cost_records
            ORDER BY year, month, provider, source_type
        """).fetchall()
    return [
        {
            "provider": r[0],
            "year": int(r[1]),
            "month": int(r[2]),
            "sourceType": r[3],
            "fileName": r[4],
            "savedAt": r[5],
        }
        for r in rows
    ]


def contar_cost_records():
    with conectar() as con:
        return int(con.execute("SELECT COUNT(*) FROM cost_records").fetchone()[0])


# FINOPS V402 - PAYLOAD GZIP EM MEMORIA (constroi uma vez por ETag)

_COSTS_GZ_LOCK = threading.Lock()
_COSTS_GZ_CACHE = {"etag": None, "gz": None}
_log_custos = logging.getLogger("uvicorn.error")


def costs_payload_gzip(etag):
    """JSON de custos ja comprimido (gzip), construido uma unica vez por ETag.

    Ler dezenas de MB do banco, serializar e comprimir custa dezenas de
    segundos num plano pequeno. Requisicoes simultaneas esperam a mesma
    construcao (lock) em vez de repetir o trabalho; depois so devolve bytes.
    """
    with _COSTS_GZ_LOCK:
        if _COSTS_GZ_CACHE["etag"] == etag and _COSTS_GZ_CACHE["gz"] is not None:
            return _COSTS_GZ_CACHE["gz"]

        t0 = time.perf_counter()
        records = carregar_cost_records()
        t1 = time.perf_counter()
        body = json.dumps(
            {"status": "ok", "total": len(records), "costRecords": records},
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        t2 = time.perf_counter()
        gz = gzip.compress(body, compresslevel=5)
        t3 = time.perf_counter()

        _COSTS_GZ_CACHE["etag"] = etag
        _COSTS_GZ_CACHE["gz"] = gz
        _log_custos.info(
            "[custos-cache] %d registros | leitura %.1fs | json %.1fs | gzip %.1fs | %.1f MB -> %.1f MB",
            len(records), t1 - t0, t2 - t1, t3 - t2,
            len(body) / 1048576.0, len(gz) / 1048576.0,
        )
        return gz


def _numero_produto(valor):
    texto = str(valor or "").strip().replace(" ", "").replace(" ", "")
    if not texto:
        return 0.0
    if "," in texto:
        texto = texto.replace(".", "").replace(",", ".")
    try:
        return float(texto)
    except ValueError:
        return 0.0


def linhas_produto(provider, year, month, termos):
    """Linhas da base de produto (PRODUCT) cujo Component contem algum dos termos.

    Leve: evita baixar todos os exports so para explicar um item (ex.: operacoes de disco).
    """
    import csv
    import io

    termos = [str(t or "").strip().lower() for t in (termos or []) if str(t or "").strip()]
    if not termos:
        return []
    with conectar() as con:
        row = con.execute(
            "SELECT content_text FROM cost_records "
            "WHERE provider = ? AND year = ? AND month = ? AND source_type = 'PRODUCT'",
            (str(provider or "").upper(), int(year), int(month)),
        ).fetchone()
    if not row or not row[0]:
        return []
    texto = row[0]
    primeira = texto.split("\n", 1)[0]
    delim = max([",", ";", "\t"], key=primeira.count)
    saida = []
    for r in csv.DictReader(io.StringIO(texto), delimiter=delim):
        chave = {str(k or "").strip().lower(): v for k, v in r.items()}
        componente = str(chave.get("component") or "")
        baixo = componente.lower()
        if not any(t in baixo for t in termos):
            continue
        saida.append({
            "product": chave.get("product") or "",
            "sku": chave.get("sku/type") or chave.get("sku") or "",
            "component": componente.strip(),
            "details": chave.get("details") or "",
            "cost": _numero_produto(chave.get("cost")),
            "avgCostDay": _numero_produto(chave.get("avg cost/day")),
            "usage": _numero_produto(chave.get("usage")),
            "unit": chave.get("unit") or "",
        })
    return saida
