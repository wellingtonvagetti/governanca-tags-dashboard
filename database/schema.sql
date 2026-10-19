CREATE TABLE IF NOT EXISTS recommendations (
    competencia TEXT NOT NULL,
    opportunity_id TEXT NOT NULL,

    recommendation TEXT,
    item TEXT,
    ambiente TEXT,
    rg TEXT,
    subscription TEXT,
    bu TEXT,
    categoria TEXT,
    fonte TEXT,
    recomendado_por TEXT,

    data_recomendada TEXT,
    data_atualizacao TEXT,

    saving_est REAL NOT NULL DEFAULT 0,
    realizado INTEGER NOT NULL DEFAULT 0,

    ticket TEXT,
    data_prevista TEXT,
    data_efetivada TEXT,

    saving REAL NOT NULL DEFAULT 0,
    saving_efetivo REAL NOT NULL DEFAULT 0,
    rescaldo_previsto REAL NOT NULL DEFAULT 0,

    analise TEXT,
    observacao TEXT,

    squad TEXT,
    responsavel TEXT,
    responsavel_tecnico TEXT,

    provider TEXT,

    calc_note TEXT,
    calc_method TEXT,

    payload_json TEXT NOT NULL,

    PRIMARY KEY (competencia, opportunity_id)
);

CREATE INDEX IF NOT EXISTS idx_rec_competencia
ON recommendations (competencia);

CREATE INDEX IF NOT EXISTS idx_rec_provider
ON recommendations (competencia, provider);

CREATE INDEX IF NOT EXISTS idx_rec_squad
ON recommendations (competencia, squad);

CREATE INDEX IF NOT EXISTS idx_rec_categoria
ON recommendations (competencia, categoria);

CREATE INDEX IF NOT EXISTS idx_rec_analise
ON recommendations (competencia, analise);

CREATE TABLE IF NOT EXISTS database_metadata (
    chave TEXT PRIMARY KEY,
    valor TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS recommendation_audit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    competencia TEXT NOT NULL,
    opportunity_id TEXT NOT NULL,

    campo TEXT NOT NULL,
    valor_anterior TEXT,
    valor_novo TEXT,

    usuario TEXT NOT NULL DEFAULT 'dev-local',

    alterado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_opportunity
ON recommendation_audit (competencia, opportunity_id);

CREATE INDEX IF NOT EXISTS idx_audit_data
ON recommendation_audit (alterado_em);

CREATE TABLE IF NOT EXISTS app_state (
    state_key TEXT PRIMARY KEY,
    state_value TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS cost_records (
    record_key TEXT PRIMARY KEY,
    provider TEXT NOT NULL,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    source_type TEXT NOT NULL DEFAULT 'ID_HISTORY',
    file_name TEXT NOT NULL DEFAULT '',
    content_text TEXT NOT NULL,
    saved_at TEXT NOT NULL,
    UNIQUE (provider, year, month, source_type)
);

CREATE INDEX IF NOT EXISTS idx_cost_records_period
ON cost_records (year, month, provider);

-- Competencias fechadas: os triggers que congelam os valores financeiros sao
-- criados por tools/freeze_competencia.py (SQLite) ou pelo migrador (--triggers).
CREATE TABLE IF NOT EXISTS competencias_fechadas (
    competencia TEXT PRIMARY KEY,
    fechada INTEGER NOT NULL DEFAULT 1,
    fechada_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
