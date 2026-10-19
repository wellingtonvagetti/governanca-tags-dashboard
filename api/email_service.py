"""Envio de e-mail/alertas via Logic App por HTTP.

Variaveis de ambiente:
  LOGIC_APP_URL                          URL do gatilho HTTP do fluxo. Sem ela, nada e enviado (status "simulado").
  FINOPS_EMAIL_OVERRIDE_TO               se definido, TODO envio vai so para este endereco.
  FINOPS_EMAIL_TIMEOUT                   segundos (padrao 30).
"""
import html as _html
import json
import os
import re
import urllib.error
import urllib.request

from fastapi import HTTPException


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


def _valor(txt):
    try:
        return float(re.sub(r"[^\d,\-]", "", txt).replace(",", "."))
    except ValueError:
        return 0.0


def _brl(v):
    return "R$ " + f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _itens_prioritarios(payload):
    """Itens pendentes acima de R$ 1.000, do maior para o menor."""
    bruto = re.sub(r"<[^>]+>", "", str(payload.get("recomendacoes") or ""))
    itens = []
    for l in (x.strip() for x in bruto.splitlines() if x.strip()):
        m = _RX_REC.match(l)
        if m:
            pri, rec, item, val = m.groups()
            v = _valor(val)
            if v > LIMITE_PRIORIDADE:
                itens.append((v, pri or "", rec, item or "", val))
    itens.sort(key=lambda x: -x[0])
    return itens


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
    lim = "R$ 1.000"
    no_chamado = f", acompanhadas no chamado <b>{chamado}</b>" if chamado else ""
    if abertura:
        titulo = "Recomenda&ccedil;&otilde;es de FinOps &mdash; abertura do ciclo"
        intro = ("Ol&aacute;, pessoal.<br>Segue a planilha com as recomenda&ccedil;&otilde;es de FinOps de "
                 f"<b>{mes}</b> da <b>{squad}</b>{no_chamado}.<br><br>"
                 f"Abaixo est&atilde;o as recomenda&ccedil;&otilde;es acima de {lim}, para prioriza&ccedil;&atilde;o. "
                 "O detalhamento completo, com as demais, est&aacute; na planilha em anexo.")
        pedido = ("Pedimos que avaliem as recomenda&ccedil;&otilde;es"
                  + (f" e registrem o andamento no chamado <b>{chamado}</b>" if chamado else "")
                  + ".")
    else:
        titulo = f"Acompanhamento FinOps &mdash; {fase}" if fase else "Acompanhamento FinOps"
        intro = ("Ol&aacute;, pessoal.<br>Este &eacute; um acompanhamento das recomenda&ccedil;&otilde;es de FinOps de "
                 f"<b>{mes}</b> da <b>{squad}</b>{no_chamado}: ainda constam pend&ecirc;ncias.<br><br>"
                 f"Abaixo est&atilde;o as acima de {lim}; o detalhamento completo est&aacute; na planilha em anexo.")
        pedido = ("Pedimos que informem o andamento"
                  + (f" no chamado <b>{chamado}</b>" if chamado else "")
                  + " ou a justificativa das recomenda&ccedil;&otilde;es que n&atilde;o ser&atilde;o executadas.")

    msg_prior = _t(payload.get("mensagemPrioridade"))

    def kpi(rotulo, valor, sub=""):
        return ("<td style=\"padding:8px 12px;border:1px solid #e3e6ea;background:#f7f8fa;text-align:center;white-space:nowrap\">"
                f"<div style=\"font-size:11px;color:#667085\">{rotulo}</div>"
                f"<div style=\"font-size:16px;font-weight:700;color:#101828\">{valor}</div>"
                + (f"<div style=\"font-size:11px;color:#667085\">{sub}</div>" if sub else "") + "</td>")

    kpis = kpi("Pend&ecirc;ncias", pend) + kpi("Potencial&nbsp;estimado", pot)
    if conc is not None and total is not None:
        kpis += kpi("Conclu&iacute;das", f"{_t(conc)} / {_t(total)}")
    if prazo and not abertura:
        kpis += kpi("Prazo", prazo)

    prior = _itens_prioritarios(payload)
    kpis += kpi(f"Acima de {lim}", str(len(prior)), _brl(sum(x[0] for x in prior)).replace(" ", "&nbsp;") if prior else "")

    itens = ""
    if prior:
        td = "padding:6px 8px;border-bottom:1px solid #eaecf0;font-size:12px;vertical-align:top"
        cab = "padding:6px 8px;background:#f2f4f7;font-size:11px;color:#667085;text-align:left"
        linhas_html = ""
        for v, pri, rec, item, val in prior[:MAX_ITENS_CORPO]:
            linhas_html += (
                f"<tr><td style=\"{td};white-space:nowrap\">{_t(pri)}</td>"
                f"<td style=\"{td}\"><b>{_t(item)}</b><br><span style=\"color:#667085\">{_t(rec)}</span></td>"
                f"<td style=\"{td};text-align:right;white-space:nowrap\">{_t(val).replace(' ', '&nbsp;')}</td></tr>")
        itens = (f"<p style=\"margin:18px 0 6px;font-weight:700\">Recomenda&ccedil;&otilde;es acima de {lim}</p>"
                 "<table width=\"100%\" cellspacing=\"0\" cellpadding=\"0\" style=\"border-collapse:collapse\">"
                 f"<tr><th style=\"{cab}\">Prioridade</th><th style=\"{cab}\">Item / recomenda&ccedil;&atilde;o</th>"
                 f"<th style=\"{cab};text-align:right\">Saving estimado</th></tr>{linhas_html}</table>")
        if len(prior) > MAX_ITENS_CORPO:
            itens += (f"<p style=\"font-size:12px;color:#667085;margin:8px 0 0\">"
                      f"... e mais {len(prior) - MAX_ITENS_CORPO} item(ns) acima de {lim}. Lista completa na planilha anexa.</p>")
    else:
        itens = (f"<p style=\"margin:18px 0 0;color:#667085\">N&atilde;o h&aacute; recomenda&ccedil;&otilde;es pendentes "
                 f"acima de {lim}. Veja a planilha em anexo.</p>")

    return (
        "<div style=\"font-family:Segoe UI,Arial,sans-serif;max-width:640px;color:#101828\">"
        f"<div style=\"background:#e8590c;color:#fff;padding:14px 18px;font-size:16px;font-weight:700\">{titulo}</div>"
        "<div style=\"padding:18px;border:1px solid #e3e6ea;border-top:0\">"
        f"<p style=\"margin:0 0 14px\">{intro}</p>"
        f"<table cellspacing=\"6\" cellpadding=\"0\" style=\"border-collapse:separate\"><tr>{kpis}</tr></table>"
        + (f"<p style=\"margin:14px 0 0;color:#b54708\"><b>{msg_prior}</b></p>" if msg_prior else "")
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
        for k in ("email", "emailSquad", "emailGestor", "emailDiretor", "to", "cc"):
            if k in body:
                body[k] = override
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
