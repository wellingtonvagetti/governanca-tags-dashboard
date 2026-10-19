# -*- coding: utf-8 -*-
# tags_carregar_base.py - grava a base do modulo Governanca de Tags na pasta de dados (fora do repositorio). ASCII-only.
# A base vem do dashboard original de tags (dashboard.html.gz.b64 ou o .html descompactado):
#   baseline.json.gz   fotografia exibida antes da 1a gravacao pela tela
#   historico.json.gz  base historica da aba de evolucao
#   subscriptions-master.json (opcional) cadastro corporativo de subscriptions
# Uso:
#   python tools\tags_carregar_base.py <dashboard.html.gz.b64|dashboard.html> [subscriptions-master.json] [pasta_destino]
# Pasta padrao: FINOPS_TAGS_DATA_DIR, ou data\modulos\tags (local). Nao apaga fotografias ja gravadas.
import base64, gzip, json, os, re, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from api.modulo_tags import diretorio_dados


def ler_html(caminho):
    bruto = open(caminho, "rb").read()
    if caminho.endswith(".b64"):
        bruto = gzip.decompress(base64.b64decode(re.sub(rb"\s+", b"", bruto)))
    return bruto.decode("utf-8")


def bloco(html, ident):
    m = re.search(r'<script id="%s" type="application/json">(.*?)</script>' % ident, html, re.S)
    if not m:
        raise SystemExit("bloco %s nao encontrado no dashboard" % ident)
    return json.loads(m.group(1))


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__ or "uso: tags_carregar_base.py <dashboard> [subscriptions.json] [pasta]")
    html = ler_html(sys.argv[1])
    subs = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] else None
    pasta = sys.argv[3] if len(sys.argv) > 3 else str(diretorio_dados())
    os.makedirs(pasta, exist_ok=True)
    base, hist = bloco(html, "data"), bloco(html, "historyData")
    for nome, valor in (("baseline.json.gz", base), ("historico.json.gz", hist)):
        with open(os.path.join(pasta, nome), "wb") as f:
            f.write(gzip.compress(json.dumps(valor, ensure_ascii=False).encode("utf-8"), 9))
    print("baseline: %d recursos | historico: %s" % (len(base.get("R", {}).get("id", [])), ", ".join(sorted(hist))))
    if subs:
        lista = json.load(open(subs, encoding="utf-8"))
        with open(os.path.join(pasta, "subscriptions-master.json"), "w", encoding="utf-8") as f:
            json.dump(lista, f, ensure_ascii=False, indent=2)
        print("subscriptions: %d" % len(lista))
    print("gravado em %s" % pasta)


if __name__ == "__main__":
    main()
