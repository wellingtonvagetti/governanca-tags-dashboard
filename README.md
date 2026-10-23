<div align="center">

# 📊 Dashboard FinOps

**Plataforma FinOps com módulos: recomendações de eficiência financeira em ambientes multicloud (da identificação à captura do saving), governança de tags e auditoria de tags de VMs.**

[![CI](https://github.com/rafabiasotto/dash-finops/actions/workflows/ci.yml/badge.svg)](https://github.com/rafabiasotto/dash-finops/actions/workflows/ci.yml)
[![Deploy POC](https://github.com/rafabiasotto/dash-finops/actions/workflows/deploy-poc.yml/badge.svg)](https://github.com/rafabiasotto/dash-finops/actions/workflows/deploy-poc.yml)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![Azure](https://img.shields.io/badge/Azure-App%20Service%20%7C%20SQL-0078D4?logo=microsoftazure&logoColor=white)
![Multicloud](https://img.shields.io/badge/Azure%20%C2%B7%20AWS%20%C2%B7%20GCP%20%C2%B7%20OCI-555555)

[Funcionalidades](#funcionalidades) · [Execução local](#execução-local) · [Processo mensal](#processo-mensal) · [Publicação](#publicação-e-infraestrutura-da-poc) · [Roadmap](#roadmap)

</div>

---

Centraliza recomendações, acompanhamento por Squad, custos, **Saving Efetivo**, **Rescaldo** e SLAs do processo FinOps, além da governança de tags do Azure. Os dados de recomendações ficam num banco SQLite (uso local) ou no Azure SQL (POC e empresa); os de tags ficam em arquivos no armazenamento do App Service.

## Sumário

- [Visão geral](#visão-geral)
- [Funcionalidades](#funcionalidades)
- [Estrutura do repositório](#estrutura-do-repositório)
- [Execução local](#execução-local)
- [Variáveis de ambiente](#variáveis-de-ambiente)
- [Processo mensal](#processo-mensal)
- [Módulos Governança de Tags e Auditoria de VMs](#módulos-governança-de-tags-e-auditoria-de-vms)
- [Custos](#custos)
- [Competências fechadas](#competências-fechadas)
- [Backup](#backup)
- [Princípios de desenvolvimento](#princípios-de-desenvolvimento)
- [Publicação e infraestrutura da POC](#publicação-e-infraestrutura-da-poc)
- [Levar para outra organização](#levar-para-outra-organização)
- [Versionamento](#versionamento)
- [Roadmap](#roadmap)

## Visão geral

- **Plataforma:** página inicial (`frontend/inicio.html`) com os módulos e um seletor "Módulo" comum no topo de todas as páginas (`frontend/plataforma/`).
- **Módulos:**

  | Rota | Módulo | Tela | Dados |
  |---|---|---|---|
  | `/` | Início | `frontend/inicio.html` | — |
  | `/recomendacoes` | Recomendações FinOps | `frontend/index.html` (arquivo único) | SQLite / Azure SQL |
  | `/tags` | Governança de Tags | `modulos/tags/` | arquivos em `FINOPS_TAGS_DATA_DIR` |
  | `/auditoria-vms` | Auditoria de Tags de VMs | `modulos/tags/` (mesma fotografia de Tags) | idem |

- **Visual comum:** topo com logo, título, botões **LIGHT** (tema escuro) e **FONTE** (normal, grande e extra grande), seletor de módulo e abas em caixa alta. Tema e fonte ficam gravados no navegador (`governanca-theme` / `governanca-font`) e valem para todos os módulos.
- **API:** FastAPI (`api/`), responsável por ler, gravar e validar os dados de todos os módulos.
- **Banco:** fonte oficial dos dados. Local: SQLite (`database/finops_dev.db`). POC: Azure SQL, ligado pelas variáveis `FINOPS_SQL_*`. O navegador guarda apenas cache; se houver divergência, vale o banco.

```mermaid
flowchart LR
    U["👤 Navegador<br/>módulos"] --> A["⚙️ API<br/>FastAPI"]
    A --> L[("SQLite<br/>local")]
    A --> Z[("Azure SQL<br/>POC / empresa")]
    A --> T[("Arquivos de tags<br/>/home/data/modulos/tags")]
    A -->|e-mail| G["Logic App"]
    C["Exports de custos<br/>e recomendações"] -->|importação| A
```

## Funcionalidades

| Área | O que faz |
|---|---|
| Recomendações | Cadastro, status (análise, aprovada, reprovada, adiada), realizado, tickets e IDs `FINOPS-xxxxxx` |
| Importação | "Novas recomendações" (exports brutos) e "Atualizar planilha" (planilha oficial), sempre com prévia |
| Indicadores | Potencial, Saving Est., Saving Efetivo, Rescaldo previsto e herdado, eficiência |
| Squads e SLA | Visão por Squad, chamados, prazos e envio de e-mail |
| Custos | Exports por competência e provedor, usados nos cálculos |
| Governança | Competências fechadas, auditoria de alterações e backup automático |
| Governança de Tags | Qualidade e classificação das tags dos recursos elegíveis, FinOps BU × CC, evolução, detalhamento e importação de fotografias (CSV do Resource Graph) |
| Auditoria de Tags de VMs | Conformidade das tags obrigatórias de VMs (disponibilidade, WAVE, start/stop etc.) sobre a mesma fotografia de Tags |

## Estrutura do repositório

<details>
<summary><b>📁 Ver a árvore de pastas</b></summary>

```text
dash-finops/
├── api/
│   ├── main.py              rotas da API e regras de persistência
│   ├── db.py                conexão e caminho do banco
│   ├── cost_service.py      leitura e gravação dos exports de custos
│   ├── backup_service.py    backup automático do SQLite
│   ├── email_service.py     envio de e-mail (Logic App)
│   ├── sqldb.py             camada de dialeto SQLite / Azure SQL
│   ├── modulo_tags.py       regras do módulo de tags (fotografias, histórico, configuração)
│   ├── modulo_tags_rotas.py rotas /tags e /api/tags/...
│   └── modulo_auditoria_vms_rotas.py  rota /auditoria-vms
├── database/
│   └── schema.sql           todas as tabelas; a API aplica ao abrir o SQLite (cria o que faltar)
├── docs/
│   ├── AZURE_SQL.md         como funciona o modo Azure SQL
│   ├── MIGRACAO.md          checklist para levar o projeto a outra organização
│   ├── CHANGELOG.md         histórico de versões
│   └── golden_numeros.json  números de referência das competências fechadas
├── frontend/
│   ├── index.html           módulo Recomendações FinOps
│   ├── inicio.html          página inicial da plataforma
│   └── plataforma/          seletor de módulo, logos e favicon comuns
├── modulos/
│   ├── tags/                tela do módulo Governança de Tags (index.html + assets/)
│   └── auditoria-vms/       README do módulo (usa a tela de tags)
├── tools/
│   ├── verifica_numeros.py  confere as competências fechadas contra o golden
│   ├── freeze_competencia.py  fecha uma competência no SQLite (triggers)
│   ├── migrar_sqlite_para_azure_sql.py  copia o SQLite para o Azure SQL
│   ├── tags_carregar_base.py  grava a base inicial do módulo de tags (fora do Git)
│   └── gerar_tema_escuro.py   gera o tema escuro de Recomendações a partir do CSS
├── tests/                   unittest (só biblioteca padrão)
├── infra/                   Terraform da POC e pos_apply.ps1 (ver infra/README.md)
├── .github/workflows/       ci (PRs), deploy-poc (main) e infra (Terraform)
├── requirements.txt
└── .env.example
```

</details>

Ficam **fora do Git** (ver `.gitignore`) e existem apenas na máquina local: `database/*.db`, `data/` (inclusive `data/modulos/tags`, com o inventário Azure), `config/squads.json`, planilhas (`*.xlsx`, `*.csv`) e, em `infra/`, o `terraform.tfvars` e o state. Backups do banco e o baseline do dashboard original ficam fora do repositório (ex.: `C:\Dash-Finops\backup_poc`).

## Execução local

```powershell
.\.venv\Scripts\Activate.ps1
python -m uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
```

Acesse `http://127.0.0.1:8000/` (início), `/recomendacoes`, `/tags` ou `/auditoria-vms`.

Para o módulo de tags abrir com dados, grave a base inicial uma vez (fica em `data/modulos/tags`, fora do Git):

```powershell
python tools\tags_carregar_base.py <dashboard.html.gz.b64> [subscriptions-master.json]
```

Instalação das dependências: `pip install -r requirements.txt` (testado em Python 3.13).

## Variáveis de ambiente

| Variável | Uso |
|---|---|
| `FINOPS_DB_PATH` | caminho do SQLite (padrão `database/finops_dev.db`) |
| `FINOPS_TAGS_DATA_DIR` | pasta dos dados do módulo de tags (padrão: `/home/data/modulos/tags` no App Service, `data/modulos/tags` local) |
| `FINOPS_ADMINS` | e-mails do time FinOps (separados por vírgula ou ponto e vírgula) com acesso completo. Vazia = todos com acesso completo. Ver [Perfis de acesso](#perfis-de-acesso) |
| `FINOPS_USUARIO_TESTE` | simula o e-mail logado quando não há Easy Auth (só para testar os perfis localmente) |
| `FINOPS_REQUIRE_AUTH=1` | exige o cabeçalho `x-ms-client-principal-name` (Easy Auth / SSO); sem ele a API responde 401. Sem a variável, o usuário registrado é `dev-local` |
| `FINOPS_BACKUP=1`, `FINOPS_BACKUP_DIR`, `FINOPS_BACKUP_HORAS`, `FINOPS_BACKUP_MANTER` | backup automático (padrão: a cada 6 h, mantém 20) |
| `LOGIC_APP_URL` | endereço do gatilho HTTP do Logic App que envia e-mail |
| `FINOPS_EMAIL_OVERRIDE_TO` | redireciona todos os envios para um único endereço (com [TESTE] no assunto) |
| `FINOPS_EMAIL_TIMEOUT` | tempo limite do envio de e-mail, em segundos (padrão 30) |
| `FINOPS_RECS_CACHE_TTL_S` | validade do cache da listagem de recomendações no Azure SQL, em segundos (padrão 300) |
| `FINOPS_SQL_SERVER`, `FINOPS_SQL_DB`, `FINOPS_SQL_USER`, `FINOPS_SQL_PASSWORD` | liga o Azure SQL no lugar do SQLite (sem `FINOPS_SQL_SERVER` o app usa SQLite). Ajustes de conexão (`FINOPS_SQL_RETRIES`, `_RETRY_S`, `_TDS`, `_PORT`) em `docs/AZURE_SQL.md` |

> [!CAUTION]
> Nunca coloque valores reais no repositório. Use `.env` (ignorado pelo Git); `.env.example` mostra os nomes.

## Processo mensal

Cada mês é uma **competência** (por exemplo `2026-10`).

> [!NOTE]
> Setembro/2026 está **fechado**; Outubro/2026 está ativo.

### Importar recomendações

Há dois caminhos, que levam ao mesmo resultado:

- **Novas recomendações:** recebe os exports brutos (Advisor, Pier Cloud, Workbook, Squad, Solo) e grava no mês ativo. Adiciona só o que é realmente novo, reconhecendo o mesmo recurso pela identidade canônica (ignora variações de nome, SKU e sufixos) e consultando todas as competências anteriores (capturada ou reprovada antes não volta). As novas recebem ID `FINOPS-xxxxxx` (continuando a sequência) e a data do primeiro dia do mês. Mostra uma prévia antes de aplicar.
- **Atualizar planilha:** recebe a planilha oficial (aba `tabela`). Célula vazia significa "não alterar". Itens ausentes na planilha são mantidos, a menos que se marque a opção de removê-los.

O `FinOpsOpportunityId` é a chave que preserva o histórico entre competências, planilhas, chamados e Saving. Importar de novo não cria duplicidade.

### Virada de mês

A partir de 3 dias antes do fim do mês, o seletor de competência mostra **"+ Abrir {Mês}/{Ano}"**. Ao abrir, as recomendações pendentes (rascunho, identificada, validação técnica, planejada, em implementação, adiada) são herdadas pelo novo mês, e o dash já abre nele. Ao abrir um mês de Outubro em diante, a tela chama `POST /api/recomendacoes/{origem}/reconciliar-pendencias/{destino}`; a API só aceita o destino que for o mês seguinte da origem. Mudanças no mês anterior (ex.: marcar como capturada) continuam refletindo no mês novo.

A **data recomendada nunca muda na herança**: é a da primeira vez que a recomendação apareceu. Os campos de chamado do ciclo recomeçam em branco.

Roteiro da virada:

1. A partir do dia −3: **+ Abrir {mês}** no seletor de competência.
2. No mês novo: importar as novas recomendações (**Novas recomendações**).
3. Já no mês seguinte: importar os custos do mês anterior do dia 1 ao último dia e conferir o dash.
4. Fechar o mês anterior: `tools/fechar_competencia.py SIMULAR` e depois `APLICAR`; em seguida `verifica_numeros.py GERAR`.

### Rescaldo

O Rescaldo previsto de um mês passa a ser o **Rescaldo herdado** do mês seguinte. A regra vale de Outubro/2026 em diante (Setembro é o mês-base).

### Valores nos indicadores

Os KPIs em reais aparecem abreviados (por exemplo `R$ 291,9k`, `R$ 1,2M`). O valor completo aparece ao passar o mouse.

## Módulos Governança de Tags e Auditoria de VMs

- **Dados:** fotografias (`<data>--<hora>.json.gz` + `.meta.json`), `latest.txt` (fotografia exibida), `historico.json.gz` (base histórica), `subscriptions-master.json` e `governance-config.json` (mapa oficial CC × BU, ações e subscriptions), todos em `FINOPS_TAGS_DATA_DIR`. **Nada disso vai para o Git**; um teste (`tests/test_modulo_tags.py`) barra inventário (IDs de recursos/subscriptions) no código.
- **Atualizar os dados:** na própria tela, aba **Modelo Power BI** → CSV de recursos elegíveis do Resource Graph (e, se mudou, o cadastro de subscriptions) → **Gravar nova fotografia**. A fotografia vale para todos os usuários daquele ambiente; cada ambiente (local, POC, empresa) tem os próprios arquivos.
- **Ambiente novo:** carregar a base inicial uma vez (`tools/tags_carregar_base.py`, ou copiar a pasta de dados de outro App Service).
- **Quem mantém:** a tela do módulo (`modulos/tags/`) é mantida pelo time de governança de tags. Mudanças entram por PR para a `dev`, em branches `tags/<descrição>`, alterando só `modulos/tags/`; API e plataforma passam pela revisão do dono do repositório. Detalhes em `modulos/tags/README.md`.

## Perfis de acesso

O e-mail vem do login do App Service (Easy Auth). Regras em `api/acesso.py`, aplicadas na API (não só na tela):

| Perfil | Quem | O que vê e faz |
|---|---|---|
| FinOps (admin) | e-mail em `FINOPS_ADMINS` | tudo |
| Responsável de squad | E-mail Champion, E-mail Gestor ou E-mail Gestor Sênior da squad em Configurações › Squads | só as recomendações das suas squads (Visão geral, Saving, Comparativo, Execução, Chamados e SLA, Detalhamento). No Detalhamento, um formulário grava só Status, Data de Implantação Planejada, Data de Implantação e Observação (Realizado segue o status), com as regras da devolutiva: Capturado exige Data de Implantação (não futura); Planejada/Em Implementação exigem Data Planejada; Adiada exige Data Planejada e Observação; Reprovada exige Observação. Não grava configurações, chamados, custos nem importações |
| Sem cadastro | qualquer outro e-mail | aviso de acesso não liberado |

Sem `FINOPS_ADMINS` (ou sem login, como no local e na POC) todos são FinOps. Para testar localmente: `FINOPS_ADMINS=voce@empresa.com` e `FINOPS_USUARIO_TESTE=<e-mail cadastrado numa squad>`.

## Custos

Os exports de custos são gravados por competência e provedor e usados nos cálculos de Saving Efetivo e Rescaldo.

```text
Arquivo de custos -> Validação / Prévia -> API -> SQLite -> Recálculo -> Dashboard
```

Uma nova base de custos só substitui a anterior depois que a gravação no SQLite é confirmada.

## Competências fechadas

Depois de fechada, uma competência não pode mais ter seus valores financeiros alterados (Saving Est., Realizado, Saving, Saving Efetivo e Rescaldo previsto). A proteção existe em três camadas: tela, API e triggers no banco, todas ligadas à tabela `competencias_fechadas`. Tentativas de alteração são bloqueadas e registradas na tabela de auditoria.

Comandos úteis:

```powershell
# conferir se a competência fechada continua idêntica ao golden (somente leitura)
python tools\verifica_numeros.py VERIFICAR database\finops_dev.db 2026-09

# fechar uma competência no SQLite (simular antes de aplicar; com o servidor parado)
python tools\freeze_competencia.py SIMULAR database\finops_dev.db 2026-09

# fechar uma competência (SQLite local ou Azure SQL, conforme FINOPS_SQL_*)
python tools\fechar_competencia.py SIMULAR 2026-10
```

No Azure SQL, os triggers vêm do migrador (`--triggers`). `verifica_numeros.py` aceita `AZURE` no lugar do arquivo do banco.

> [!IMPORTANT]
> Qualquer alteração no código de cálculo deve ser seguida de `verifica_numeros.py`: o resultado precisa ser `OK`.

## Backup

Com `FINOPS_BACKUP=1`, a API copia o SQLite periodicamente para a pasta de backups. No Azure SQL o backup em disco fica desligado (o serviço tem backup próprio).

## Princípios de desenvolvimento

- Dados operacionais, custos, planilhas e configurações reais não vão para o Git.
- Nenhuma alteração sobrescreve dados sem validação; falhas de persistência não são mascaradas por armazenamento local.
- Alterações preservam os identificadores das recomendações.
- Competências fechadas permanecem imutáveis.

Fluxo de trabalho: alterar, validar tecnicamente, validar no dashboard, rodar `verifica_numeros.py`, commitar e enviar para a branch `dev`. Cada commit deve representar um estado funcional.

Ao mudar cores no CSS de Recomendações, gere de novo o tema escuro e confira o resultado com o botão LIGHT/DARK:

```powershell
python tools\gerar_tema_escuro.py frontend\index.html
```

## Publicação e infraestrutura da POC

A POC é um App Service pessoal (`dash-recomendacao-rb-tf`, Central US, SSO por Easy Auth) com Azure SQL Basic como banco.

**Fluxo de publicação**

1. Criar uma branch a partir da `dev`, alterar e abrir PR para a `dev`.
2. O workflow `ci` roda no PR (`.github/workflows/ci.yml`): compila o Python, roda `tests/` (unittest, só biblioteca padrão) e o gitleaks (procura segredos no código e no histórico). O PR só deve ser mesclado com os dois jobs verdes.
3. Para publicar, abrir PR `dev` → `main` e mesclar. A `main` só aceita PR com o job `testes` verde e **aprovação do dono do repositório** (o dono, como admin, mescla os próprios PRs com "bypass rules"). O push na `main` dispara `deploy-poc` (`.github/workflows/deploy-poc.yml`): testes, zip do código, `azure/login` por OIDC, `az webapp deploy` (sem acompanhar o status de startup do Azure, que às vezes fica preso numa falha anterior) e a confirmação de que o site responde (200/301/302/401), tentando por até 10 minutos.
4. Depois do merge, rodar `git pull` na cópia local para ela ficar igual ao repositório.

**Configuração no GitHub**

- Variáveis do repositório: `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID`, `TF_RESOURCE_GROUP`, `TF_APP_NAME`; para o workflow de infra também `TF_PLAN_NAME`, `EASYAUTH_CLIENT_ID` e, com state remoto, `TF_BACKEND_READY`.
- Secrets: `SQL_ADMIN_PASSWORD` (infra) e, no environment `poc`, `EASYAUTH_CLIENT_SECRET`. Credenciais federadas (OIDC) na service principal usada pelo login; o subject do OIDC do GitHub usa IDs numéricos: `repo:<dono>@<id>/<repo>@<id>:environment:poc`.
- O deploy não usa senha nem publish profile.

**Infraestrutura (Terraform)**

A infra da POC está em `infra/`. O workflow `infra` roda `plan` em PRs que mexem em `infra/`; enquanto o state for local, esse plan não vale como conferência (mostra tudo como novo) e o `apply` é feito na máquina. Depois de um `apply`, o `infra/pos_apply.ps1` grava senha e segredos, carrega os dados e publica o código. Roteiro completo em `infra/README.md`.

**Banco**

- SQLite é o padrão; o Azure SQL entra pelas variáveis `FINOPS_SQL_*`. Migração dos dados: `tools/migrar_sqlite_para_azure_sql.py <arquivo.db> APLICAR` (sem `APLICAR` só simula; `--recriar` apaga e recria as tabelas, `--triggers` cria os gatilhos de competência fechada).
- O firewall do SQL precisa liberar serviços do Azure e, para rodar a migração, o IP de quem executa. Remover a regra do IP depois.

<details>
<summary><b>⚡ Desempenho e cache</b></summary>

**`/api/custos/persistidos`**

O payload de custos é grande (~90 MB de JSON). O servidor guarda uma versão gzip em memória, indexada por ETag, e a aquece no startup (leva ~1 min depois de cada deploy). O navegador revalida com `If-None-Match` e recebe 304 quando nada mudou. O front só reenvia o estado de uma recomendação se o conteúdo mudou desde o último envio confirmado, e junta as gravações disparadas quase juntas numa única chamada (`POST /api/recomendacoes/{competencia}/estado-completo-lote`, uma transação, tudo ou nada). O log `[custos-cache]` mostra os tempos de leitura, JSON e gzip.

A listagem `GET /api/recomendacoes/{competencia}` também tem cache em memória no modo Azure SQL (sem filtros). Ele é invalidado a cada commit que escreve em `recommendations` (com versão nova a leitura é sempre refeita na hora, nunca se serve dado velho). Passados 5 minutos (`FINOPS_RECS_CACHE_TTL_S`), a requisição ainda recebe o que está em memória e uma releitura em segundo plano atualiza o cache, para cobrir alterações feitas fora do app (migração, SQL manual) sem que ninguém pague a leitura fria depois de um intervalo sem uso. Gravações que não mudam nenhum valor são ignoradas, para não invalidar o cache à toa. No lote, o estado atual das linhas é lido numa única consulta e só as linhas que mudam passam pelo caminho completo. No startup (Azure SQL) as 2 competências mais recentes são lidas em segundo plano para aquecer o cache. Vale para 1 instância com 1 worker, como está hoje; com mais instâncias, o cache de cada uma só se atualiza pelo TTL.

</details>

## Levar para outra organização

Veja `docs/MIGRACAO.md`: checklist de repositório, configuração, variáveis, publicação (App Service, SSO) e validação final.

O ambiente da empresa (Evertec) segue `infra/empresa/README.md`: recursos criados pelo Cloud Shell, login Entra ID (o App Registration precisa de *ID tokens* habilitado; sem isso o retorno do login responde 401) e publicação por pacote montado no Cloud Shell (Run From Package). O código chega ao repositório da empresa por sincronização com a `main` deste repositório; os dados de tags são carregados à parte na pasta do App Service.

## Versionamento

Segue [SemVer](https://semver.org/lang/pt-BR/) (`vMAJOR.MINOR.PATCH`), com tags criadas na `main`:

| Mudança | Versão |
|---|---|
| Correção de cálculo ou ajuste visual | PATCH (`v1.0.1`) |
| Funcionalidade nova | MINOR (`v1.1.0`) |
| Mudança que altera a forma de uso | MAJOR (`v2.0.0`) |

Versões candidatas usam `-rc.N` e são marcadas como *Pre-release*. Cada competência fechada recebe também uma tag `fechamento-AAAA-MM`, que registra a versão do código que calculou aqueles números. Histórico em [Releases](https://github.com/rafabiasotto/dash-finops/releases) e `docs/CHANGELOG.md`.

## Roadmap

- [x] Visão geral, Saving, Execução e Detalhamento no novo layout
- [x] Saving Efetivo de resize pelo preço efetivo e troca de tier de disco
- [x] Competências fechadas protegidas em tela, API e banco
- [x] Login corporativo (Entra ID) no ambiente da empresa
- [x] Plataforma de módulos: Recomendações, Governança de Tags e Auditoria de Tags de VMs
- [x] Tema escuro e ajuste de fonte em todos os módulos
- [ ] Deploy automático no ambiente da empresa (App Registration de deploy com OIDC)
- [ ] Extração diária automática de custos do PierCloud
- [ ] Acesso segregado por squad, com resposta direto no dash (piloto: Bancos)
