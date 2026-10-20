"""Modulo Governanca de Tags (porte do server.js do dashboard de tags): regras e arquivos.
As rotas HTTP ficam em api/modulo_tags_rotas.py.

Front-end em modulos/tags/ (mantido pelo time de governanca de tags).
Os dados ficam fora do repositorio, em FINOPS_TAGS_DATA_DIR:
  baseline.json.gz            fotografia padrao (antes da 1a gravacao)
  historico.json.gz           base historica usada pela aba de evolucao
  subscriptions-master.json   cadastro corporativo de subscriptions (padrao)
  <id>.json.gz/.meta.json     fotografias gravadas pela tela
  latest.txt                  fotografia exibida para todos
  governance-config.json      mapa oficial, acoes e subscriptions
"""

import copy
import gzip
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

from api.db import USUARIO_ATUAL

BASE_DIR = Path(__file__).resolve().parent.parent
MODULO_DIR = BASE_DIR / "modulos" / "tags"
ASSETS_DIR = MODULO_DIR / "assets"

MAX_BODY = 30 * 1024 * 1024
ID_RE = re.compile(r"^[a-zA-Z0-9._-]+$")
DATA_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SUB_ID_RE = re.compile(r"^[0-9a-f-]{36}$")
TAGS_RESUMO = ["AMBIENTE", "BU", "CAPEX", "CC", "CCOWNER", "CLIENTE", "PRODUTO", "FOLIO"]

# A primeira fotografia pode ser importada antes dos históricos de saneamento.
# A tela exige estas quatro coleções, portanto as normalizamos para listas vazias.
HISTORICO_VAZIO = {"prod": [], "w1": [], "w2": [], "w3": []}

# Fotografia vazia: a tela abre (sem numeros) ate a 1a carga de dados.
SNAPSHOT_VAZIO = {
    "meta": {"date": "", "fullFile": "", "scopeFile": "", "eligibilityApplied": True},
    "nScopeRows": 0, "subs": [], "rgs": [], "dict": {},
    "R": {"id": [], "s": [], "g": [], "sc": []},
}

def diretorio_dados():
    explicito = os.getenv("FINOPS_TAGS_DATA_DIR")
    if explicito:
        return Path(explicito)
    if os.getenv("WEBSITE_SITE_NAME"):
        return Path("/home/data/modulos/tags")
    return BASE_DIR / "data" / "modulos" / "tags"


class ErroTags(Exception):
    def __init__(self, status, mensagem):
        super().__init__(mensagem)
        self.status = status
        self.mensagem = mensagem


def _erro(status, mensagem):
    return ErroTags(status, mensagem)


def _ler_json_gz(arquivo):
    return json.loads(gzip.decompress(arquivo.read_bytes()).decode("utf-8"))


def _gravar_atomico(arquivo, conteudo):
    if isinstance(conteudo, str):
        conteudo = conteudo.encode("utf-8")
    temp = arquivo.with_name(f"{arquivo.name}.{os.getpid()}.{datetime.now().timestamp()}.tmp")
    temp.write_bytes(conteudo)
    os.replace(temp, arquivo)


def _usuario():
    return (USUARIO_ATUAL.get() or "usuário autenticado")[:200]


def baseline(pasta):
    arquivo = pasta / "baseline.json.gz"
    try:
        return _ler_json_gz(arquivo)
    except FileNotFoundError:
        return copy.deepcopy(SNAPSHOT_VAZIO)


def normalizar_elegibilidade(snapshot):
    # Corrige fotografias 2.4 gravadas por uma versao antiga do front-end que
    # marcou todo o inventario como escopo (mesma regra do server.js).
    r = (snapshot or {}).get("R") or {}
    total = len(r["id"]) if isinstance(r.get("id"), list) else 0
    if (not total or (snapshot.get("meta") or {}).get("eligibilityApplied") is not False
            or not isinstance(r.get("CLASSE_INVENTARIO"), list)):
        return snapshot
    classes = ((snapshot.get("dict") or {}).get("CLASSE_INVENTARIO")) or []
    if "ELEGIVEL_OPERACIONAL" not in classes:
        return snapshot
    elegivel = classes.index("ELEGIVEL_OPERACIONAL")
    manter = [i for i in range(total) if r["CLASSE_INVENTARIO"][i] == elegivel]
    if not manter or len(manter) == total:
        return snapshot
    norm = copy.deepcopy(snapshot)
    for chave, valores in norm["R"].items():
        if isinstance(valores, list) and len(valores) == total:
            norm["R"][chave] = [valores[i] for i in manter]
    norm["nScopeRows"] = len(manter)
    norm["meta"] = {**norm.get("meta", {}), "eligibilityApplied": True,
                    "eligibilityRecoveredFromInventoryClass": True}
    usadas = set(norm["R"].get("s") or [])
    for indice, sub in enumerate(norm.get("subs") or []):
        sub["inScope"] = indice in usadas
    return norm


def resumir(snapshot):
    r = snapshot.get("R") or {}
    dic = snapshot.get("dict") or {}
    s = r.get("s") or []
    sc = r.get("sc") or []
    indices = range(len(s))
    escopos = {
        "governance": [i for i in indices if i < len(sc) and sc[i] == 1],
        "complete": list(indices),
        "outside": [i for i in indices if not (i < len(sc) and sc[i] == 1)],
    }

    def valor(tag, i):
        col = r.get(tag)
        x = col[i] if isinstance(col, list) and i < len(col) else None
        if x is None or x < 0:
            return None
        nomes = dic.get(tag) or []
        return nomes[x] if x < len(nomes) else None

    def um(ids):
        tags = {}
        for nome in TAGS_RESUMO:
            valores = [valor(nome, i) for i in ids]
            preenchidas = sum(v is not None for v in valores)
            if nome in ("CLIENTE", "PRODUTO"):
                classificadas = sum(v is not None and v != "INDEFINIDO" for v in valores)
            else:
                classificadas = preenchidas
            tags[nome] = {"filled": preenchidas, "classified": classificadas, "total": len(ids)}
        g = r.get("g") or []
        return {
            "resources": len(ids),
            "subscriptions": len({s[i] for i in ids}),
            "resourceGroups": len({g[i] for i in ids if i < len(g)}),
            "tags": tags,
        }

    return {nome: um(ids) for nome, ids in escopos.items()}


def listar_fotografias(pasta, base):
    pasta.mkdir(parents=True, exist_ok=True)
    gravadas = []
    for arquivo in pasta.glob("*.meta.json"):
        try:
            gravadas.append(json.loads(arquivo.read_text("utf-8")))
        except Exception:
            continue
    gravadas.sort(key=lambda m: str(m.get("savedAt")), reverse=True)
    meta = base.get("meta") or {}
    gravadas.append({
        "id": "baseline", "date": meta.get("date") or None, "savedAt": None,
        "savedBy": "Deploy inicial", "fullFile": meta.get("fullFile") or "",
        "scopeFile": meta.get("scopeFile") or "", "baseline": True, "summary": resumir(base),
    })
    return gravadas


def fotografia_atual(pasta, base):
    try:
        ident = (pasta / "latest.txt").read_text("utf-8").strip()
        if not ID_RE.match(ident):
            return base
        return normalizar_elegibilidade(_ler_json_gz(pasta / f"{ident}.json.gz"))
    except FileNotFoundError:
        return base
    except Exception as exc:
        print(f"[tags] falha ao ler fotografia: {exc}")
        return base


def gravar_fotografia(pasta, snapshot):
    meta = (snapshot or {}).get("meta") or {}
    r = (snapshot or {}).get("R") or {}
    if not meta or not isinstance(r.get("id"), list) or not meta.get("date"):
        raise _erro(400, "Fotografia inválida ou sem Data de Coleta")
    if not DATA_RE.match(str(meta["date"])):
        raise _erro(400, "Data de Coleta inválida")
    if isinstance(r.get("CLASSE_INVENTARIO"), list) and meta.get("eligibilityApplied") is not True:
        raise _erro(400, "A fotografia contém inventário classificado, mas a elegibilidade não foi "
                         "aplicada. Atualize a página e importe novamente.")
    pasta.mkdir(parents=True, exist_ok=True)
    salvo_em = datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    ident = f"{meta['date']}--{re.sub(r'[:.]', '-', salvo_em)}"
    metadados = {
        "id": ident, "date": meta["date"], "savedAt": salvo_em, "savedBy": _usuario(),
        "fullFile": str(meta.get("fullFile") or "")[:240], "scopeFile": str(meta.get("scopeFile") or "")[:240],
        "baseline": False, "summary": resumir(snapshot),
    }
    _gravar_atomico(pasta / f"{ident}.json.gz", gzip.compress(json.dumps(snapshot).encode("utf-8"), 9))
    _gravar_atomico(pasta / f"{ident}.meta.json", json.dumps(metadados, ensure_ascii=False, indent=2))
    _gravar_atomico(pasta / "latest.txt", ident)
    return metadados


def excluir_fotografia(pasta, ident):
    if ident == "baseline":
        raise _erro(400, "O baseline do deploy não pode ser excluído")
    if not ID_RE.match(ident):
        raise _erro(400, "Identificador de fotografia inválido")
    meta, dados = pasta / f"{ident}.meta.json", pasta / f"{ident}.json.gz"
    if not meta.exists() or not dados.exists():
        raise _erro(404, "Fotografia não encontrada")
    meta.unlink()
    dados.unlink()
    try:
        atual = (pasta / "latest.txt").read_text("utf-8").strip()
    except FileNotFoundError:
        atual = None
    if atual == ident:
        restantes = [m for m in listar_fotografias(pasta, baseline(pasta)) if not m.get("baseline")]
        if restantes:
            _gravar_atomico(pasta / "latest.txt", restantes[0]["id"])
        else:
            (pasta / "latest.txt").unlink(missing_ok=True)


def _subscriptions_padrao(pasta):
    """Lê o cadastro corporativo persistido e, no primeiro acesso, o cadastro do deploy."""
    for arquivo in (pasta / "subscriptions-master.json", BASE_DIR / "subscriptions-master.json"):
        try:
            dados = json.loads(arquivo.read_text("utf-8"))
            if isinstance(dados, list):
                return dados
        except (FileNotFoundError, OSError, json.JSONDecodeError):
            continue
    return []


def ler_configuracao(pasta):
    try:
        config = json.loads((pasta / "governance-config.json").read_text("utf-8"))
    except FileNotFoundError:
        return {"officialMap": [], "actions": [], "subscriptions": _subscriptions_padrao(pasta)}
    if not isinstance(config.get("subscriptions"), list) or not config["subscriptions"]:
        config["subscriptions"] = _subscriptions_padrao(pasta)
    return config


def _txt(valor, limite=None):
    texto = str(valor if valor is not None else "").strip()
    return texto[:limite] if limite else texto


def _num(valor):
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        return 0
    if numero != numero or numero in (float("inf"), float("-inf")):
        return 0
    return int(numero) if numero.is_integer() else numero


def gravar_configuracao(pasta, config):
    config = config if isinstance(config, dict) else {}
    lista = lambda chave, limite: config.get(chave)[:limite] if isinstance(config.get(chave), list) else []
    usuario = _usuario()
    mapa = [{"CC": _txt(x.get("CC")), "BU": _txt(x.get("BU")), "CCOWNER": _txt(x.get("CCOWNER"))}
            for x in lista("officialMap", 5000) if isinstance(x, dict)]
    acoes = [{
        "id": _txt(x.get("id")), "date": _txt(x.get("date")), "action": _txt(x.get("action"), 160),
        "scope": _txt(x.get("scope"), 160), "processed": _num(x.get("processed")),
        "success": _num(x.get("success")), "failure": _num(x.get("failure")),
        "responsible": _txt(x.get("responsible"), 160), "evidence": _txt(x.get("evidence"), 500),
        "savedBy": _txt(x.get("savedBy") or usuario, 200),
    } for x in lista("actions", 1000) if isinstance(x, dict)]
    subs = [{
        "name": _txt(x.get("name"), 240), "id": _txt(x.get("id"), 80).lower(),
        "managementGroup": _txt(x.get("managementGroup"), 240), "status": _txt(x.get("status"), 40),
        "inScope": x.get("inScope") is True,
    } for x in lista("subscriptions", 500) if isinstance(x, dict)]
    limpo = {
        "officialMap": [x for x in mapa if x["CC"] and x["BU"]],
        "actions": [x for x in acoes if DATA_RE.match(x["date"]) and x["action"]],
        "subscriptions": [x for x in subs if x["name"] and SUB_ID_RE.match(x["id"])],
        "updatedAt": datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
        "updatedBy": usuario,
    }
    pasta.mkdir(parents=True, exist_ok=True)
    _gravar_atomico(pasta / "governance-config.json", json.dumps(limpo, ensure_ascii=False, indent=2))
    return limpo


def _json_seguro(valor):
    return json.dumps(valor, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")


def _historico_para_tela(pasta):
    """Garante o contrato do front-end mesmo sem histórico inicial no App Service."""
    try:
        bruto = _ler_json_gz(pasta / "historico.json.gz")
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        bruto = {}
    if not isinstance(bruto, dict):
        bruto = {}
    return {
        chave: list(bruto.get(chave) or []) if isinstance(bruto.get(chave), list) else []
        for chave in HISTORICO_VAZIO
    }


def pagina(pasta):
    html = (MODULO_DIR / "index.html").read_text("utf-8")
    base = baseline(pasta)
    historico = _historico_para_tela(pasta)
    html = html.replace("__TAGS_SNAPSHOT__", _json_seguro(fotografia_atual(pasta, base)), 1)
    return html.replace("__TAGS_HISTORICO__", _json_seguro(historico), 1)


def pagina_auditoria_vms(pasta):
    """Reutiliza a fotografia e os assets de Tags, abrindo somente a auditoria de VMs.

    A base permanece unica em data/modulos/tags. A separacao e de modulo/rota
    e evita duplicar CSVs, historicos ou configuracoes corporativas.
    """
    return pagina(pasta).replace(
        '<body class="v2-loading">',
        '<body class="v2-loading" data-module="auditoria-vms">',
        1,
    )
