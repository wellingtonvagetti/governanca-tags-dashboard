# -*- coding: utf-8 -*-
"""Registro de Decisao de Custo (RDC) em PDF preenchivel.

O dash monta os dados da squad (recomendacoes reprovadas Alta/Critica do mes, devolutiva, responsaveis) e esta
funcao devolve o PDF com esses campos ja preenchidos; o que depende da Reuniao de Analise e Deliberacao (diretor,
centro de custo, validade, natureza da justificativa, assinaturas) fica em branco para preencher.
Valores em R$ 1.234,56; o anual (mensal x 12) e os totais sao recalculados no Acrobat quando um mensal muda.
"""
import io
from datetime import date

from pypdf import PdfReader, PdfWriter
from pypdf.generic import ArrayObject, BooleanObject, DictionaryObject, NameObject, NumberObject, TextStringObject
from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import simpleSplit
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

LARANJA, ESCURO, CINZA, LINHA = HexColor("#FF6C0C"), HexColor("#1E212C"), HexColor("#7D868C"), HexColor("#CCCCCC")
ROT_BG, TOTAL_BG, SLATE = HexColor("#F2F3F4"), HexColor("#ECEDEE"), HexColor("#4C5F71")
W, H = A4
M = 50
LARG = W - 2 * M
RODAPE = 60

ROTULOS = [
    ("numero", "Nº do RDC / ID"), ("emissao", "Data de emissão"), ("bu", "Unidade de Negócio (BU)"),
    ("diretor", "Diretor da BU"), ("centro_custo", "Centro de Custo"), ("gestor", "Gestor Responsável"),
    ("email_gestor", "E-mail do Gestor"), ("tecnico", "Responsável Técnico"),
    ("email_tecnico", "E-mail do Responsável Técnico"),
    ("finops", "Responsável FinOps / Governança Cloud (solicitante)"),
    ("validade", "Validade da exceção / reavaliação"),
]
COLS = [("ID FinOps", 78), ("Recomendação", 108), ("Recurso / Ambiente", 104), ("Categoria", 70),
        ("Saving Est. Mensal (R$)", 67), ("Saving Est. Anual (R$)", LARG - 78 - 108 - 104 - 70 - 67)]
CHAVES = ["id", "recomendacao", "recurso", "categoria", "mensal", "anual"]
OPCOES = [("tecnica", "Técnica", "risco de indisponibilidade, incompatibilidade, restrição de arquitetura"),
          ("negocio", "Negócio", "sazonalidade, SLA contratual, prioridade de projeto"),
          ("financeira", "Financeira", "orçamento já comprometido, custo de implementação")]
DECLARACAO = [
    "A recomendação acima foi formalmente apresentada pela área de FinOps/Governança Cloud como oportunidade de "
    "otimização de custos.",
    "A decisão de não implementá-la é de responsabilidade exclusiva da Unidade de Negócio signatária.",
    "O Saving Estimado destas recomendações não será considerado nas metas e indicadores de otimização da área de "
    "FinOps e será reportado como oportunidade não capturada, nunca como saving.",
    "O custo adicional decorrente desta decisão será mantido no orçamento (budget) da BU responsável e acompanhado "
    "nos relatórios de gestão de custos cloud.",
    "Esta exceção é temporária e vale até a data indicada na Seção 1; a renovação exige nova análise, valor recalculado "
    "e nova aprovação. Pode ser reavaliada antes, a qualquer momento, por solicitação da BU ou da Governança Cloud.",
]
ASSINATURAS = ["Gestor Responsável (BU)", "Responsável Técnico", "Gestor da Squad (aprovação)",
               "Representante FinOps / Governança Cloud"]

# JavaScript dos campos de valor (Acrobat): aceita "6793,45", "6.793,45" ou "R$ 6.793,45"
JS_NUM = ('function n(c){var v=String(this.getField(c).value).replace(/[^0-9,.-]/g,"");'
          'if(v.indexOf(",")>=0)v=v.replace(/\\./g,"").replace(",",".");var x=Number(v);return isNaN(x)?0:x;}'
          'function brl(x){var s=x.toFixed(2).split(".");s[0]=s[0].replace(/\\B(?=(\\d{3})+(?!\\d))/g,".");'
          'return "R$ "+s[0]+","+s[1];}'
          'function vazio(c){return String(this.getField(c).value).replace(/\\s/g,"")==="";}')


def brl(v):
    return ("R$ {:,.2f}".format(float(v or 0))).replace(",", "X").replace(".", ",").replace("X", ".")


def _txt(s):
    """Fontes padrao do PDF usam WinAnsi (cp1252): troca o que nao cabe."""
    s = str(s or "").replace("→", "->").replace("≥", ">=").replace("≤", "<=")
    return s.encode("cp1252", "replace").decode("cp1252")


class _Pdf:
    def __init__(self, buf, total_paginas):
        self.c = canvas.Canvas(buf, pagesize=A4)
        self.c.setTitle("Registro de Decisão de Custo (RDC)")
        self.c.setAuthor("Governança Cloud / FinOps · Evertec")
        self.total = total_paginas
        self.pagina = 1
        self.y = H - 80
        self.moldura()

    def moldura(self):
        c = self.c
        c.setFont("Helvetica-Bold", 11); c.setFillColor(CINZA); c.drawString(M, H - 38, "EVERTEC")
        c.setFont("Helvetica", 8.5); c.setFillColor(SLATE)
        c.drawString(M + stringWidth("EVERTEC", "Helvetica-Bold", 11) + 6, H - 38,
                     _txt("|  Governança Cloud & FinOps Corporativo — ITOPS"))
        c.setStrokeColor(LARANJA); c.setLineWidth(2); c.line(M, H - 46, W - M, H - 46)
        c.setFont("Helvetica-Oblique", 7.5); c.setFillColor(CINZA)
        c.drawCentredString(W / 2, 34, _txt("Uso interno — Documento controlado por Governança Cloud/FinOps · ITOPS Evertec"))
        c.drawCentredString(W / 2, 24, "Página %d de %d" % (self.pagina, self.total))

    def nova_pagina(self):
        self.c.showPage()
        self.pagina += 1
        self.y = H - 80
        self.moldura()

    def cabe(self, altura):
        if self.y - altura < RODAPE:
            self.nova_pagina()
            return False
        return True

    def campo(self, nome, x, y, w, h, valor="", multi=False, tam=9, leitura=False):
        flags = []
        if multi:
            flags.append("multiline")
        if leitura:
            flags.append("readOnly")
        self.c.acroForm.textfield(name=nome, value=_txt(valor), x=x, y=y, width=w, height=h, fontName="Helvetica",
                                  fontSize=tam, borderWidth=0, fillColor=white, textColor=ESCURO,
                                  fieldFlags=" ".join(flags), annotationFlags="print")

    def texto(self, x, s, fonte="Helvetica", tam=9.5, cor=ESCURO, larg=LARG, entre=12.5):
        c = self.c
        c.setFont(fonte, tam); c.setFillColor(cor)
        for linha in simpleSplit(_txt(s), fonte, tam, larg):
            c.drawString(x, self.y, linha)
            self.y -= entre

    def secao(self, titulo):
        c = self.c
        c.setFont("Helvetica-Bold", 13); c.setFillColor(ESCURO); c.drawString(M, self.y, _txt(titulo))
        c.setStrokeColor(LARANJA); c.setLineWidth(1.5); c.line(M, self.y - 6, W - M, self.y - 6)
        self.y -= 22

    def celula(self, x, y, w, h, fundo=None):
        c = self.c
        if fundo is not None:
            c.setFillColor(fundo); c.rect(x, y, w, h, stroke=0, fill=1)
        c.setStrokeColor(LINHA); c.setLineWidth(0.6); c.rect(x, y, w, h, stroke=1, fill=0)

    def cabecalho_tabela(self):
        c, hh = self.c, 26
        self.y -= hh
        x = M
        for nome, w in COLS:
            c.setFillColor(ESCURO); c.rect(x, self.y, w, hh, stroke=0, fill=1)
            c.setFillColor(white); c.setFont("Helvetica-Bold", 7.5)
            ls = simpleSplit(nome, "Helvetica-Bold", 7.5, w - 8)
            yy = self.y + hh / 2 + (len(ls) - 1) * 4.5 - 2.5
            for linha in ls:
                c.drawCentredString(x + w / 2, yy, linha)
                yy -= 9
            x += w


def _desenhar(buf, d, total_paginas):
    p = _Pdf(buf, total_paginas)
    c = p.c
    c.setFont("Helvetica-Bold", 22); c.setFillColor(LARANJA)
    c.drawString(M, p.y - 8, _txt("REGISTRO DE DECISÃO DE CUSTO (RDC)"))
    p.y -= 28
    p.texto(M, "Não acatação de recomendação de otimização de custos FinOps", "Helvetica-Oblique", 11, SLATE)
    p.y -= 4
    p.texto(M, "Este documento formaliza a decisão da Unidade de Negócio (BU) de não implementar uma ou mais recomendações "
               "de otimização de custos em nuvem identificadas pela área de FinOps/Governança Cloud, registrando a "
               "justificativa apresentada e o valor de economia estimado que deixará de ser realizado. Aplica-se às "
               "recomendações de prioridade Alta e Crítica (Saving Estimado acima de R$ 1.000) cuja não implementação "
               "foi deliberada na Reunião de Análise e Deliberação.")
    p.y -= 14
    p.secao("1. Identificação")
    rl, rh = 230, 21
    ident = d.get("identificacao") or {}
    for i, (chave, rotulo) in enumerate(ROTULOS):
        p.y -= rh
        p.celula(M, p.y, rl, rh, ROT_BG); p.celula(M + rl, p.y, LARG - rl, rh)
        c.setFont("Helvetica-Bold", 8.5); c.setFillColor(ESCURO); c.drawString(M + 7, p.y + 7, _txt(rotulo))
        p.campo("ident_%s" % chave, M + rl + 2, p.y + 2, LARG - rl - 4, rh - 4, ident.get(chave, ""))
    p.y -= 26
    p.secao("2. Recomendações Não Acatadas")
    p.texto(M, "Relação das recomendações de prioridade Alta ou Crítica (Saving Estimado acima de R$ 1.000) reprovadas no "
               "ciclo, com o respectivo Saving Estimado mensal e anual não capturado.")
    p.y -= 4
    itens = list(d.get("itens") or [])
    linhas = max(len(itens), 3)
    p.cabecalho_tabela()
    for r in range(linhas):
        it = itens[r] if r < len(itens) else {}
        mensal = it.get("mensal")
        vals = [it.get("id", ""), it.get("recomendacao", ""), it.get("recurso", ""), it.get("categoria", ""),
                brl(mensal) if mensal not in (None, "") else "", brl(float(mensal) * 12) if mensal not in (None, "") else ""]
        n_lin = max(len(simpleSplit(_txt(vals[k]), "Helvetica", 7.5, COLS[k][1] - 8)) for k in (1, 2))
        lh = max(24, n_lin * 9 + 8)
        if not p.cabe(lh + 22):
            p.cabecalho_tabela()
        p.y -= lh
        x = M
        for k, (_, w) in enumerate(COLS):
            p.celula(x, p.y, w, lh)
            p.campo("rec%d_%s" % (r + 1, CHAVES[k]), x + 2, p.y + 2, w - 4, lh - 4, vals[k], multi=k in (1, 2),
                    tam=7.5 if k in (1, 2) else 8, leitura=k == 5)
            x += w
    p.y -= 22
    wl = sum(w for _, w in COLS[:4])
    p.celula(M, p.y, wl, 22, TOTAL_BG)
    c.setFont("Helvetica-Bold", 9); c.setFillColor(ESCURO); c.drawRightString(M + wl - 8, p.y + 7, _txt("Total estimado não realizado:"))
    tot = sum(float(it.get("mensal") or 0) for it in itens)
    x = M + wl
    for k, (_, w) in enumerate(COLS[4:]):
        p.celula(x, p.y, w, 22, TOTAL_BG)
        p.campo("total_" + ("mensal", "anual")[k], x + 2, p.y + 2, w - 4, 18, brl(tot * (1, 12)[k]) if itens else "",
                tam=8.5, leitura=True)
        x += w

    # secoes 3 a 5 sempre juntas numa pagina nova
    p.nova_pagina()
    p.secao("3. Justificativa para o Não Aceite")
    c.setFont("Helvetica-Bold", 9.5); c.setFillColor(ESCURO)
    c.drawString(M, p.y, _txt("Assinale a(s) natureza(s) da justificativa apresentada pela BU:"))
    p.y -= 8
    bh, bw = 52, LARG / 3
    p.y -= bh
    for i, (k, tit, ex) in enumerate(OPCOES):
        x = M + i * bw
        p.celula(x, p.y, bw, bh)
        c.acroForm.checkbox(name="just_" + k, x=x + 9, y=p.y + bh / 2 - 7, size=14, buttonStyle="check",
                            borderColor=ESCURO, fillColor=white, textColor=LARANJA, borderWidth=0.8, checked=False,
                            annotationFlags="print")
        c.setFont("Helvetica-Bold", 9); c.setFillColor(ESCURO); c.drawString(x + 30, p.y + bh - 15, _txt(tit))
        c.setFont("Helvetica", 7.8); c.setFillColor(SLATE)
        yy = p.y + bh - 27
        for linha in simpleSplit(_txt("ex.: " + ex), "Helvetica", 7.8, bw - 38):
            c.drawString(x + 30, yy, linha); yy -= 9.5
    p.y -= 20
    c.setFont("Helvetica-Bold", 9.5); c.setFillColor(ESCURO); c.drawString(M, p.y, _txt("Descrição detalhada da justificativa:"))
    p.y -= 96
    p.celula(M, p.y, LARG, 88)
    p.campo("justificativa", M + 3, p.y + 3, LARG - 6, 82, d.get("justificativa", ""), multi=True, tam=8.5)
    p.y -= 26
    p.secao("4. Declaração de Aceite do Risco e Responsabilidade")
    p.texto(M, "Eu, responsável pela Unidade de Negócio identificada neste documento, declaro estar ciente de que:")
    p.y -= 2
    for it in DECLARACAO:
        c.setFillColor(LARANJA); c.circle(M + 14, p.y + 3, 1.8, stroke=0, fill=1)
        p.texto(M + 24, it, larg=LARG - 24)
        p.y -= 3
    p.y -= 14
    p.secao("5. Assinaturas")
    # espaco para assinar; o campo Nome e a propria linha; embaixo: papel e Data
    sh, sw = 84, LARG / 2
    for i, nome in enumerate(ASSINATURAS):
        if i % 2 == 0:
            p.y -= sh
        x = M + (i % 2) * sw
        p.celula(x, p.y, sw, sh)
        c.setFont("Helvetica-Oblique", 6.5); c.setFillColor(CINZA); c.drawString(x + 12, p.y + 55, "Nome")
        p.campo("assinatura_%d_nome" % (i + 1), x + 10, p.y + 37, sw - 20, 16, tam=8.5)
        c.setStrokeColor(ESCURO); c.setLineWidth(0.6); c.line(x + 10, p.y + 36, x + sw - 10, p.y + 36)
        c.setFont("Helvetica-Bold", 8.5); c.setFillColor(ESCURO); c.drawString(x + 10, p.y + 24, _txt(nome))
        c.setFont("Helvetica-Oblique", 7.5); c.setFillColor(CINZA); c.drawString(x + 10, p.y + 8, "Data:")
        p.campo("assinatura_%d_data" % (i + 1), x + 34, p.y + 4, 90, 15, tam=8)
    c.save()
    return p.pagina, linhas


def _calculos(pdf, linhas):
    """Anual = mensal x 12 e totais, recalculados no Acrobat quando um mensal muda."""
    w = PdfWriter(clone_from=PdfReader(io.BytesIO(pdf)))

    def js(code):
        return DictionaryObject({NameObject("/S"): NameObject("/JavaScript"), NameObject("/JS"): TextStringObject(code)})

    soma = ('var s=0,t=false;for(var i=1;i<=%d;i++){var c="rec"+i+"_mensal";if(!vazio(c)){t=true;s+=n(c)*%s;}}'
            'event.value=t?brl(s):"";')
    refs = {}
    for page in w.pages:
        for a in page.get("/Annots", []):
            o = a.get_object()
            nome = str(o.get("/T", ""))
            calc = None
            if nome.startswith("rec") and nome.endswith("_anual"):
                i = nome[3:nome.index("_")]
                calc = JS_NUM + 'var c="rec%s_mensal";event.value=vazio(c)?"":brl(n(c)*12);' % i
            elif nome == "total_mensal":
                calc = JS_NUM + soma % (linhas, "1")
            elif nome == "total_anual":
                calc = JS_NUM + soma % (linhas, "12")
            elif nome.startswith("rec") and nome.endswith("_mensal"):
                # ao sair do campo, mostra no formato R$ 1.234,56
                o[NameObject("/AA")] = DictionaryObject({NameObject("/Bl"): js(
                    JS_NUM + 'if(String(event.target.value).replace(/\\s/g,"")!=="")'
                    'event.target.value=brl(n(event.target.name));')})
                o[NameObject("/Q")] = NumberObject(2)
            if calc:
                o[NameObject("/AA")] = DictionaryObject({NameObject("/C"): js(calc)})
                o[NameObject("/Q")] = NumberObject(2)
                refs[nome] = a
    af = w._root_object["/AcroForm"]
    ordem = ["rec%d_anual" % i for i in range(1, linhas + 1)] + ["total_mensal", "total_anual"]
    af[NameObject("/CO")] = ArrayObject([refs[k] for k in ordem if k in refs])
    af[NameObject("/NeedAppearances")] = BooleanObject(True)
    out = io.BytesIO()
    w.write(out)
    return out.getvalue()


def gerar_rdc(dados):
    """dados = {identificacao: {...}, itens: [{id, recomendacao, recurso, categoria, mensal}], justificativa}."""
    paginas, _ = _desenhar(io.BytesIO(), dados, 1)  # 1a passada so para contar as paginas
    buf = io.BytesIO()
    _, linhas = _desenhar(buf, dados, paginas)
    return _calculos(buf.getvalue(), linhas)


def hoje_br():
    return date.today().strftime("%d/%m/%Y")
