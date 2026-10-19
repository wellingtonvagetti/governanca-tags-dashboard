# Azure SQL (opcional)

O dash continua em SQLite por padrao. O Azure SQL so entra quando o app tem a variavel
`FINOPS_SQL_SERVER` (appsettings: `FINOPS_SQL_SERVER`, `FINOPS_SQL_DB`, `FINOPS_SQL_USER`,
`FINOPS_SQL_PASSWORD`). Sem ela, nada muda.

## Como funciona
- `api/sqldb.py`: camada de dialeto. Traduz o SQL do dash (`?`, aspas duplas, `LENGTH`,
  `BEGIN IMMEDIATE`, `CREATE ... IF NOT EXISTS`, `PRAGMA`) e implementa `upsert` (MERGE no Azure SQL).
- Esquema e dados: `tools/migrar_sqlite_para_azure_sql.py` (le o SQLite, cria as tabelas,
  copia e confere contagens, assinatura do conteudo e somas por competencia).
- Backup periodico em disco fica desligado com Azure SQL (o servico tem backup proprio).
- Conexao com nova tentativa (FINOPS_SQL_RETRIES x FINOPS_SQL_RETRY_S) para banco pausado.

## Limites conhecidos
- O Azure SQL roda na POC (Basic, Central US). A latencia ate a regiao domina o tempo das paginas; na empresa, usar uma regiao proxima (ex.: Brazil South).
- Colunas de texto indexadas (competencia, squad, provider, categoria, analise) ficam em
  NVARCHAR(200); chaves de coluna unica em NVARCHAR(450).
- Collation padrao do Azure SQL e case-insensitive; no SQLite comparacoes `=` diferenciam maiusculas.
- Triggers de competencia fechada: `--triggers` no migrador (testar depois da carga).
- `tools/verifica_numeros.py` e `freeze_competencia.py` continuam so SQLite.
