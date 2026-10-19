# -*- coding: utf-8 -*-
# freeze_competencia.py - congela competencia fechada no SQLite (triggers). ASCII-only.
# A API (api/main.py) ja respeita competencias_fechadas; esta ferramenta so mexe no banco.
# Uso: python tools/freeze_competencia.py SIMULAR|APLICAR <db> <competencia>
import sys, os, sqlite3, datetime

modo, db, comp = sys.argv[1].upper(), sys.argv[2], sys.argv[3]
COLS = ["saving_est", "realizado", "saving", "saving_efetivo", "rescaldo_previsto"]
FECH = "EXISTS (SELECT 1 FROM competencias_fechadas f WHERE f.competencia = {r}.competencia AND f.fechada = 1)"

def sql_triggers():
    ch = " OR ".join("OLD.%s IS NOT NEW.%s" % (c, c) for c in COLS)
    audit_blk = "\n".join(
        "  INSERT INTO recommendation_audit (competencia, opportunity_id, campo, valor_anterior, valor_novo, usuario)\n"
        "  SELECT NEW.competencia, NEW.opportunity_id, '%s', OLD.%s, NEW.%s, 'BLOQUEADO_FECHAMENTO'\n"
        "  WHERE OLD.%s IS NOT NEW.%s;" % (c, c, c, c, c) for c in COLS)
    restore = "  UPDATE recommendations SET " + ", ".join("%s = OLD.%s" % (c, c) for c in COLS) + \
              "\n  WHERE competencia = NEW.competencia AND opportunity_id = NEW.opportunity_id;"
    open_audit_cols = ["realizado", "saving_efetivo", "rescaldo_previsto"]
    open_ch = " OR ".join("OLD.%s IS NOT NEW.%s" % (c, c) for c in open_audit_cols)
    open_blk = "\n".join(
        "  INSERT INTO recommendation_audit (competencia, opportunity_id, campo, valor_anterior, valor_novo, usuario)\n"
        "  SELECT NEW.competencia, NEW.opportunity_id, 'db:%s', OLD.%s, NEW.%s, 'db-trigger'\n"
        "  WHERE OLD.%s IS NOT NEW.%s;" % (c, c, c, c, c) for c in open_audit_cols)
    return [
"""CREATE TABLE IF NOT EXISTS competencias_fechadas (
  competencia TEXT PRIMARY KEY,
  fechada INTEGER NOT NULL DEFAULT 1,
  fechada_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)""",
"DROP TRIGGER IF EXISTS trg_fechamento_bloqueia_update",
"""CREATE TRIGGER trg_fechamento_bloqueia_update
AFTER UPDATE OF %s ON recommendations
WHEN %s AND (%s)
BEGIN
%s
%s
END""" % (", ".join(COLS), FECH.format(r="NEW"), ch, audit_blk, restore),
"DROP TRIGGER IF EXISTS trg_fechamento_bloqueia_delete",
"""CREATE TRIGGER trg_fechamento_bloqueia_delete
BEFORE DELETE ON recommendations
WHEN %s
BEGIN
  SELECT RAISE(ABORT, 'COMPETENCIA FECHADA: exclusao bloqueada');
END""" % FECH.format(r="OLD"),
"DROP TRIGGER IF EXISTS trg_fechamento_bloqueia_insert",
"""CREATE TRIGGER trg_fechamento_bloqueia_insert
BEFORE INSERT ON recommendations
WHEN %s AND NOT EXISTS (SELECT 1 FROM recommendations x WHERE x.competencia = NEW.competencia AND x.opportunity_id = NEW.opportunity_id)
BEGIN
  SELECT RAISE(ABORT, 'COMPETENCIA FECHADA: insercao bloqueada');
END""" % FECH.format(r="NEW"),
"DROP TRIGGER IF EXISTS trg_audit_financeiro_aberta",
"""CREATE TRIGGER trg_audit_financeiro_aberta
AFTER UPDATE OF %s ON recommendations
WHEN NOT %s AND (%s)
BEGIN
%s
END""" % (", ".join(open_audit_cols), FECH.format(r="NEW"), open_ch, open_blk),
]

con = sqlite3.connect(db)
con.row_factory = sqlite3.Row
n = con.execute("SELECT COUNT(*) FROM recommendations WHERE competencia=?", (comp,)).fetchone()[0]
print("competencia %s: %d linhas" % (comp, n))
if n == 0:
    print("ERRO: competencia sem linhas; abortando"); sys.exit(1)
if not con.execute("SELECT 1 FROM sqlite_master WHERE name='recommendation_audit'").fetchone():
    print("ERRO: tabela recommendation_audit nao existe (abra o banco pela API: o schema.sql cria a tabela)"); sys.exit(1)
if modo != "APLICAR":
    print("SIMULAR: nada foi alterado. Rode com APLICAR (servidor parado).")
    sys.exit(0)

ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
bk = os.path.join(os.path.dirname(db), "finops_dev.before_freeze_%s.db" % ts)
b = sqlite3.connect(bk); con.backup(b); b.close()
print("backup:", bk)

con.isolation_level = None
con.execute("BEGIN IMMEDIATE")
for s in sql_triggers():
    con.execute(s)
con.execute("INSERT OR IGNORE INTO competencias_fechadas (competencia, fechada) VALUES (?, 1)", (comp,))
con.execute("UPDATE competencias_fechadas SET fechada = 1 WHERE competencia = ?", (comp,))
con.execute("COMMIT")

# auto-teste dentro de transacao com rollback
con.execute("BEGIN")
r = con.execute("SELECT opportunity_id, saving_efetivo, rescaldo_previsto FROM recommendations WHERE competencia=? LIMIT 1", (comp,)).fetchone()
oid, ef0, rs0 = r[0], r[1], r[2]
con.execute("UPDATE recommendations SET saving_efetivo = COALESCE(saving_efetivo,0) + 123.45, rescaldo_previsto = COALESCE(rescaldo_previsto,0) + 9 WHERE competencia=? AND opportunity_id=?", (comp, oid))
r2 = con.execute("SELECT saving_efetivo, rescaldo_previsto FROM recommendations WHERE competencia=? AND opportunity_id=?", (comp, oid)).fetchone()
ok_upd = (r2[0] == ef0 and r2[1] == rs0)
try:
    con.execute("DELETE FROM recommendations WHERE competencia=? AND opportunity_id=?", (comp, oid)); ok_del = False
except sqlite3.DatabaseError:
    ok_del = True
try:
    con.execute("INSERT INTO recommendations (competencia, opportunity_id) VALUES (?, 'ZZZ-TESTE')", (comp,)); ok_ins = False
except sqlite3.DatabaseError:
    ok_ins = True
con.execute("ROLLBACK")
print("auto-teste: update bloqueado=%s delete bloqueado=%s insert bloqueado=%s" % (ok_upd, ok_del, ok_ins))

print("Para desbloquear (manutencao): UPDATE competencias_fechadas SET fechada=0 WHERE competencia='%s';" % comp)
if not (ok_upd and ok_del and ok_ins):
    print("ATENCAO: auto-teste falhou; restaure o backup acima."); sys.exit(2)
