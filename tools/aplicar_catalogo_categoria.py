"""Aplica o catalogo Classificacao -> Categoria nas competencias ABERTAS.

A Classificacao e a coluna recommendation; a Categoria (coluna categoria) passa
a seguir o catalogo oficial (api.db.CATALOGO_CLASSIFICACAO). Classificacoes fora
do catalogo ficam como estao. Competencias fechadas nao sao tocadas.

Uso:
    python tools/aplicar_catalogo_categoria.py            # so mostra o que mudaria
    python tools/aplicar_catalogo_categoria.py APLICAR    # backup (SQLite) + grava
"""
import json
import os
import shutil
import sys
from collections import Counter
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.db import DB_PATH, categoria_do_catalogo, conectar  # noqa: E402
from api.sqldb import USE_AZURE_SQL  # noqa: E402


def main():
    aplicar = len(sys.argv) > 1 and sys.argv[1] == "APLICAR"
    with conectar() as con:
        fechadas = {r[0] for r in con.execute(
            "SELECT competencia FROM competencias_fechadas WHERE fechada = 1").fetchall()}
        linhas = con.execute(
            "SELECT competencia, opportunity_id, recommendation, categoria, payload_json "
            "FROM recommendations").fetchall()

    mudar, de_para, ignoradas, fora = [], Counter(), Counter(), Counter()
    for comp, oid, classificacao, atual, payload in linhas:
        if '"categoriaManual": true' in (payload or ""):
            continue  # categoria editada na tela: o catalogo nao sobrescreve
        novo = categoria_do_catalogo(classificacao, None)
        if novo is None:
            if comp not in fechadas:
                fora[(comp, classificacao, atual)] += 1
            continue
        if novo == (atual or ""):
            continue
        if comp in fechadas:
            ignoradas[comp] += 1
            continue
        de_para[(comp, classificacao, atual, novo)] += 1
        mudar.append((comp, oid, novo, payload))

    print("Competencias fechadas (nao alteradas):", ", ".join(sorted(fechadas)) or "nenhuma")
    for comp, n in sorted(ignoradas.items()):
        print(f"  {comp}: {n} linha(s) divergentes do catalogo ficam como estao (fechada)")
    for (comp, classificacao, atual, novo), n in sorted(de_para.items()):
        print(f"  {comp}: {classificacao!r}: {atual!r} -> {novo!r}: {n}")
    if fora:
        print("Classificacoes fora do catalogo (mantidas):")
        for (comp, classificacao, atual), n in sorted(fora.items()):
            print(f"  {comp}: {classificacao!r} ({atual!r}): {n}")
    print(f"Total a alterar: {len(mudar)}")

    if not aplicar:
        print("Simulacao. Rode com APLICAR para gravar.")
        return
    if not mudar:
        return

    if not USE_AZURE_SQL:
        destino = str(DB_PATH).replace(".db", f".antes_catalogo_categoria_{datetime.now():%Y%m%d_%H%M%S}.db")
        shutil.copy2(DB_PATH, destino)
        print("Backup:", destino)

    with conectar() as con:
        for comp, oid, novo, payload in mudar:
            try:
                dados = json.loads(payload) if payload else None
            except json.JSONDecodeError:
                dados = None
            if isinstance(dados, dict) and "categoria" in dados:
                dados["categoria"] = novo
                payload = json.dumps(dados, ensure_ascii=False)
            con.execute(
                "UPDATE recommendations SET categoria = ?, payload_json = ? "
                "WHERE competencia = ? AND opportunity_id = ?",
                (novo, payload, comp, oid))
        con.commit()
    print(f"Gravado: {len(mudar)} linha(s).")


if __name__ == "__main__":
    main()
