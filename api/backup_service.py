import datetime
import os
import sqlite3
import threading
import time
from pathlib import Path


def _fazer_backup(db_path, pasta, manter):
    pasta.mkdir(parents=True, exist_ok=True)
    nome = "finops_%s.db" % datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    destino = pasta / nome
    src = sqlite3.connect(str(db_path), timeout=30)
    dst = sqlite3.connect(str(destino))
    try:
        src.backup(dst)
    finally:
        dst.close()
        src.close()
    antigos = sorted(pasta.glob("finops_*.db"))
    for f in antigos[:-manter]:
        try:
            f.unlink()
        except OSError:
            pass
    return destino


def _ultimo_backup_ts(pasta):
    arqs = sorted(pasta.glob("finops_*.db"))
    return arqs[-1].stat().st_mtime if arqs else 0


def iniciar_backup_periodico(db_path):
    if os.getenv("FINOPS_BACKUP", "") != "1":
        return
    db_path = Path(db_path)
    pasta = Path(os.getenv("FINOPS_BACKUP_DIR", str(db_path.parent / "backups")))
    horas = float(os.getenv("FINOPS_BACKUP_HORAS", "6"))
    manter = int(os.getenv("FINOPS_BACKUP_MANTER", "20"))

    def laco():
        while True:
            try:
                if time.time() - _ultimo_backup_ts(pasta) >= horas * 3600:
                    _fazer_backup(db_path, pasta, manter)
            except Exception as e:
                print("[backup] falhou:", e)
            time.sleep(600)

    threading.Thread(target=laco, daemon=True).start()
