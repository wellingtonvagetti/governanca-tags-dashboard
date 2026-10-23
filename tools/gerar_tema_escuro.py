# -*- coding: utf-8 -*-
"""Gera o tema escuro (botao LIGHT/DARK) de Recomendacoes a partir do CSS do proprio frontend/index.html.

Cada cor do CSS vira a equivalente escura pela categoria da propriedade (fundo, texto, borda), na paleta do
modulo de Tags; as cores fixas do JavaScript (estilos inline e --cor) ganham regras por seletor de atributo.
Rodar de novo sempre que o CSS de Recomendacoes mudar cores. ASCII-only.
Uso: python tools/gerar_tema_escuro.py frontend/index.html   (substitui o bloco <style id="tema-escuro-v5">)"""
import colorsys
import re
import sys

ARQ = sys.argv[1]
s = open(ARQ, encoding="utf-8").read()
INI, FIM = '<style id="tema-escuro-v5">', "</style>"
if INI in s:
    a = s.index(INI)
    s = s[:a] + s[s.index(FIM, a) + len(FIM) + 1:]
head = s[:s.index("</head>")]
blocos = re.findall(r'<style(?: id="([^"]*)")?>(.*?)</style>', head, re.S)
css = "".join(c for ident, c in blocos if ident not in ("topo-padrao-modulos-v5",))
css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)

COR = re.compile(r"#[0-9a-fA-F]{3,8}\b|rgba?\([^)]*\)")


def parse(c):
    c = c.strip()
    if c.startswith("#"):
        h = c[1:]
        if len(h) in (3, 4):
            h = "".join(x * 2 for x in h)
        r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
        a = int(h[6:8], 16) / 255 if len(h) == 8 else None
        return r, g, b, a
    n = [x.strip() for x in c[c.index("(") + 1:-1].replace("/", ",").split(",")]
    r, g, b = (float(x.rstrip("%")) * (2.55 if x.endswith("%") else 1) for x in n[:3])
    a = float(n[3]) if len(n) > 3 and n[3] else None
    return r, g, b, a


def fmt(r, g, b, a):
    r, g, b = (max(0, min(255, round(x))) for x in (r, g, b))
    if a is None:
        return "#%02x%02x%02x" % (r, g, b)
    return "rgba(%d,%d,%d,%s)" % (r, g, b, ("%.3f" % a).rstrip("0").rstrip("."))


def hls(r, g, b):
    return colorsys.rgb_to_hls(r / 255, g / 255, b / 255)


def rgb(h, l, s_):
    return tuple(x * 255 for x in colorsys.hls_to_rgb(h, l, s_))


def fundo(c):
    r, g, b, a = parse(c)
    h, l, s_ = hls(r, g, b)
    if a is not None and a < 0.5:
        return None                      # veus translucidos: mantem
    if l >= 0.86:                         # superficies claras -> superficies escuras (Tags: #111218 / #191b23)
        if s_ < 0.25:                     # neutras: tom levemente azulado das superficies de Tags
            h, ns = 0.64, 0.14
        else:                             # tingidas (verde/laranja/vermelho claro): mesmo tom, escuro
            ns = min(s_, 0.5) * 0.55
        nl = 0.068 + (1 - l) * 0.75
        return fmt(*rgb(h, nl, ns), a)
    return None


def texto(c):
    r, g, b, a = parse(c)
    h, l, s_ = hls(r, g, b)
    if l < 0.5 and s_ < 0.5:              # texto escuro neutro/navy -> claro neutro (Tags: #f5f7fa / #b9c0ca)
        return fmt(*rgb(0.6, 0.965 - l * 0.55, 0.12), a)
    if l < 0.5:                           # texto colorido escuro (status) -> mesma cor, mais clara
        return fmt(*rgb(h, max(0.64, l + 0.28), min(1, s_ * 0.9)), a)
    return None


def borda(c):
    r, g, b, a = parse(c)
    h, l, s_ = hls(r, g, b)
    if l >= 0.78 and s_ < 0.5:            # bordas claras -> #303440
        return fmt(*rgb(h, 0.16 + (1 - l) * 0.45, min(s_, 0.12)), a)
    if l >= 0.86:
        return fmt(*rgb(h, 0.22, min(s_, 0.45)), a)
    return None


def categoria(prop):
    if prop.startswith("background") or prop in ("fill",):
        return fundo
    if prop in ("color", "caret-color", "-webkit-text-fill-color"):
        return texto
    if prop.startswith("border") or prop.startswith("outline") or prop in ("stroke", "column-rule"):
        return borda
    return None


def converte_decl(prop, val):
    f = categoria(prop)
    if not f:
        return None
    mudou = False

    def troca(m):
        nonlocal mudou
        novo = f(m.group(0))
        if novo:
            mudou = True
            return novo
        return m.group(0)
    novo = COR.sub(troca, val)
    if not mudou and re.search(r"\b(white)\b", val) and f is fundo:
        novo, mudou = re.sub(r"\bwhite\b", "#111218", val), True
    return f"{prop}:{novo.strip()}" if mudou else None


def prefixa(sel):
    out = []
    for p in re.split(r",(?![^(]*\))", sel):
        p = p.strip()
        if not p or p.startswith("@"):
            continue
        if re.match(r"^(html|:root)\b", p):
            continue
        if re.match(r"^body\b", p):
            out.append("body.dark-theme" + p[4:])
        else:
            out.append("body.dark-theme " + p)
    return ",".join(out)


def varre(texto_css):
    """Gera regras escuras; preserva @media (exceto print)."""
    saida, i, n = [], 0, len(texto_css)
    while i < n:
        j = texto_css.find("{", i)
        if j < 0:
            break
        sel = texto_css[i:j].strip()
        if sel.startswith("@media") or sel.startswith("@supports"):
            prof, k = 1, j + 1
            while prof and k < n:
                prof += {"{": 1, "}": -1}.get(texto_css[k], 0)
                k += 1
            interno = varre(texto_css[j + 1:k - 1])
            if interno and "print" not in sel:
                saida.append(sel + "{" + interno + "}")
            i = k
            continue
        if sel.startswith("@"):
            prof, k = 1, j + 1
            while prof and k < n:
                prof += {"{": 1, "}": -1}.get(texto_css[k], 0)
                k += 1
            i = k
            continue
        k = texto_css.find("}", j)
        decls = texto_css[j + 1:k]
        i = k + 1
        novas = []
        for d in decls.split(";"):
            if ":" not in d:
                continue
            prop, val = d.split(":", 1)
            prop = prop.strip().lower()
            if prop.startswith("--"):
                continue
            imp = "!important" in val
            r = converte_decl(prop, val.replace("!important", ""))
            if r:
                novas.append(r + ("!important" if imp else ""))
        ps = prefixa(sel)
        if novas and ps:
            saida.append(ps + "{" + ";".join(novas) + "}")
    return "".join(saida)


# variaveis de cor (redefinidas no body.dark-theme)
vars_ = {}
for m in re.finditer(r"(--[a-z0-9-]+)\s*:\s*(#[0-9a-fA-F]{3,8}|rgba?\([^)]*\))", css):
    nome, val = m.group(1), m.group(2)
    if any(k in nome for k in ("bg", "card", "line", "input", "soft")):
        novo = fundo(val) if not ("line" in nome or "input" in nome) else borda(val)
    elif any(k in nome for k in ("text", "ink", "muted", "dark", "gray")):
        novo = texto(val)
    else:
        novo = None
    if novo:
        vars_[nome] = novo

regras = varre(css)

# cores fixas usadas pelo JavaScript em estilos inline (templates) e na variavel --cor dos cartoes
corpo = s[s.index("</head>"):]
hexes = sorted({m.upper() for m in re.findall(r"#(?:[0-9A-Fa-f]{6}|[0-9A-Fa-f]{3})(?![0-9A-Fa-f])", corpo)})


def dado(c):
    """Cor de dado (barra, faixa): so clareia as muito escuras para aparecerem no fundo escuro."""
    r, g, b, a = parse(c)
    h, l, s_ = hls(r, g, b)
    if l < 0.3:
        return fmt(*rgb(h, 0.48, max(s_, 0.25) if s_ > 0.05 else s_), a)
    return None


inline = []
for H in hexes:
    alvo = []
    for prefixo, func, prop in (("color:", texto, "color"), ("--cor:", texto, "--cor"),
                                ("background:", None, "background"), ("background-color:", None, "background-color")):
        if func is None:
            novo = fundo(H) or dado(H)
        else:
            novo = func(H)
        if novo:
            sel = ",".join(f'body.dark-theme [style*="{prefixo}{H}" i],body.dark-theme [style*="{prefixo} {H}" i]' for _ in (0,))
            inline.append(f"{sel}{{{prop}:{novo}!important}}")
regras += "".join(inline)
vars_.update({"--cv-navy": "#4a6a93", "--navy": "#4a6a93", "--navy-2": "#3c5878"})
base = (
    "body.dark-theme{color-scheme:dark;background:#0d0e13!important;color:#f5f7fa;"
    + ";".join(f"{k}:{v}" for k, v in vars_.items()) + "}"
    "body.dark-theme:before{content:\"\";position:fixed;inset:0;background:linear-gradient(rgba(8,9,13,.30),rgba(8,9,13,.45)),"
    "url('/plataforma/fundo-evertec-escuro.svg') center/cover no-repeat;pointer-events:none;z-index:-1}"
    "body.dark-theme .topbar{background:rgba(7,8,12,.97)!important;box-shadow:0 5px 22px rgba(0,0,0,.35)}"
    "body.dark-theme input,body.dark-theme select,body.dark-theme textarea{color-scheme:dark}"
    "body.dark-theme .corporate-footer{background:rgba(7,8,12,.97)}"
    # faixas grandes que usam o navy como fundo continuam escuras (o navy claro e para barras/botoes)
    "body.dark-theme .tk-sla-v5{background:#13283F}"
)
bloco = INI + "\n/* Tema escuro (LIGHT/DARK) gerado a partir do CSS desta pagina, na paleta do modulo de Tags. */\n" + base + "\n" + regras + "\n" + FIM + "\n"
pos = s.index("</head>")
s = s[:pos] + bloco + s[pos:]
open(ARQ, "w", encoding="utf-8", newline="\n").write(s)
print("variaveis:", len(vars_), "| regras:", regras.count("{"), "| bytes:", len(bloco))
