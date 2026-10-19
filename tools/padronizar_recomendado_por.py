"""Padroniza o campo "Identificado por" (coluna recomendado_por) nas competencias ABERTAS.

Evertec, Solo, Dedalus e Evertec Latam (qualquer LATAM vira Evertec Latam).
Competencias fechadas nao sao tocadas.

Uso:
    python tools/padronizar_recomendado_por.py            # so mostra o que mudaria
    python tools/padronizar_recomendado_por.py APLICAR    # backup (SQLite) + grava
"""
import json
import os
import shutil
import sys
from collections import Counter
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.db import DB_PATH, conectar, padronizar_recomendado_por  # noqa: E402
from api.sqldb import USE_AZURE_SQL  # noqa: E402


def main():
    aplicar = len(sys.argv) > 1 and sys.argv[1] == "APLICAR"
    with conectar() as con:
        fechadas = {r[0] for r in con.execute(
            "SELECT competencia FROM competencias_fechadas WHERE fechada = 1").fetchall()}
        linhas = con.execute(
            "SELECT competencia, opportunity_id, recomendado_por, payload_json FROM recommendations").fetchall()

    mudar, de_para, ignoradas = [], Counter(), Counter()
    for comp, oid, atual, payload in linhas:
        novo = padronizar_recomendado_por(atual)
        if (novo or "") == (atual or ""):
            continue
        if comp in fechadas:
            ignoradas[comp] += 1
            continue
        de_para[(comp, atual, novo)] += 1
        mudar.append((comp, oid, novo, payload))

    print("Competencias fechadas (nao alteradas):", ", ".join(sorted(fechadas)) or "nenhuma")
    for comp, n in sorted(ignoradas.items()):
        print(f"  {comp}: {n} linha(s) fora do padrao ficam como estao (fechada)")
    for (comp, atual, novo), n in sorted(de_para.items()):
        print(f"  {comp}: {atual!r} -> {novo!r}: {n}")
    print(f"Total a alterar: {len(mudar)}")

    if not aplicar:
        print("Simulacao. Rode com APLICAR para gravar.")
        return
    if not mudar:
        return

    if not USE_AZURE_SQL:
        destino = str(DB_PATH).replace(".db", f".antes_recomendado_por_{datetime.now():%Y%m%d_%H%M%S}.db")
        shutil.copy2(DB_PATH, destino)
        print("Backup:", destino)

    with conectar() as con:
        for comp, oid, novo, payload in mudar:
            try:
                dados = json.loads(payload) if payload else None
            except json.JSONDecodeError:
                dados = None
            if isinstance(dados, dict) and "recomendadoPor" in dados:
                dados["recomendadoPor"] = novo
                payload = json.dumps(dados, ensure_ascii=False)
            con.execute(
                "UPDATE recommendations SET recomendado_por = ?, payload_json = ? "
                "WHERE competencia = ? AND opportunity_id = ?",
                (novo, payload, comp, oid))
        con.commit()
    print(f"Gravado: {len(mudar)} linha(s).")


if __name__ == "__main__":
    main()
