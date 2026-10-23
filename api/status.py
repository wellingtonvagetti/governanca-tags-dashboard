# -*- coding: utf-8 -*-
"""Status de analise das recomendacoes (coluna `analise`).

Lista oficial (do inicio ao fim do ciclo):
  RASCUNHO            preenchendo ainda, sem identificacao
  IDENTIFICADA        ja tem equipe e valor
  VALIDAÇÃO TÉCNICA   em analise
  PLANEJADA           aprovada, ainda nao realizada (com data prevista)
  EM IMPLEMENTAÇÃO    aprovada e em execucao (escolhido pela squad)
  CAPTURADO           aprovada e realizada (realizado = Sim)
  REPROVADA
  ADIADA

Valores antigos (APROVADO, EM ANÁLISE, REPROVADO, ADIAR e vazio) continuam
aceitos na ENTRADA e sao convertidos por `normalizar`; nada novo e gravado com
eles.
"""
import re
import unicodedata

RASCUNHO = "Rascunho"
IDENTIFICADA = "Identificada"
VALIDACAO = "Validação Técnica"
PLANEJADA = "Planejada"
IMPLEMENTACAO = "Em Implementação"
CAPTURADO = "Capturado"
REPROVADA = "Reprovada"
ADIADA = "Adiada"

STATUS = (
    RASCUNHO,
    IDENTIFICADA,
    VALIDACAO,
    PLANEJADA,
    IMPLEMENTACAO,
    CAPTURADO,
    REPROVADA,
    ADIADA,
)

# "Aprovado" = tudo que saiu da analise com sinal verde.
APROVADOS = (PLANEJADA, IMPLEMENTACAO, CAPTURADO)

# Ainda precisam de acao: passam de um mes para o seguinte.
PENDENTES = (RASCUNHO, IDENTIFICADA, VALIDACAO, ADIADA, PLANEJADA, IMPLEMENTACAO)


def chave(valor):
    """Maiusculo, sem acento e com espacos normalizados."""
    texto = str(valor or "").strip().upper()
    texto = "".join(
        c for c in unicodedata.normalize("NFKD", texto)
        if not unicodedata.combining(c)
    )
    return " ".join(texto.split())


_DIRETOS = {
    "": RASCUNHO,
    "RASCUNHO": RASCUNHO,
    "IDENTIFICADA": IDENTIFICADA,
    "IDENTIFICADO": IDENTIFICADA,
    "VALIDACAO TECNICA": VALIDACAO,
    "EM ANALISE": VALIDACAO,
    "PLANEJADA": PLANEJADA,
    "PLANEJADO": PLANEJADA,
    "EM IMPLEMENTACAO": IMPLEMENTACAO,
    "CAPTURADO": CAPTURADO,
    "CAPTURADA": CAPTURADO,
    "REPROVADA": REPROVADA,
    "REPROVADO": REPROVADA,
    "ADIADA": ADIADA,
    "ADIADO": ADIADA,
    "ADIAR": ADIADA,
}


_RE_CHAMADO_INTERNO = re.compile(r"SR-\d+|chamado\s+(dedalus|interno)|ticket\s+aberto", re.I)


def chamado_interno(observacao):
    """Observacao com chamado aberto para a execucao: "Chamado Dedalus - SR-437072",
    "Dedalus responsavel pela execucao, ticket aberto SR-453663", "Chamado interno ..."."""
    return bool(_RE_CHAMADO_INTERNO.search(str(observacao or "")))


def _aprovada_sem_estagio(realizado, ticket, observacao=""):
    # O ticket e o chamado da devolutiva (o FinOps abre para todas as squads): nao indica implementacao.
    # Aprovada e nao realizada = PLANEJADA; EM IMPLEMENTAÇÃO quando ha chamado interno de execucao
    # (Observacao "Chamado Dedalus - ...") ou quando a squad escolhe esse status.
    if realizado:
        return CAPTURADO
    if chamado_interno(observacao):
        return IMPLEMENTACAO
    return PLANEJADA


def normalizar(analise, realizado=False, ticket="", observacao=""):
    """Converte qualquer valor (antigo ou novo) para um status oficial.

    - APROVADO (antigo): realizado=Sim -> CAPTURADO; com chamado interno na Observacao
      ("Chamado Dedalus - ...") -> EM IMPLEMENTAÇÃO; senao PLANEJADA.
    - Coerencia: aprovada + realizado = CAPTURADO; CAPTURADO sem realizado volta
      a PLANEJADA.
    - Texto desconhecido (nao vazio) cai em VALIDAÇÃO TÉCNICA, como o dash fazia
      com EM ANÁLISE.
    """
    k = chave(analise)
    if k in ("APROVADO", "APROVADA"):
        return _aprovada_sem_estagio(realizado, ticket, observacao)
    status = _DIRETOS.get(k, VALIDACAO)
    if status in (PLANEJADA, IMPLEMENTACAO) and realizado:
        return CAPTURADO
    if status == CAPTURADO and not realizado:
        return _aprovada_sem_estagio(False, ticket, observacao)
    return status


def aprovado(analise, realizado=False, ticket=""):
    return normalizar(analise, realizado, ticket) in APROVADOS


def pendente(analise, realizado=False, ticket=""):
    """Equivale a regra antiga: EM ANÁLISE, ADIAR ou APROVADO nao realizado."""
    return normalizar(analise, realizado, ticket) in PENDENTES


def legado(analise):
    """Classe antiga do status (APROVADO / EM ANÁLISE / REPROVADO / ADIAR / '').

    Serve para o verificador de numeros: o hash de Setembro nao muda com a
    troca de nomes. Aceita valores dos dois vocabularios.
    """
    k = chave(analise)
    if k in ("APROVADO", "APROVADA", "PLANEJADA", "PLANEJADO",
             "EM IMPLEMENTACAO", "CAPTURADO", "CAPTURADA"):
        return "APROVADO"
    if k in ("EM ANALISE", "VALIDACAO TECNICA"):
        return "EM ANÁLISE"
    if k in ("REPROVADO", "REPROVADA"):
        return "REPROVADO"
    if k in ("ADIAR", "ADIADA", "ADIADO"):
        return "ADIAR"
    if k in ("", "RASCUNHO", "IDENTIFICADA", "IDENTIFICADO"):
        return ""
    return str(analise or "").strip()
