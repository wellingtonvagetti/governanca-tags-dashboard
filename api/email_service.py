"""Envio de e-mail/alertas via Logic App por HTTP.

Variaveis de ambiente:
  LOGIC_APP_URL                          URL do gatilho HTTP do fluxo. Sem ela, nada e enviado (status "simulado").
  FINOPS_EMAIL_OVERRIDE_TO               se definido, TODO envio vai so para este endereco.
  FINOPS_EMAIL_TIMEOUT                   segundos (padrao 30).
No local, essas variaveis podem ficar no arquivo .env da raiz do projeto (fora do git); o ambiente tem prioridade.
"""
import html as _html
import json
import os
import re
import urllib.error
import urllib.request

from fastapi import HTTPException


def _carregar_env_local():
    """Le o .env da raiz do projeto (so no local; no Azure as variaveis vem das configuracoes do app)."""
    caminho = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    if not os.path.isfile(caminho):
        return
    with open(caminho, encoding="utf-8-sig") as f:
        for linha in f:
            linha = linha.strip()
            if not linha or linha.startswith("#") or "=" not in linha:
                continue
            chave, valor = linha.split("=", 1)
            chave, valor = chave.strip(), valor.strip().strip('"').strip("'")
            if chave and valor and not os.getenv(chave):
                os.environ[chave] = valor


_carregar_env_local()


def config_publica():
    """O que a tela precisa saber: se ha Logic App e para onde vai tudo no modo de teste (sem a URL)."""
    return {
        "logicApp": bool(_url()),
        "redirecionaPara": (os.getenv("FINOPS_EMAIL_OVERRIDE_TO") or "").strip(),
    }


def _url():
    return (os.getenv("LOGIC_APP_URL") or "").strip()


def _tipo(payload):
    return payload.get("tipo") or payload.get("acao") or payload.get("action") or "nao_informado"


def _t(v):
    return _html.escape(str(v if v is not None else "").strip())


_RX_REC = re.compile(r"^\d+\.\s*(?:\[([^\]]+)\]\s*)?(.*?)\s*(?:\|\s*(.*?))?\s*\u2014\s*(R\$\s*[-\d.,]+)\s*$")
_MESES = ["janeiro", "fevereiro", "mar&ccedil;o", "abril", "maio", "junho", "julho",
          "agosto", "setembro", "outubro", "novembro", "dezembro"]
LIMITE_PRIORIDADE = 1000.0
MAX_ITENS_CORPO = 40
# Politica de recomendacoes FinOps: dias corridos a partir da abertura (plano de execucao, execucao)
PRAZOS_POLITICA = {"CRITICA": (3, 5), "ALTA": (5, 10), "MEDIA": (10, 30), "BAIXA": (30, 60)}
ORDEM_PRIORIDADE = ("CRITICA", "ALTA", "MEDIA", "BAIXA")
ROTULO_PRIORIDADE = {"CRITICA": "Cr&iacute;tica", "ALTA": "Alta", "MEDIA": "M&eacute;dia", "BAIXA": "Baixa"}


def _chave_pri(pri):
    import unicodedata
    return unicodedata.normalize("NFKD", str(pri or "")).encode("ascii", "ignore").decode().upper().strip()


def _data_br(txt):
    from datetime import datetime
    try:
        return datetime.strptime(str(txt or "").strip()[:10], "%d/%m/%Y")
    except ValueError:
        return None


def _prazos(pri, abertura):
    """(plano ate, execucao ate) em dd/mm/aaaa pela prioridade, ou ("", "")."""
    from datetime import timedelta
    dias = PRAZOS_POLITICA.get(_chave_pri(pri))
    if not dias or not abertura:
        return "", ""
    return tuple((abertura + timedelta(days=d)).strftime("%d/%m/%Y") for d in dias)


def _valor(txt):
    try:
        return float(re.sub(r"[^\d,\-]", "", txt).replace(",", "."))
    except ValueError:
        return 0.0


def _brl(v):
    return "R$ " + f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _itens(payload):
    """Todos os itens pendentes da lista enviada pelo dash: (valor, prioridade, recomendacao, item, valor_txt)."""
    bruto = re.sub(r"<[^>]+>", "", str(payload.get("recomendacoes") or ""))
    itens = []
    for l in (x.strip() for x in bruto.splitlines() if x.strip()):
        m = _RX_REC.match(l)
        if m:
            pri, rec, item, val = m.groups()
            itens.append((_valor(val), pri or "", rec, item or "", val))
    return itens


def _itens_prioritarios(payload):
    """Itens pendentes acima de R$ 1.000, do maior para o menor."""
    return sorted((x for x in _itens(payload) if x[0] > LIMITE_PRIORIDADE), key=lambda x: -x[0])


def montar_corpo_html(payload: dict) -> str:
    """Corpo do e-mail de aviso/cobranca (HTML simples, compativel com Outlook)."""
    abertura = str(payload.get("tipoEnvio") or "").upper().startswith("AVISO")
    squad = _t(payload.get("squad"))
    chamado = _t(payload.get("chamado"))
    prazo = _t(payload.get("prazo"))
    fase = _t(payload.get("fase") or payload.get("acao"))
    pend = _t(payload.get("pendentes"))
    pot = _t(payload.get("potencialPendente"))
    conc = payload.get("concluidas")
    total = payload.get("total")

    from datetime import datetime
    hoje = datetime.now()
    mes = f"{_MESES[hoje.month - 1]} de {hoje.year}"
    # prazos da politica contam da abertura do chamado (sem data informada: o dia do envio)
    data_abertura = _data_br(payload.get("dataAbertura")) or datetime(hoje.year, hoje.month, hoje.day)
    lim = "R$ 1.000"
    todos = _itens(payload)
    prior = _itens_prioritarios(payload)
    no_chamado = f", acompanhadas no chamado <b>{chamado}</b>" if chamado else ""
    anexo = (f"Abaixo est&atilde;o o resumo por prioridade e as recomenda&ccedil;&otilde;es acima de {lim}, para "
             "prioriza&ccedil;&atilde;o. O detalhamento completo est&aacute; na planilha em anexo."
             if prior else
             "Abaixo est&aacute; o resumo por prioridade. O detalhamento completo est&aacute; na planilha em anexo.")
    if abertura:
        titulo = "Recomenda&ccedil;&otilde;es de FinOps &mdash; abertura do ciclo"
        intro = ("Ol&aacute;, pessoal.<br>Segue a planilha com as recomenda&ccedil;&otilde;es de FinOps de "
                 f"<b>{mes}</b> da <b>{squad}</b>{no_chamado}.<br><br>{anexo}")
        pedido = ("Pedimos que avaliem as recomenda&ccedil;&otilde;es"
                  + (f" e registrem o andamento no chamado <b>{chamado}</b>" if chamado else "")
                  + ", respeitando os prazos de plano de execu&ccedil;&atilde;o e de execu&ccedil;&atilde;o de cada "
                  "prioridade, conforme a pol&iacute;tica de recomenda&ccedil;&otilde;es FinOps.")
    else:
        titulo = f"Acompanhamento FinOps &mdash; {fase}" if fase else "Acompanhamento FinOps"
        intro = ("Ol&aacute;, pessoal.<br>Este &eacute; um acompanhamento das recomenda&ccedil;&otilde;es de FinOps de "
                 f"<b>{mes}</b> da <b>{squad}</b>{no_chamado}: ainda constam pend&ecirc;ncias.<br><br>{anexo}")
        pedido = ("Pedimos que informem o andamento"
                  + (f" no chamado <b>{chamado}</b>" if chamado else "")
                  + " ou a justificativa das recomenda&ccedil;&otilde;es que n&atilde;o ser&atilde;o executadas, "
                  "conforme os prazos da pol&iacute;tica de recomenda&ccedil;&otilde;es FinOps.")

    msg_prior = _t(payload.get("mensagemPrioridade"))

    def kpi(rotulo, valor, sub=""):
        return ("<td style=\"padding:8px 12px;border:1px solid #e3e6ea;background:#f7f8fa;text-align:center;white-space:nowrap\">"
                f"<div style=\"font-size:11px;color:#667085\">{rotulo}</div>"
                f"<div style=\"font-size:16px;font-weight:700;color:#101828\">{valor}</div>"
                + (f"<div style=\"font-size:11px;color:#667085\">{sub}</div>" if sub else "") + "</td>")

    kpis = kpi("Pend&ecirc;ncias", pend) + kpi("Potencial&nbsp;estimado", pot)
    # na abertura nada foi tratado ainda: Concluidas so entra nas cobrancas
    if conc is not None and total is not None and not abertura:
        kpis += kpi("Conclu&iacute;das", f"{_t(conc)} / {_t(total)}")
    if prazo and not abertura:
        kpis += kpi("Prazo", prazo)
    if prior:
        kpis += kpi(f"Acima de {lim}", str(len(prior)), _brl(sum(x[0] for x in prior)).replace(" ", "&nbsp;"))

    td = "padding:6px 8px;border-bottom:1px solid #eaecf0;font-size:12px;vertical-align:top"
    cab = "padding:6px 8px;background:#f2f4f7;font-size:11px;color:#667085;text-align:left"

    # resumo por prioridade (sempre): quantidade, saving e prazos da politica
    grupos = {}
    for v, pri, *_ in todos:
        k = _chave_pri(pri)
        n, soma = grupos.get(k, (0, 0.0))
        grupos[k] = (n + 1, soma + v)
    linhas_res = ""
    for k in ORDEM_PRIORIDADE:
        if k not in grupos:
            continue
        n, soma = grupos[k]
        plano, execucao = _prazos(k, data_abertura)
        linhas_res += (
            f"<tr><td style=\"{td};white-space:nowrap\"><b>{ROTULO_PRIORIDADE[k]}</b></td>"
            f"<td style=\"{td};text-align:center\">{n}</td>"
            f"<td style=\"{td};text-align:right;white-space:nowrap\">{_brl(soma).replace(' ', '&nbsp;')}</td>"
            f"<td style=\"{td};text-align:center;white-space:nowrap\">{plano or '&ndash;'}</td>"
            f"<td style=\"{td};text-align:center;white-space:nowrap\">{execucao or '&ndash;'}</td></tr>")
    resumo = ""
    if linhas_res:
        resumo = ("<p style=\"margin:18px 0 6px;font-weight:700\">Resumo por prioridade</p>"
                  "<table width=\"100%\" cellspacing=\"0\" cellpadding=\"0\" style=\"border-collapse:collapse\">"
                  f"<tr><th style=\"{cab}\">Prioridade</th><th style=\"{cab};text-align:center\">Recomenda&ccedil;&otilde;es</th>"
                  f"<th style=\"{cab};text-align:right\">Saving estimado</th>"
                  f"<th style=\"{cab};text-align:center\">Plano at&eacute;</th>"
                  f"<th style=\"{cab};text-align:center\">Execu&ccedil;&atilde;o at&eacute;</th></tr>{linhas_res}</table>")

    # recomendacoes acima de R$ 1.000: so quando existem
    itens = ""
    if prior:
        linhas_html = ""
        for v, pri, rec, item, val in prior[:MAX_ITENS_CORPO]:
            plano, execucao = _prazos(pri, data_abertura)
            linhas_html += (
                f"<tr><td style=\"{td};white-space:nowrap\">{_t(pri)}</td>"
                f"<td style=\"{td}\"><b>{_t(item)}</b><br><span style=\"color:#667085\">{_t(rec)}</span></td>"
                f"<td style=\"{td};text-align:right;white-space:nowrap\">{_t(val).replace(' ', '&nbsp;')}</td>"
                f"<td style=\"{td};text-align:center;white-space:nowrap\">{plano or '&ndash;'}</td>"
                f"<td style=\"{td};text-align:center;white-space:nowrap\">{execucao or '&ndash;'}</td></tr>")
        itens = (f"<p style=\"margin:18px 0 6px;font-weight:700\">Recomenda&ccedil;&otilde;es acima de {lim}</p>"
                 "<table width=\"100%\" cellspacing=\"0\" cellpadding=\"0\" style=\"border-collapse:collapse\">"
                 f"<tr><th style=\"{cab}\">Prioridade</th><th style=\"{cab}\">Item / recomenda&ccedil;&atilde;o</th>"
                 f"<th style=\"{cab};text-align:right\">Saving estimado</th>"
                 f"<th style=\"{cab};text-align:center\">Plano at&eacute;</th>"
                 f"<th style=\"{cab};text-align:center\">Execu&ccedil;&atilde;o at&eacute;</th></tr>{linhas_html}</table>")
        if len(prior) > MAX_ITENS_CORPO:
            itens += (f"<p style=\"font-size:12px;color:#667085;margin:8px 0 0\">"
                      f"... e mais {len(prior) - MAX_ITENS_CORPO} item(ns) acima de {lim}. Lista completa na planilha anexa.</p>")

    return (
        "<div style=\"font-family:Segoe UI,Arial,sans-serif;max-width:640px;color:#101828\">"
        f"<div style=\"background:#e8590c;color:#fff;padding:14px 18px;font-size:16px;font-weight:700\">{titulo}</div>"
        "<div style=\"padding:18px;border:1px solid #e3e6ea;border-top:0\">"
        f"<p style=\"margin:0 0 14px\">{intro}</p>"
        f"<table cellspacing=\"6\" cellpadding=\"0\" style=\"border-collapse:separate\"><tr>{kpis}</tr></table>"
        + (f"<p style=\"margin:14px 0 0;color:#b54708\"><b>{msg_prior}</b></p>" if msg_prior else "")
        + resumo
        + itens
        + f"<p style=\"margin:18px 0 0\">{pedido}</p>"
        "<p style=\"margin:18px 0 0;font-size:11px;color:#98a2b3\">Mensagem autom&aacute;tica do Dashboard FinOps.</p>"
        "</div></div>"
    )


def enviar_email(payload: dict):
    url = _url()
    if not url:
        return {
            "status": "simulado",
            "mensagem": "E-mail NAO enviado: LOGIC_APP_URL nao configurada neste ambiente.",
            "tipo": _tipo(payload),
            "squad": payload.get("squad"),
            "subject": payload.get("subject") or payload.get("assunto"),
        }

    body = dict(payload)
    body["corpoHtml"] = montar_corpo_html(payload)
    override = (os.getenv("FINOPS_EMAIL_OVERRIDE_TO") or "").strip()
    if override:
        for k in ("email", "emailSquad", "emailBackup", "emailGestor", "emailDiretor", "emailDiretoria", "emailFinOps",
                  "emailOutros", "to", "cc"):
            if k in body:
                body[k] = override
        body["cc"] = ""  # no teste a copia iria para o mesmo endereco
        body["to"] = override
        for k in ("assunto", "subject"):
            if body.get(k):
                body[k] = "[TESTE] " + str(body[k])
        body["modoTeste"] = True

    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=float(os.getenv("FINOPS_EMAIL_TIMEOUT", "30"))) as r:
            code = r.status
    except urllib.error.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Logic App respondeu HTTP {e.code}")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Falha ao chamar o Logic App: {type(e).__name__}")

    return {
        "status": "enviado",
        "http": code,
        "tipo": _tipo(payload),
        "squad": payload.get("squad"),
        "destino_teste": override or None,
    }


# compatibilidade com o nome antigo
enviar_email_dev = enviar_email
