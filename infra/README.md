# infra/ (Terraform) - roteiro do dash FinOps

Ambiente da POC: RG `rg-dash-recomendacao-tf`, criado e mantido por este Terraform. Estado em 2026-10-10.

Recursos (10): RG, App Service Plan Linux B1, Linux Web App (Python 3.12, Easy Auth), Azure SQL
(servidor, banco `finops` Basic e a regra de firewall `AllowAzureServices`), conexao Outlook e Logic App
(gatilho HTTP `manual` + acao `Enviar_email`).
A App Registration NAO e criada: usa uma existente (`auth_client_id`), que ja tem consent.
Nunca commitar: `terraform.tfvars`, state, `tf.plan`, URL do gatilho do Logic App, secrets.

## 1. Subir ou alterar a infra

```powershell
cd infra
copy terraform.tfvars.example terraform.tfvars   # so na 1a vez; preencher (arquivo so local)
az login
terraform init
terraform fmt
terraform validate
terraform plan -out tf.plan      # ler o plan antes de aplicar
terraform apply tf.plan
```

- A senha do admin do SQL vai por variavel de ambiente, nunca no tfvars commitado:
  `$env:TF_VAR_sql_admin_password = "<senha>"`. So vale na criacao do servidor; depois e ignorada.
- Valor conferido na POC: `log_retention_days = 3` (no tfvars).
- Num RG vazio o plan cria 10 recursos. Numa infra ja criada, so o que mudou no codigo.
- Se o nome do Web App ja existir no mundo, trocar `app_name`. Se o apply falhar no meio, rodar de novo (nao duplica).
- Mudar appsettings reinicia o web app (~1 min fora + ~1 min para aquecer o cache de custos).

## 2. Depois do apply: `infra/pos_apply.ps1`

O Terraform nao grava senhas e segredos (para nao irem ao state) nem os dados. O script faz o resto:

```powershell
# na raiz do repo, com o .venv ativo; antes: az login e gh auth login
powershell -ExecutionPolicy Bypass -File infra\pos_apply.ps1
```

Nada para editar: os nomes vem do `terraform output` e o `auth_client_id` do `terraform.tfvars`.
Para rodar so alguns passos, ajuste `$passos` no inicio do script. A senha do SQL e pedida uma vez.

| Passo | O que faz | Precisa de voce |
|---|---|---|
| 1 | Grava `FINOPS_SQL_PASSWORD` no web app | digitar a senha do SQL |
| 2 | Confere setembro contra o golden, libera seu IP no firewall e copia o SQLite local para o Azure SQL (`tools/migrar_sqlite_para_azure_sql.py`, que confere contagens, assinatura e somas) | depois: `--triggers` e fechar o firewall (o script imprime os comandos) |
| 3 | Dispara o workflow `deploy-poc` (publica a `main`) | - |
| 4 | Cadastra a Redirect URI na App Registration | ser Owner da app |
| 5 | Gera um secret NOVO do Easy Auth, grava no app e copia para a area de transferencia | colar no GitHub: Settings > Environments > `poc` > `EASYAUTH_CLIENT_SECRET` |
| 6 | Confere a conexao do Outlook | autorizar no portal: API connection `outlook` > Edit API connection > Authorize > Save |
| 7 | Grava `LOGIC_APP_URL` e `FINOPS_EMAIL_OVERRIDE_TO` (todo e-mail vai so para voce, com [TESTE]) | seu e-mail; para enviar de verdade, apagar o override (o script imprime o comando) |

A ordem importa: dados (2) antes do codigo (3), para o app ja subir com as tabelas.
O passo 5 gera um secret novo a cada execucao: tire-o de `$passos` se o atual ainda vale.

Cuidados (valem tambem fora do script):
- Valores com `&` (URLs assinadas) nunca vao direto na linha do `az` no Windows: o `&` vira "proximo
  comando" e o valor e gravado cortado. O script grava por arquivo JSON (`--settings "@arquivo"`).
- NUNCA listar os appsettings do Web App com valores na tela: o `az` mostra os segredos.
  Listar so os nomes: `az webapp config appsettings list -g <rg> -n <app> --query "[].name" -o tsv`.
- Secret do Easy Auth: manter so o que esta em uso e ANOTAR a validade (rot4-2026-10 vence em 2027-10-09).
  Perto disso: rodar o passo 5, atualizar o GitHub, apagar o antigo. Guardar o valor ao gerar: ler de
  volta pelo `az` e pouco confiavel.
- O Terraform ignora (`ignore_changes`) `FINOPS_SQL_PASSWORD`, `MICROSOFT_PROVIDER_AUTHENTICATION_SECRET`,
  `LOGIC_APP_URL` e `FINOPS_EMAIL_OVERRIDE_TO`: um apply nao apaga o que o script gravou.
- Campos que o dash envia ao Logic App: email, assunto, corpoHtml, anexoNome, anexoBase64.
- Backups do banco ficam fora do repo (ex.: C:\Dash-Finops\backup_poc).

Destruir e recriar tudo: o apply recria o SQL **vazio**; rodar o `pos_apply.ps1` inteiro (e o `--triggers`).

## 3. Pipeline GitHub Actions (`.github/workflows/infra.yml`)

- `plan` roda em PR que mexe em `infra/` (credencial federada `gh-dash-pr`).
- **Enquanto o state for local, o `plan` do CI nao vale como conferencia:** o runner nao tem o state e mostra
  todos os recursos como novos ("10 to add"). Conferir com `terraform plan` local.
- `apply` roda em push na `main` ou manual, so no environment `poc` (credencial `gh-dash-env-poc`)
  e SO se a variable `TF_BACKEND_READY=true` (state remoto pronto). Sem state remoto o runner perde o state.
- Login Azure por OIDC (sem senha): SP `sp-rafael-labs` com 2 federated credentials:
  `repo:<owner>/<repo>:pull_request` e `repo:<owner>/<repo>:environment:poc`.
- Variables no nivel do REPOSITORIO (o job `plan` nao ve variables de environment):
  `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID`, `TF_RESOURCE_GROUP`, `TF_APP_NAME`,
  `TF_PLAN_NAME`, `EASYAUTH_CLIENT_ID` e, quando houver state remoto, `TF_BACKEND_READY`.
- Secrets: `SQL_ADMIN_PASSWORD` (sem ele o plan usa um valor so para planejar) e `EASYAUTH_CLIENT_SECRET`
  SO no environment `poc`.
- Environment `poc`: restringir deployment branches a `main`. Revisor obrigatorio so existe em plano pago
  (repo privado gratuito nao tem); sem isso, deixar o apply manual (`workflow_dispatch`).
- A SP `sp-rafael-labs` tem Contributor + User Access Administrator na assinatura: largo demais.
  Este Terraform nao cria role assignment; remover o User Access Administrator se nenhum outro lab usar.
- `terraform fmt -check` falha o PR se o codigo nao estiver formatado: rodar `terraform fmt` antes.
- Pinar as actions por SHA antes de migrar para a empresa.

## 4. Apagar o POC antigo (`rg-dash-recomendacao-teste`), se ainda existir - so depois de:
1. App novo abre com login e mostra setembro e outubro (banco confirmado, hashes iguais).
2. Definicao do Logic App salva (feito: `logic-definition.json`) e modelada em `main.tf`.
3. `az resource list -g rg-dash-recomendacao-teste` mostra so: plano, Web App, conexao outlook, Logic App.
Apagar: `az group delete -n rg-dash-recomendacao-teste` (sem --yes, para confirmar).
NAO apagar a App Registration (o app novo usa a mesma). Depois: remover da app a Redirect URI do
app antigo e conferir que sobrou so um secret valido.

## 5. State remoto (empresa)
Criar Storage Account + container `tfstate` e descomentar o `backend` em `versions.tf`.
O state nao guarda o secret do Easy Auth, mas o acesso deve ser restrito mesmo assim.
Hoje o state e LOCAL (arquivo na maquina): nao apagar `terraform.tfstate` antes de `terraform destroy`.

## 6. Migracao para a empresa (ver docs/MIGRACAO.md)
- Recriar a infra no tenant da empresa (nao reaproveitar o POC); App Registration dedicada ao dash
  (pedir a quem da consent) e SP propria com papel so no RG (RG criado antes por quem tem permissao).
- Tags e nomes seguindo a policy; `always_on = true`; `outlook_api_name = "office365"` (provavelmente).
- FTP e SCM com senha estao ligados (padrao do provider): transformar em variavel e desligar na empresa.
- `use_32_bit_worker` esta true (igual ao POC); revisar.
- Secret do Easy Auth: credencial federada ou Key Vault reference em vez de secret.
- Historico do repo tem `*.bak_encoding_*` e 23 commits com e-mail pessoal: subir sem historico ou filtrar.
- Validar sempre com `tools/verifica_numeros.py` (setembro tem que bater com o golden).

## 7. Checklist (estado em 2026-10-10)
- [x] Infra criada pelo Terraform (RG `-tf`), inclusive Logic App e conexao Outlook
- [x] Azure SQL (servidor, banco `finops`, regra `AllowAzureServices`) no state do Terraform (ver Historico)
- [x] Redirect URI e secret do Easy Auth aplicados
- [x] GitHub: variables no repo (`AZURE_*`, `TF_*`, `EASYAUTH_CLIENT_ID`), secret `SQL_ADMIN_PASSWORD`
- [x] `.terraform.lock.hcl` commitado e `tf.plan` no `.gitignore`
- [ ] Testar `destroy` + `apply` + `pos_apply.ps1` do zero (nunca rodou de ponta a ponta)
- [ ] State remoto (secao 5) e `TF_BACKEND_READY=true` para o apply pelo pipeline
- [ ] Trocar a senha do admin do SQL (apareceu em log) e atualizar `SQL_ADMIN_PASSWORD` e `FINOPS_SQL_PASSWORD`
- [ ] Apagar a regra de firewall `pc-rafael-evertec` e as credenciais federadas antigas do GitHub
- [ ] Recriar os triggers de competencia fechada no Azure SQL (`--triggers`) depois dos testes
- [ ] Apagar `rg-dash-recomendacao-teste` e a Redirect URI antiga, se ainda existirem (secao 4)
- [ ] Pendencias do dash: conferir dash x planilha de recomendacoes (ultima diferenca anotada: 50 "Volume de instancia parada")

## Historico: adocao do Azure SQL no state (feito uma vez, em 2026-10)

O SQL Server, o banco e a regra `AllowAzureServices` foram criados a mao na POC e depois adotados no state.
So e preciso repetir se um SQL criado fora do Terraform tiver de ser adotado de novo (de dentro de `infra/`):

```powershell
$base = "/subscriptions/<subscription_id>/resourceGroups/rg-dash-recomendacao-tf/providers/Microsoft.Sql/servers/sql-dash-recomendacao-rb"
$env:TF_VAR_sql_admin_password = "qualquer-valor"   # ignorado depois (ignore_changes)
terraform import azurerm_mssql_server.this $base
terraform import azurerm_mssql_database.finops "$base/databases/finops"
terraform import azurerm_mssql_firewall_rule.azure_services "$base/firewallRules/AllowAzureServices"
terraform plan   # tem que dar 0 to destroy e nenhum "must be replaced"
```

Se o plan mostrar replace no banco, parar e ajustar collation/sku em `sql.tf`.
