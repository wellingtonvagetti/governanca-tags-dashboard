# -*- coding: utf-8 -*-
"""Perfis de acesso do dash de recomendacoes.

- admin: e-mail na lista FINOPS_ADMINS (app setting, separada por virgula ou ponto e virgula). Acesso completo.
- squad: e-mail cadastrado em Configuracoes > Squads (E-mail Champion, Backup, Gestor, Gestor Senior ou Diretoria da BU).
  Ve so as recomendacoes das suas squads e grava so Status, Realizado, Data de Implantacao Planejada,
  Data de Implantacao e Observacao, com as mesmas regras da devolutiva.
- bloqueado: logado, mas fora das listas.

O e-mail vem do login do App Service (Easy Auth, cabecalho X-MS-CLIENT-PRINCIPAL-NAME). Sem esse cabecalho
(execucao local, POC sem login) todos sao admin. Com FINOPS_ADMINS vazia tambem: a restricao so liga quando a
lista e preenchida. FINOPS_USUARIO_TESTE simula um e-mail para testar localmente.
"""
import base64
import json
import os
import re
from datetime import date

from api import status as _status

CHAVE_CONFIG_SQUADS = "finops_squad_config_v111"
CAMPOS_EMAIL = ("emailSquad", "emailBackup", "emailGestor", "emailDiretor", "emailDiretoria")
# campos que o responsavel da squad pode gravar (o resto vem sempre do banco)
CAMPOS_SQUAD = ("analise", "realizado", "dataPrevista", "dataEfetivada", "observacao")
# campos de controle que a tela grava junto com a edicao da squad
CAMPOS_CONTROLE = ("dataDevolutiva", "dataAtualizacao", "ticketCycleResponded")
# "squad nao responsavel pelo recurso": volta ao FinOps para redirecionar (nao e reprovacao)
CAMPOS_NAO_RESPONSAVEL = ("squadNaoResponsavel", "squadNaoResponsavelMotivo", "squadNaoResponsavelEm")


def _emails(texto):
    return {normalizar_email(e) for e in re.split(r"[;,\s]+", str(texto or "")) if "@" in e}


def admins():
    return _emails(os.getenv("FINOPS_ADMINS", ""))


def normalizar_email(valor):
    """Conta externa no Entra ID chega como 'live.com#a@b.com' ou 'a_b.com#EXT#@tenant.onmicrosoft.com'."""
    v = str(valor or "").strip().lower()
    if "#ext#" in v:
        local = v.split("#ext#")[0]
        if "_" in local:
            i = local.rfind("_")
            v = local[:i] + "@" + local[i + 1:]
    elif "#" in v:
        v = v.split("#")[-1]
    return v if "@" in v else ""


def emails_da_requisicao(request):
    """Todos os e-mails do usuario logado (nome principal e claims do Easy Auth), normalizados."""
    brutos = [request.headers.get("x-ms-client-principal-name", "")]
    token = request.headers.get("x-ms-client-principal", "")
    if token:
        try:
            dados = json.loads(base64.b64decode(token + "=" * (-len(token) % 4)).decode("utf-8"))
            for c in dados.get("claims") or []:
                tipo = str(c.get("typ") or "").lower()
                if any(t in tipo for t in ("email", "upn", "preferred_username", "/name")):
                    brutos.append(c.get("val"))
        except (ValueError, TypeError):
            pass
    emails = {e for e in (normalizar_email(b) for b in brutos) if e}
    if not emails and os.getenv("FINOPS_USUARIO_TESTE"):
        emails = {normalizar_email(os.getenv("FINOPS_USUARIO_TESTE"))}
    return emails


def nome_da_requisicao(request):
    """Nome de exibicao do login (claim 'name' do Easy Auth)."""
    token = request.headers.get("x-ms-client-principal", "")
    if not token:
        return ""
    try:
        dados = json.loads(base64.b64decode(token + "=" * (-len(token) % 4)).decode("utf-8"))
    except (ValueError, TypeError):
        return ""
    for c in dados.get("claims") or []:
        tipo = str(c.get("typ") or "").lower()
        if tipo == "name" or tipo.endswith("/identity/claims/name"):
            v = str(c.get("val") or "").strip()
            if v and "@" not in v:
                return v
    return ""


def email_da_requisicao(request):
    emails = emails_da_requisicao(request)
    return sorted(emails)[0] if emails else ""


def _config_squads(con):
    linha = con.execute("SELECT state_value FROM app_state WHERE state_key = ?", (CHAVE_CONFIG_SQUADS,)).fetchone()
    try:
        return json.loads(linha[0]) if linha else {}
    except ValueError:
        return {}


def nome_cadastrado(con, emails):
    """Sem nome no login (teste local): o nome do Champion / Gestor cadastrado com aquele e-mail."""
    for c in (_config_squads(con) or {}).values():
        if not isinstance(c, dict):
            continue
        for campo_email, campo_nome in (("emailSquad", "responsavelTecnico"), ("emailBackup", "backup"), ("emailGestor", "responsavel")):
            if _emails(c.get(campo_email)) & set(emails) and str(c.get(campo_nome) or "").strip():
                return str(c.get(campo_nome)).strip()
    return ""


def squads_do_email(con, emails):
    if isinstance(emails, str):
        emails = {emails}
    cfg = _config_squads(con)
    squads = []
    for chave, c in (cfg or {}).items():
        if not isinstance(c, dict):
            continue
        todos = set()
        for campo in CAMPOS_EMAIL:
            todos |= _emails(c.get(campo))
        if todos & set(emails):
            squads.append(str(c.get("name") or chave).strip())
    return sorted(set(s for s in squads if s))


def perfil(request, conectar):
    emails = emails_da_requisicao(request)
    email = sorted(emails)[0] if emails else ""
    nome = nome_da_requisicao(request)
    lista = admins()
    if not emails or not lista or emails & lista:
        return {"email": email, "nome": nome, "papel": "admin", "squads": []}
    with conectar() as con:
        squads = squads_do_email(con, emails)
        if squads and not nome:
            nome = nome_cadastrado(con, emails)
    if squads:
        return {"email": email, "nome": nome, "papel": "squad", "squads": squads}
    return {"email": email, "nome": nome, "papel": "bloqueado", "squads": []}


def _norm(sq):
    return str(sq or "").strip().lower()


def filtrar_linhas(perf, linhas):
    if perf["papel"] != "squad":
        return linhas
    ok = {_norm(s) for s in perf["squads"]}
    return [r for r in (linhas or []) if _norm(r.get("squad")) in ok]


def _vazio(v):
    return str(v or "").strip() == ""


def validar(reg):
    """Mesmas regras da importacao da devolutiva. Devolve a lista de problemas (vazia = ok)."""
    oid = reg.get("finOpsOpportunityId", "")
    classe = _status.legado(reg.get("analise"))
    realizado = bool(reg.get("realizado"))
    hoje = date.today().isoformat()
    erros = []
    if classe == "APROVADO":
        if realizado:
            if _vazio(reg.get("dataEfetivada")):
                erros.append("%s: Capturado exige Data de Implantação" % oid)
            elif str(reg.get("dataEfetivada"))[:10] > hoje:
                erros.append("%s: Data de Implantação no futuro; use Planejada com Data Planejada" % oid)
        elif _vazio(reg.get("dataPrevista")):
            erros.append("%s: Planejada / Em Implementação exige Data de Implantação Planejada" % oid)
    elif classe == "REPROVADO":
        if realizado:
            erros.append("%s: Reprovada exige Realizado = Não" % oid)
        if _vazio(reg.get("observacao")):
            erros.append("%s: Reprovada exige Observação (motivo)" % oid)
    elif classe == "ADIAR":
        if realizado:
            erros.append("%s: Adiada exige Realizado = Não" % oid)
        if _vazio(reg.get("dataPrevista")):
            erros.append("%s: Adiada exige Data de Implantação Planejada" % oid)
        if _vazio(reg.get("observacao")):
            erros.append("%s: Adiada exige Observação" % oid)
    return erros


def restringir_lote(perf, linhas_banco, rows):
    """Para o papel squad: cada linha precisa existir no banco, ser de uma squad do usuario e so muda os campos
    permitidos (o resto vem do banco). Devolve (rows_ajustadas, erros)."""
    if perf["papel"] == "admin":
        return rows, []
    if perf["papel"] != "squad":
        return [], ["Seu e-mail não tem acesso a este dashboard."]
    ok = {_norm(s) for s in perf["squads"]}
    banco = {str(r.get("finOpsOpportunityId") or "").strip(): r for r in (linhas_banco or [])}
    saida, erros = [], []
    for oid, row in rows:
        atual = banco.get(oid)
        if not atual:
            erros.append("%s: recomendação não encontrada nesta competência" % oid)
            continue
        if _norm(atual.get("squad")) not in ok:
            erros.append("%s: recomendação de outra squad (%s)" % (oid, atual.get("squad")))
            continue
        novo = dict(atual)
        for campo in CAMPOS_SQUAD + CAMPOS_CONTROLE + CAMPOS_NAO_RESPONSAVEL:
            if campo in row:
                novo[campo] = row[campo]
        novo["finOpsOpportunityId"] = oid
        if "squadNaoResponsavel" in row:
            novo["squadNaoResponsavelPor"] = perf.get("email", "") if row.get("squadNaoResponsavel") else ""
        # as regras de status valem quando o responsavel muda status, datas ou observacao
        mudou = any(str(novo.get(c) or "") != str(atual.get(c) or "") for c in CAMPOS_SQUAD)
        if mudou:
            erros.extend(validar(novo))
        saida.append((oid, novo))
    return saida, erros
