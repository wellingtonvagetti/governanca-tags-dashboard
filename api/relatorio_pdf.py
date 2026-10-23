# -*- coding: utf-8 -*-
"""Relatorios de acompanhamento das recomendacoes (PDF): parcial da competencia e fechamento do mes.

O dash monta os numeros (nomes de exibicao, totais, squads, BUs e categorias) e manda prontos; aqui so desenha.
Os dois tem o mesmo formato; o fechamento acrescenta o saving efetivado (validado por custo), o rescaldo e os
tops por status (implementadas, em andamento, pendentes e rejeitadas).
Duas passadas: a primeira conta as paginas (tabelas longas quebram pagina) para o "Pagina x de y".
"""
import io
import math

from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import simpleSplit
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

W, H = A4
M = 42
LARG = W - 2 * M
BASE = 52  # abaixo disso e rodape

NAVY, TEAL, BLUE, ORANGE, RED = (HexColor(x) for x in ("#12263F", "#0F7C80", "#3B7DD8", "#F2A03D", "#C0392B"))
INK, MUT, LINE, ZEBRA, HL = (HexColor(x) for x in ("#1D2733", "#6B7785", "#E3E8EE", "#F4F7FA", "#E8F3F3"))
KICK, PER = HexColor("#7FD6D2"), HexColor("#C9D3DF")
FUNIL = [HexColor(x) for x in ("#5D7189", "#B0473E", "#C08A2E", "#2F6FA0", "#108A6A")]
PAL = [HexColor(x) for x in ("#12263F", "#0F7C80", "#3B7DD8", "#F2A03D", "#8A6FD6", "#D65A7A", "#7BB36A", "#5BB8C9",
                             "#C98B2B", "#2F5F8F", "#B56576", "#6C8E3E", "#9AA5B4", "#E07A5F", "#4F6D7A", "#A37CB5",
                             "#C2A878", "#58A4B0", "#B07AA1", "#7D9D5C", "#D9886A", "#6E8B9E")]
F_CEL, F_SUB = 7.4, 6.2


def _txt(s):
    """Fontes padrao do PDF usam WinAnsi (cp1252): troca o que nao cabe."""
    s = str(s if s is not None else "").replace("→", "->").replace("≥", ">=").replace("≤", "<=")
    return s.encode("cp1252", "replace").decode("cp1252")


def num(v):
    return "{:,.0f}".format(round(float(v or 0))).replace(",", ".")


def brl(v, dec=False):
    if dec:
        return ("R$ {:,.2f}".format(float(v or 0))).replace(",", "X").replace(".", ",").replace("X", ".")
    return "R$ " + num(v)


def pct(a, b):
    return ("%.1f%%" % (100.0 * a / b)).replace(".", ",") if b else "0,0%"


def mil(v):
    return "R$ " + ("{:,.1f}".format(float(v or 0) / 1000)).replace(",", "X").replace(".", ",").replace("X", ".") + " mil"


def traco(v):
    return num(v) if v else "–"


def traco_r(v):
    return brl(v) if round(float(v or 0)) else "–"


def lista_curta(xs, n=3):
    xs = [x for x in xs if x]
    return ", ".join(xs[:n]) + (" +%d" % (len(xs) - n) if len(xs) > n else "")


class _Pdf:
    def __init__(self, buf, d, total, cab_direita):
        self.c = canvas.Canvas(buf, pagesize=A4)
        self.c.setTitle(_txt("Relatório de Acompanhamento FinOps - " + d["mes"]))
        self.c.setAuthor("FinOps / Cloud Governance")
        self.d, self.total, self.pagina, self.cab_direita = d, total, 1, cab_direita
        self.y = H - 40

    # ---------------------------------------------------------------- base
    def fonte(self, tam, bold=False, cor=INK):
        self.c.setFont("Helvetica-Bold" if bold else "Helvetica", tam)
        self.c.setFillColor(cor)

    def texto(self, x, y, s, tam, bold=False, cor=INK, alinha="l"):
        self.fonte(tam, bold, cor)
        s = _txt(s)
        if alinha == "r":
            self.c.drawRightString(x, y, s)
        elif alinha == "c":
            self.c.drawCentredString(x, y, s)
        else:
            self.c.drawString(x, y, s)

    def rodape(self):
        c = self.c
        c.setStrokeColor(LINE)
        c.setLineWidth(0.6)
        c.line(M, 34, W - M, 34)
        self.texto(M, 24, "Uso interno", 7, cor=MUT)
        self.texto(W / 2, 24, "FinOps / Cloud Governance", 7, cor=MUT, alinha="c")
        self.texto(W - M, 24, "Página %d de %d" % (self.pagina, self.total), 7, cor=MUT, alinha="r")

    def nova_pagina(self):
        self.rodape()
        self.c.showPage()
        self.pagina += 1
        self.y = H - 40
        self.texto(M, self.y, "Relatório de Acompanhamento FinOps", 8, True, NAVY)
        largura = stringWidth(_txt("Relatório de Acompanhamento FinOps"), "Helvetica-Bold", 8)
        self.c.setStrokeColor(TEAL)
        self.c.setLineWidth(1.4)
        self.c.line(M, self.y - 4, M + largura, self.y - 4)
        self.texto(W - M, self.y, self.cab_direita, 8, cor=MUT, alinha="r")
        self.y -= 30

    def cabe(self, altura):
        if self.y - altura < BASE:
            self.nova_pagina()

    def titulo(self, s, tam=14):
        if self.y < H - 90:
            self.y -= 12  # respiro quando vem depois de outro bloco na mesma pagina
        self.cabe(60)
        self.texto(M, self.y, s, tam, True, NAVY)
        self.y -= tam + 4

    def subtitulo(self, s):
        if self.y < H - 90:
            self.y -= 4
        self.cabe(50)
        self.texto(M, self.y, s, 10, True, TEAL)
        self.y -= 14

    def paragrafo(self, s, tam=8.6, cor=INK, larg=LARG, entre=11.5):
        for linha in simpleSplit(_txt(s), "Helvetica", tam, larg):
            self.cabe(entre)
            self.texto(M, self.y, linha, tam, cor=cor)
            self.y -= entre

    def bullets(self, itens):
        for neg, resto in itens:
            wn = stringWidth(_txt(neg), "Helvetica-Bold", 8.4)
            linhas = simpleSplit(_txt(resto), "Helvetica", 8.4, LARG - 12 - wn)
            self.cabe(12 + 11 * (len(linhas) - 1))
            self.c.setFillColor(INK)
            self.c.circle(M + 4, self.y + 2.6, 1.3, stroke=0, fill=1)
            self.texto(M + 12, self.y, neg, 8.4, True)
            self.texto(M + 12 + wn, self.y, linhas[0] if linhas else "", 8.4)
            for extra in linhas[1:]:
                self.y -= 11
                self.texto(M + 12, self.y, extra, 8.4)
            self.y -= 14

    # ---------------------------------------------------------------- blocos
    def hero(self, subtitulo):
        c = self.c
        top, alt = H - 34, 92
        c.setFillColor(NAVY)
        c.roundRect(M, top - alt, LARG, alt, 7, stroke=0, fill=1)
        c.setFillColor(TEAL)
        c.rect(M, top - alt, 8, alt, stroke=0, fill=1)
        self.texto(M + 24, top - 20, "FINOPS / CLOUD GOVERNANCE", 7.5, True, KICK)
        self.texto(M + 24, top - 40, "Relatório de Acompanhamento das Recomendações", 16, True, white)
        self.texto(M + 24, top - 59, "de Eficiência FinOps", 16, True, white)
        self.texto(M + 24, top - 78, subtitulo, 8.5, cor=PER)
        self.y = top - alt - 26

    def cards(self, itens):
        gap, alt = 7, 58
        lw = (LARG - gap * (len(itens) - 1)) / len(itens)
        self.cabe(alt + 10)
        topo = self.y
        for i, (rot, val, pe, cor) in enumerate(itens):
            x = M + i * (lw + gap)
            self.c.setFillColor(ZEBRA)
            self.c.rect(x, topo - alt, lw, alt, stroke=0, fill=1)
            self.c.setFillColor(cor)
            self.c.rect(x, topo - alt, 3, alt, stroke=0, fill=1)
            yy = topo - 12
            for linha in simpleSplit(_txt(rot), "Helvetica", 6.2, lw - 14)[:2]:
                self.texto(x + 9, yy, linha, 6.2, cor=MUT)
                yy -= 7.5
            self.texto(x + 9, yy - 9, val, 13.5, True, cor)
            yy -= 20
            for linha in simpleSplit(_txt(pe), "Helvetica", 6.5, lw - 14)[:2]:
                self.texto(x + 9, yy, linha, 6.5, cor=MUT)
                yy -= 8
        self.y = topo - alt - 16

    def tabela(self, cols, linhas, total=None, realce=(), extras=(), alt_lin=17, alt_cab=22):
        """cols: [(titulo, largura, alinhamento)]; celula: texto ou (texto, subtexto, estilo 'b'|'ok'|'mut').
        Texto longo quebra linha dentro da coluna. extras: linhas apos o total (estilo apagado)."""
        larguras = [w for _, w, _ in cols]
        esc = LARG / float(sum(larguras))
        larguras = [w * esc for w in larguras]

        def cabecalho():
            self.c.setFillColor(NAVY)
            self.c.rect(M, self.y - alt_cab, LARG, alt_cab, stroke=0, fill=1)
            x = M
            for (tit, _, al), lw in zip(cols, larguras):
                partes = tit.split("\n")
                yy = self.y - alt_cab / 2 + (len(partes) - 1) * 3.6 - 2.6
                for p in partes:
                    if al == "r":
                        self.texto(x + lw - 5, yy, p, 6.6, True, white, "r")
                    else:
                        self.texto(x + 5, yy, p, 6.6, True, white)
                    yy -= 7.2
                x += lw
            self.y -= alt_cab

        def partes(cl, lw):
            principal, sub, estilo = (tuple(cl) + (None, None))[:3] if isinstance(cl, tuple) else (cl, None, None)
            fonte = "Helvetica-Bold" if estilo in ("b", "ok") else "Helvetica"
            lp = simpleSplit(_txt(principal), fonte, F_CEL, lw - 10) or [""]
            ls = simpleSplit(_txt(sub), "Helvetica", F_SUB, lw - 10) if sub else []
            return lp, ls, estilo

        def linha(cells, fundo, negrito=False, borda_topo=False, apagada=False):
            info = [partes(cl, lw) for cl, lw in zip(cells, larguras)]
            conteudo = max(9.0 * len(lp) + 7.8 * len(ls) for lp, ls, _ in info)
            alt = max(alt_lin, conteudo + 8)
            if self.y - alt < BASE:
                self.nova_pagina()
                cabecalho()
            if fundo:
                self.c.setFillColor(fundo)
                self.c.rect(M, self.y - alt, LARG, alt, stroke=0, fill=1)
            if borda_topo:
                self.c.setStrokeColor(NAVY)
                self.c.setLineWidth(1.4)
                self.c.line(M, self.y, M + LARG, self.y)
            self.c.setStrokeColor(LINE)
            self.c.setLineWidth(0.5)
            self.c.line(M, self.y - alt, M + LARG, self.y - alt)
            x = M
            for (lp, ls, estilo), (_, _, al), lw in zip(info, cols, larguras):
                bold = (negrito or estilo in ("b", "ok")) and not apagada
                cor = MUT if apagada or estilo == "mut" else (TEAL if estilo == "ok" else INK)
                bloco = 9.0 * len(lp) + 7.8 * len(ls)
                yy = self.y - (alt - bloco) / 2 - 7
                for t in lp:
                    if al == "r":
                        self.texto(x + lw - 5, yy, t, F_CEL, bold, cor, "r")
                    else:
                        self.texto(x + 5, yy, t, F_CEL, bold, cor)
                    yy -= 9.0
                for t in ls:
                    self.texto(x + 5, yy + 1, t, F_SUB, cor=MUT)
                    yy -= 7.8
                x += lw
            self.y -= alt

        self.cabe(alt_cab + alt_lin * 2)
        cabecalho()
        for i, cells in enumerate(linhas):
            linha(cells, HL if i in realce else (ZEBRA if i % 2 else None))
        if total:
            linha(total, HL, negrito=True, borda_topo=True)
        for ex in extras:
            linha(ex, None, apagada=True)
        self.y -= 12

    def funil(self, etapas, cores=FUNIL):
        n, alt, ponta = len(etapas), 38, 12
        self.cabe(alt + 12)
        lw = (LARG + (n - 1) * (ponta - 2)) / n
        topo = self.y
        for i, (rot, val) in enumerate(etapas):
            x = M + i * (lw - ponta + 2)
            p = self.c.beginPath()
            p.moveTo(x, topo)
            p.lineTo(x + lw - ponta, topo)
            p.lineTo(x + lw, topo - alt / 2)
            p.lineTo(x + lw - ponta, topo - alt)
            p.lineTo(x, topo - alt)
            if i:
                p.lineTo(x + ponta, topo - alt / 2)
            p.close()
            self.c.setFillColor(cores[i % len(cores)])
            self.c.drawPath(p, stroke=0, fill=1)
            meio = x + (lw + (ponta if i else 0)) / 2 - ponta / 2
            self.texto(meio, topo - 13, rot, 7, cor=white, alinha="c")
            self.texto(meio, topo - 29, val, 13, True, white, "c")
        self.y = topo - alt - 12

    def rosca(self, cx, cy, valores, cores, centro, rot, sub):
        r, ri = 60, 38
        total = sum(max(0.0, v) for _, v in valores) or 1.0
        ang = 90.0
        for k, v in valores:
            if v <= 0:
                continue
            ext = 360.0 * v / total
            self.c.setFillColor(cores[k])
            self.c.wedge(cx - r, cy - r, cx + r, cy + r, ang - ext, ext, stroke=0, fill=1)
            if v / total >= 0.06:
                meio = math.radians(ang - ext / 2)
                self.texto(cx + 49 * math.cos(meio), cy + 49 * math.sin(meio) - 2.2, "%d%%" % round(100 * v / total),
                           6.2, True, white, "c")
            ang -= ext
        self.c.setFillColor(white)
        self.c.circle(cx, cy, ri, stroke=0, fill=1)
        self.texto(cx, cy + 3, centro, 10.5, True, NAVY, "c")
        self.texto(cx, cy - 8, rot, 7, cor=INK, alinha="c")
        self.texto(cx, cy - 16, sub, 5.6, cor=MUT, alinha="c")

    def rodas(self, lista, terceira=("inf", "Capturado", "realizadas no período")):
        t = self.d["tot"]
        cores = {k["nome"]: PAL[i % len(PAL)] for i, k in enumerate(lista)}
        self.cabe(150)
        cy = self.y - 64
        campo3, rot3, sub3 = terceira
        for i, (campo, rot, sub) in enumerate((("v", "Recomendado", "total geral"),
                                               ("pot", "Potencial", "sem reprovadas"), (campo3, rot3, sub3))):
            cx = M + LARG * (i * 2 + 1) / 6.0
            self.rosca(cx, cy, [(k["nome"], float(k.get(campo) or 0)) for k in lista], cores, mil(t[campo]), rot, sub)
        self.y = cy - 74
        linhas, atual, larg_atual = [], [], 0
        for k in lista:
            w = 12 + stringWidth(_txt(k["nome"]), "Helvetica", 7) + 12
            if atual and larg_atual + w > LARG:
                linhas.append((atual, larg_atual))
                atual, larg_atual = [], 0
            atual.append((k["nome"], cores[k["nome"]], w))
            larg_atual += w
        if atual:
            linhas.append((atual, larg_atual))
        for itens_l, larg_l in linhas:
            x = M + (LARG - larg_l) / 2
            for nome, cor, w in itens_l:
                self.c.setFillColor(cor)
                self.c.rect(x, self.y - 1, 7, 7, stroke=0, fill=1)
                self.texto(x + 10, self.y, nome, 7)
                x += w
            self.y -= 11
        self.y -= 6

    def assinatura(self):
        self.cabe(50)
        self.y -= 12
        self.texto(M, self.y, "Atenciosamente,", 9)
        self.texto(M, self.y - 13, "FinOps / Cloud Governance", 9, True)
        self.texto(M, self.y - 26, "Data de referência: " + self.d["ref"], 9, cor=MUT)

    def fechar(self):
        self.rodape()
        self.c.save()
        return self.pagina


# ==================================================================== parcial
class _Parcial(_Pdf):
    def tabela_acomp(self, rotulo, lista):
        t = self.d["tot"]
        cols = [(rotulo, 120, "l"), ("Total", 44, "r"), ("Recomendado", 70, "r"), ("Potencial (s/\nreprovadas)", 70, "r"),
                ("Em\nimplantação", 62, "r"), ("Capturadas", 56, "r"), ("Saving\ncapturado", 64, "r"), ("% do\npotencial", 50, "r")]
        linhas = [[(k["nome"], None, "b"), num(k["n"]), brl(k["v"]), brl(k["pot"]), traco_r(k["vapr"]), traco(k["cap"]),
                   (traco_r(k["inf"]), None, "b"), pct(k["inf"], k["pot"])] for k in lista]
        total = ["Total", num(t["n"]), brl(t["v"]), brl(t["pot"]), brl(t["vapr"]), num(t["cap"]), brl(t["inf"]),
                 pct(t["inf"], t["pot"])]
        self.tabela(cols, linhas, total)

    def desenhar(self):
        d, t = self.d, self.d["tot"]
        self.hero("Acompanhamento parcial de %s · Período: %s" % (d["mes"], d["periodo"]))
        self.titulo("1. Resumo Executivo")
        self.paragrafo("Seguem as atividades de alinhamento com as squads, planejamento e acompanhamento das implementações "
                       "e atualização do status das recomendações na competência de %s, com posição até %s. O saving "
                       "efetivado (validado por custo) será apresentado no fechamento do mês." % (d["mes_nome"], d["ref"]))
        self.y -= 6
        self.cards([
            ("TOTAL RECOMENDADO", brl(t["v"]), "%s recomendações" % num(t["n"]), NAVY),
            ("POTENCIAL (SEM REPROVADAS)", brl(t["pot"]), "%s do recomendado" % pct(t["pot"], t["v"]), ORANGE),
            ("EM IMPLANTAÇÃO", num(t["apr"]), "%s estimados" % brl(t["vapr"]), BLUE),
            ("CAPTURADAS", num(t["cap"]), "%s · %s do potencial" % (brl(t["inf"]), pct(t["inf"], t["pot"])), TEAL),
            ("REPROVADAS", num(t["rep"]), "%s · %s da base" % (brl(t["vrep"]), pct(t["rep"], t["n"])), RED),
        ])
        self.subtitulo("Principais indicadores")
        ind = [("Recomendações em acompanhamento", "saving estimado total", t["n"], t["v"]),
               ("Validação Técnica", "aguardando avaliação das squads", t["ana"], t["vana"]),
               ("Em Implantação", "aprovadas: planejada + em implementação", t["apr"], t["vapr"]),
               ("Capturadas", "implementadas; valor informado pelas squads", t["cap"], t["inf"]),
               ("Reprovadas", "saving estimado reprovado", t["rep"], t["vrep"]),
               ("Adiadas", "saving estimado adiado", t["adi"], t["vadi"]),
               ("Potencial (sem reprovadas)", "recomendado menos as reprovadas", t["n"] - t["rep"], t["pot"])]
        self.tabela([("Indicador", 230, "l"), ("Quantidade", 70, "r"), ("% da base", 64, "r"), ("Valor", 90, "r"),
                     ("% do recomendado", 80, "r")],
                    [[(a, s, "b"), (num(q), None, "b"), pct(q, t["n"]), (brl(v, True), None, "b"), pct(v, t["v"])]
                     for a, s, q, v in ind], realce=(0, 6))
        self.subtitulo("Leitura parcial")
        lider = max(d["squads"], key=lambda s: s["inf"]) if d["squads"] else None
        self.bullets([
            ("Base do mês: ", "%s recomendações em acompanhamento, somando %s estimados." % (num(t["n"]), brl(t["v"]))),
            ("Avaliação: ", "%s (%s) seguem em validação técnica; %s aprovadas estão em implantação (%s)."
             % (num(t["ana"]), pct(t["ana"], t["n"]), num(t["apr"]), brl(t["vapr"]))),
            ("Capturadas: ", "%s recomendações implementadas, com %s informados pelas squads (%s do potencial).%s"
             % (num(t["cap"]), brl(t["inf"]), pct(t["inf"], t["pot"]),
                (" %s lidera, com %s." % (lider["nome"], brl(lider["inf"]))) if lider and lider["inf"] > 0 else "")),
            ("Reprovadas: ", "%s itens (%s)." % (num(t["rep"]), brl(t["vrep"]))),
        ])

        self.nova_pagina()
        self.titulo("2. Funil por Squad")
        self.paragrafo("Distribuição das recomendações por etapa, com o valor recomendado, o potencial e o saving capturado.")
        self.y -= 4
        self.funil([("Validação Técnica", num(t["ana"])), ("Reprovada", num(t["rep"])), ("Adiada", num(t["adi"])),
                    ("Em Implantação", num(t["apr"])), ("Capturada", num(t["cap"]))])
        cols = [("Squad", 106, "l"), ("Total", 38, "r"), ("Validação\nTécnica", 50, "r"), ("Reprovada", 50, "r"),
                ("Adiada", 40, "r"), ("Em\nImplantação", 54, "r"), ("Capturada", 50, "r"), ("Recomendado", 62, "r"),
                ("Potencial", 58, "r"), ("Saving\ncapturado", 58, "r")]
        linhas = [[(s["nome"], s.get("resp") or None, "b"), num(s["n"]), traco(s["ana"]), traco(s["rep"]), traco(s["adi"]),
                   traco(s["apr"]), (traco(s["cap"]), None, "ok"), traco_r(s["v"]), traco_r(s["pot"]),
                   (traco_r(s["inf"]), None, "b")] for s in sorted(d["squads"], key=lambda s: s["nome"].lower())]
        total = ["Total", num(t["n"]), num(t["ana"]), num(t["rep"]), num(t["adi"]), num(t["apr"]), num(t["cap"]),
                 brl(t["v"]), brl(t["pot"]), brl(t["inf"])]
        self.tabela(cols, linhas, total)
        self.paragrafo("Critérios. Validação Técnica: aguardando avaliação/validação técnica da squad · Em Implantação: "
                       "aprovada e ainda não implementada (Planejada ou Em Implementação) · Reprovada: Análise = REPROVADO · "
                       "Adiada: Análise = ADIAR · Capturada: aprovada e Realizado = SIM. Recomendado: saving estimado de "
                       "todas as recomendações · Potencial: recomendado menos as reprovadas · Saving capturado: valor "
                       "informado pelas squads nas capturadas. O responsável exibido sob cada Squad vem da planilha.",
                       tam=6.8, cor=MUT, entre=9)

        self.nova_pagina()
        self.titulo("3. Acompanhamento por Unidade de Negócio")
        self.paragrafo("Recomendado, potencial (sem reprovadas), em implantação e capturado, por BU.")
        bus = sorted(d["bus"], key=lambda b: -b["v"])
        self.rodas(bus)
        self.tabela_acomp("BU", bus)
        self.titulo("3.1 Acompanhamento por Categoria")
        cats = sorted(d["cats"], key=lambda k: -k["v"])
        self.tabela([("Categoria", 190, "l"), ("Total", 46, "r"), ("Capturadas", 56, "r"), ("Estimado", 70, "r"),
                     ("Em\nimplantação", 62, "r"), ("Capturado", 66, "r"), ("Reprovado\n(estimado)", 66, "r")],
                    [[(k["nome"], k.get("desc") or None, "b"), num(k["n"]), traco(k["cap"]), brl(k["v"]), traco_r(k["vapr"]),
                      (traco_r(k["inf"]), None, "b"), traco_r(k["vrep"])] for k in cats],
                    ["Total consolidado", num(t["n"]), num(t["cap"]), brl(t["v"]), brl(t["vapr"]), brl(t["inf"]),
                     brl(t["vrep"])])
        self.paragrafo("Estimado = saving estimado das recomendações · Em implantação = estimado das aprovadas ainda não "
                       "implementadas · Capturado = saving informado pelas squads nas capturadas.", tam=6.8, cor=MUT, entre=9)

        self.nova_pagina()
        self.titulo("4. Acompanhamento por Squad")
        self.paragrafo("Recomendado, potencial (sem reprovadas), em implantação e capturado, por Squad.")
        squads = sorted(d["squads"], key=lambda s: -s["v"])
        self.rodas(squads)
        self.tabela_acomp("Squad", squads)
        self.assinatura()
        return self.fechar()


# ==================================================================== fechamento
class _Fechamento(_Pdf):
    """Mesmo formato do parcial, com o que e de fechamento: saving efetivado (validado por custo) e rescaldo."""

    def tabela_fech(self, rotulo, lista, extras_commit=False):
        t, com = self.d["tot"], self.d.get("commit")
        prox = self.d["prox_curto"]
        cols = [(rotulo, 104, "l"), ("Total", 38, "r"), ("Recomendado", 62, "r"), ("Potencial (s/\nreprovadas)", 62, "r"),
                ("Capturadas", 48, "r"), ("Saving\ncapturado", 58, "r"), ("Saving\nefetivado", 58, "r"),
                ("Rescaldo\n(%s)" % prox, 54, "r"), ("% do\npotencial", 44, "r")]
        linhas = [[(k["nome"], None, "b"), num(k["n"]), brl(k["v"]), brl(k["pot"]), traco(k["cap"]), traco_r(k["inf"]),
                   (traco_r(k["ef"]), None, "b"), traco_r(k["res"]), pct(k["ef"], k["pot"])] for k in lista]
        total = ["Total", num(t["n"]), brl(t["v"]), brl(t["pot"]), num(t["cap"]), brl(t["inf"]), brl(t["ef"]),
                 brl(t["res"]), pct(t["ef"], t["pot"])]
        extras = []
        if extras_commit and com and com["n"]:
            extras.append(["Total sem Commitment", num(t["n"] - com["n"]), brl(t["v"] - com["v"]), brl(t["pot"] - com["pot"]),
                           num(t["cap"] - com["cap"]), brl(t["inf"] - com["inf"]), brl(t["ef"] - com["ef"]),
                           brl(t["res"] - com["res"]), pct(t["ef"] - com["ef"], t["pot"] - com["pot"])])
        self.tabela(cols, linhas, total, extras=extras)

    def desenhar(self):
        d, t, com = self.d, self.d["tot"], self.d.get("commit")
        prox = d["prox_curto"]
        self.hero("Fechamento de %s · Período: %s" % (d["mes"], d["periodo"]))
        self.titulo("1. Resumo Executivo")
        self.paragrafo("Foram conduzidas atividades de alinhamento com as squads, planejamento e acompanhamento das "
                       "implementações e atualização do status das recomendações na competência de %s. O saving efetivado "
                       "e o rescaldo foram validados pelos custos diários das nuvens, conforme o processo de validação dos "
                       "benefícios capturados." % d["mes_nome"])
        self.y -= 6
        self.cards([
            ("TOTAL RECOMENDADO", brl(t["v"]), "%s recomendações" % num(t["n"]), NAVY),
            ("POTENCIAL (SEM REPROVADAS)", brl(t["pot"]), "%s do recomendado" % pct(t["pot"], t["v"]), ORANGE),
            ("CAPTURADAS", num(t["cap"]), "%s informados · %s do potencial" % (brl(t["inf"]), pct(t["inf"], t["pot"])), BLUE),
            ("SAVING EFETIVADO", brl(t["ef"]), "%s do potencial · validado por custo" % pct(t["ef"], t["pot"]), TEAL),
            ("RESCALDO PREVISTO (%s)" % prox.upper(), brl(t["res"]), "benefício recorrente no mês seguinte", RED),
        ])
        self.subtitulo("Principais indicadores")
        ind = [("Recomendações em acompanhamento", "saving estimado total", t["n"], t["v"]),
               ("Validação Técnica", "aguardando avaliação das squads", t["ana"], t["vana"]),
               ("Em Implantação", "aprovadas: planejada + em implementação", t["apr"], t["vapr"]),
               ("Capturadas", "implementadas; valor informado pelas squads", t["cap"], t["inf"]),
               ("Saving efetivado", "capturadas com redução comprovada no custo", t["ef_n"], t["ef"]),
               ("Reprovadas", "saving estimado reprovado", t["rep"], t["vrep"]),
               ("Adiadas", "saving estimado adiado", t["adi"], t["vadi"]),
               ("Potencial (sem reprovadas)", "recomendado menos as reprovadas", t["n"] - t["rep"], t["pot"]),
               ("Rescaldo previsto para %s" % prox, "benefício recorrente das ações implementadas", None, t["res"])]
        self.tabela([("Indicador", 230, "l"), ("Quantidade", 70, "r"), ("% da base", 64, "r"), ("Valor", 90, "r"),
                     ("% do recomendado", 80, "r")],
                    [[(a, s, "b"), (num(q) if q is not None else "–", None, "b"), pct(q, t["n"]) if q is not None else "–",
                      (brl(v, True), None, "b"), pct(v, t["v"])] for a, s, q, v in ind], realce=(0, 4, 7, 8))
        self.subtitulo("Leitura do fechamento")
        lider = max(d["squads"], key=lambda s: s["ef"]) if d["squads"] else None
        cats = sorted(d["cats"], key=lambda k: -k["ef"])
        itens = [
            ("Base do mês: ", "%s recomendações em acompanhamento, somando %s estimados." % (num(t["n"]), brl(t["v"]))),
            ("Avaliação: ", "%s (%s) seguem em validação técnica; %s aprovadas estão em implantação (%s)."
             % (num(t["ana"]), pct(t["ana"], t["n"]), num(t["apr"]), brl(t["vapr"]))),
            ("Capturadas: ", "%s recomendações implementadas, com %s informados pelas squads (%s do potencial)."
             % (num(t["cap"]), brl(t["inf"]), pct(t["inf"], t["pot"]))),
            ("Saving efetivado: ", "%s, equivalente a %s do saving informado. Itens sem redução comprovada no custo "
             "permanecem em R$ 0,00.%s" % (brl(t["ef"]), pct(t["ef"], t["inf"]),
                                           (" %s lidera, com %s." % (lider["nome"], brl(lider["ef"])))
                                           if lider and lider["ef"] > 0 else "")),
        ]
        if cats and cats[0]["ef"] > 0:
            txt = "%s responde por %s (%s) do efetivado." % (cats[0]["nome"], brl(cats[0]["ef"]), pct(cats[0]["ef"], t["ef"]))
            if com and com["ef"] > 0:
                txt += " Sem Commitment, o efetivado é %s (%s do potencial)." % (
                    brl(t["ef"] - com["ef"]), pct(t["ef"] - com["ef"], t["pot"] - com["pot"]))
            itens.append(("Concentração: ", txt))
        itens.append(("Rescaldo: ", "%s projetados para o mês cheio de %s com base nas ações já implementadas."
                      % (brl(t["res"]), d["prox_nome"])))
        itens.append(("Reprovadas: ", "%s itens (%s)." % (num(t["rep"]), brl(t["vrep"]))))
        self.bullets(itens)

        self.nova_pagina()
        self.titulo("2. Funil por Squad")
        self.paragrafo("Distribuição das recomendações por etapa, com o valor recomendado, o saving capturado, o saving "
                       "efetivado e o rescaldo.")
        self.y -= 4
        self.funil([("Validação Técnica", num(t["ana"])), ("Reprovada", num(t["rep"])), ("Adiada", num(t["adi"])),
                    ("Em Implantação", num(t["apr"])), ("Capturada", num(t["cap"]))])
        cols = [("Squad", 98, "l"), ("Total", 34, "r"), ("Validação\nTécnica", 44, "r"), ("Reprovada", 44, "r"),
                ("Adiada", 34, "r"), ("Em\nImplantação", 48, "r"), ("Capturada", 44, "r"), ("Recomendado", 56, "r"),
                ("Saving\ncapturado", 54, "r"), ("Saving\nefetivado", 54, "r"), ("Rescaldo\n(%s)" % prox, 50, "r")]
        linhas = [[(s["nome"], s.get("resp") or None, "b"), num(s["n"]), traco(s["ana"]), traco(s["rep"]), traco(s["adi"]),
                   traco(s["apr"]), (traco(s["cap"]), None, "ok"), traco_r(s["v"]), traco_r(s["inf"]),
                   (traco_r(s["ef"]), None, "b"), traco_r(s["res"])]
                  for s in sorted(d["squads"], key=lambda s: s["nome"].lower())]
        total = ["Total", num(t["n"]), num(t["ana"]), num(t["rep"]), num(t["adi"]), num(t["apr"]), num(t["cap"]),
                 brl(t["v"]), brl(t["inf"]), brl(t["ef"]), brl(t["res"])]
        self.tabela(cols, linhas, total)
        self.paragrafo("Critérios. Validação Técnica: aguardando avaliação/validação técnica da squad · Em Implantação: "
                       "aprovada e ainda não implementada (Planejada ou Em Implementação) · Reprovada: Análise = REPROVADO · "
                       "Adiada: Análise = ADIAR · Capturada: aprovada e Realizado = SIM. Saving capturado: valor informado "
                       "pelas squads nas capturadas · Saving efetivado: validado pela variação do custo diário antes e "
                       "depois da ação · Rescaldo: benefício diário recorrente × dias de %s. O responsável exibido sob cada "
                       "Squad vem da planilha." % d["prox_nome"], tam=6.8, cor=MUT, entre=9)

        self.nova_pagina()
        self.titulo("3. Fechamento por Unidade de Negócio")
        self.paragrafo("Recomendado, potencial (sem reprovadas) e saving efetivado, por BU.")
        bus = sorted(d["bus"], key=lambda b: -b["v"])
        self.rodas(bus, ("ef", "Saving efetivado", "validado por custo"))
        self.tabela_fech("BU", bus, extras_commit=True)
        self.titulo("3.1 Fechamento por Categoria")
        cats_v = sorted(d["cats"], key=lambda k: -k["v"])
        self.tabela([("Categoria", 160, "l"), ("Total", 40, "r"), ("Capturadas", 48, "r"), ("Estimado", 62, "r"),
                     ("Capturado", 60, "r"), ("Efetivado", 60, "r"), ("Rescaldo", 56, "r"), ("Reprovado\n(estimado)", 60, "r")],
                    [[(k["nome"], k.get("desc") or None, "b"), num(k["n"]), traco(k["cap"]), brl(k["v"]), traco_r(k["inf"]),
                      (traco_r(k["ef"]), None, "b"), traco_r(k["res"]), traco_r(k["vrep"])] for k in cats_v],
                    ["Total consolidado", num(t["n"]), num(t["cap"]), brl(t["v"]), brl(t["inf"]), brl(t["ef"]),
                     brl(t["res"]), brl(t["vrep"])])
        self.paragrafo("Estimado = saving estimado das recomendações · Capturado = saving informado pelas squads nas "
                       "capturadas · Efetivado = validado por custo.", tam=6.8, cor=MUT, entre=9)

        self.nova_pagina()
        self.titulo("4. Fechamento por Squad")
        self.paragrafo("Recomendado, potencial (sem reprovadas) e saving efetivado, por Squad.")
        squads = sorted(d["squads"], key=lambda s: -s["v"])
        self.rodas(squads, ("ef", "Saving efetivado", "validado por custo"))
        self.tabela_fech("Squad", squads)

        tops = d.get("top") or {}
        if any(tops.get(k) for k in ("impl", "and", "pend", "rej")):
            self.nova_pagina()
            self.titulo("5. Atualização de Status das Recomendações")

            def rec(x):
                return (x["rec"], "%s %s" % (num(x["n"]), "item" if x["n"] == 1 else "itens"))

            if tops.get("impl"):
                self.subtitulo("Top recomendações implementadas")
                self.tabela([("Recomendação", 210, "l"), ("Estimado", 62, "r"), ("Efetivado", 62, "r"), ("BU", 95, "l"),
                             ("Squad", 95, "l")],
                            [[rec(x), brl(x["v"]), (brl(x["ef"]), None, "b"), lista_curta(x["bu"]), lista_curta(x["sq"])]
                             for x in tops["impl"]])
                self.paragrafo("Aprovadas e efetivadas (Realizado = SIM). Estimado e efetivado somados por tipo de "
                               "recomendação.", tam=6.8, cor=MUT, entre=9)
            for chave, tit in (("and", "Top recomendações em andamento (aprovadas, em implementação)"),
                               ("pend", "Top recomendações pendentes de avaliação"),
                               ("rej", "Top recomendações rejeitadas")):
                if not tops.get(chave):
                    continue
                self.subtitulo(tit)
                self.tabela([("Recomendação", 160, "l"), ("Estimado", 56, "r"), ("BU", 82, "l"), ("Squad", 82, "l"),
                             ("Justificativa", 150, "l")],
                            [[rec(x), brl(x["v"]), lista_curta(x["bu"]), lista_curta(x["sq"]), x.get("obs") or "–"]
                             for x in tops[chave]])
        self.assinatura()
        return self.fechar()


def _gerar(classe, d, cab):
    total = classe(io.BytesIO(), d, 0, cab).desenhar()
    buf = io.BytesIO()
    classe(buf, d, total, cab).desenhar()
    return buf.getvalue()


def gerar_relatorio_parcial(d):
    """d: {mes, mes_nome, periodo, ref, tot{...}, squads[...], bus[...], cats[...]} -> bytes do PDF."""
    return _gerar(_Parcial, d, "Acompanhamento parcial de " + d["mes"])


def gerar_relatorio_fechamento(d):
    """d: {mes, mes_nome, prox_curto, prox_nome, periodo, ref, tot, squads, bus, cats, commit|None,
    top{impl, and, pend, rej}} -> bytes do PDF."""
    return _gerar(_Fechamento, d, "Fechamento de " + d["mes"])
