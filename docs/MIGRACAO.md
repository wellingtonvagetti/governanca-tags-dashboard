# Checklist de migracao para outra organizacao

Objetivo: levar o dashboard para o GitHub/Azure da empresa sem carregar dados pessoais, dados reais indevidos ou configuracao presa a conta pessoal.

## 1. Repositorio
- [ ] Criar o repo novo na organizacao (privado) e subir SEM o historico antigo: `git clone --depth 1` + novo `git init`, ou `git filter-repo`.
  - Motivo: o historico contem `api/main.py.bak_encoding_*` e `frontend/index.html.bak_encoding_*` (backups ja removidos, mas ainda no historico) e 23 commits com e-mail pessoal.
- [ ] Conferir `.gitignore` (dados reais, *.csv, *.xlsx, *.db, backups ja ignorados).
- [ ] Nao versionar banco real, custos, planilhas oficiais nem `config/squads.json`.

## 2. Dados e configuracao no codigo
- [ ] `frontend/index.html` traz tabela de squads com responsaveis tecnicos como valores padrao (secao Configuracoes). Decidir: manter como padrao da empresa ou mover para `config/squads.json` carregado pela API.
- [x] E-mails pessoais do autor removidos do padrao de squads (V337). Conferir com: `grep -n "@gmail.com" frontend/index.html` (deve voltar vazio).
- [ ] `.env.example` tem `LOGIC_APP_URL` vazio: criar o Logic App na empresa e preencher no ambiente (nunca no repo).

## 3. Variaveis de ambiente
| Variavel | Uso |
|---|---|
| FINOPS_REQUIRE_AUTH=1 | exige identidade (Easy Auth / SSO) |
| FINOPS_SQL_SERVER, FINOPS_SQL_DB, FINOPS_SQL_USER, FINOPS_SQL_PASSWORD | Azure SQL (sem `FINOPS_SQL_SERVER` o dash usa SQLite) |
| FINOPS_SQL_RETRIES, FINOPS_SQL_RETRY_S, FINOPS_SQL_TDS, FINOPS_SQL_PORT | conexao com Azure SQL (tentativas, espera, protocolo, porta) |
| FINOPS_RECS_CACHE_TTL_S | validade do cache de recomendacoes (padrao 300 s) |
| LOGIC_APP_URL | envio de e-mail (Logic App) |
| FINOPS_EMAIL_OVERRIDE_TO | manda todo e-mail so para esse endereco (teste); remover para valer |
| FINOPS_EMAIL_TIMEOUT | tempo limite do envio de e-mail |
| FINOPS_DB_PATH | caminho do SQLite (so no modo SQLite; default `database/finops_dev.db`) |
| FINOPS_BACKUP=1, FINOPS_BACKUP_DIR, _HORAS, _MANTER | backup automatico do SQLite (nao vale com Azure SQL) |

## 4. Python
- [ ] `requirements.txt` fixado (testado em Python 3.13 local). Validar o build no Python do destino (App Service usava 3.12) antes de confiar.

## 5. Publicacao (so no tenant da empresa)
- [ ] App Service + Easy Auth (SSO corporativo) + `FINOPS_REQUIRE_AUTH=1`.
- [ ] CI/CD por GitHub Actions com OIDC (sem senha), deploy a partir da branch principal.
- [ ] Slots exigem tier Standard; SQLite fica em armazenamento separado por slot. Para varios usuarios ou slots, migrar para Postgres/Azure SQL.
- [ ] Persistir o banco fora do pacote de deploy (volume /home) e fazer backup.

## 6. Validacao apos subir
- [ ] `python tools/verifica_numeros.py VERIFICAR <db> 2026-09` deve dar OK (competencia fechada identica ao golden).
- [ ] Conferir triggers de fechamento (`triggers_fechamento = 3`) no banco novo.
- [ ] Rodar "Conferir com a oficial" com a planilha oficial do mes.

## 7. Nao fazer
- Nao copiar dados reais para conta pessoal (Azure/GitHub pessoal).
- Nao reaproveitar a POC: recriar infraestrutura na empresa.
