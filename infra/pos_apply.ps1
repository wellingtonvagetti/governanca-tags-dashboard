# pos_apply.ps1 - passos que o Terraform NAO faz, para rodar DEPOIS do `terraform apply` (ver infra/README.md, secao 2).
#
# Como rodar (na raiz do repo, com o .venv ativo):
#   powershell -ExecutionPolicy Bypass -File infra\pos_apply.ps1
#
# Antes: az login, gh auth login, e o .venv com as dependencias (pip install -r requirements.txt).
# Os nomes (RG, app, SQL) vem do `terraform output` e o client id do Easy Auth vem do terraform.tfvars:
# nada para editar aqui. Para rodar so alguns passos, ajuste $passos.
# Nunca imprime senha, secret nem a URL do gatilho. So LE o banco local. ASCII only.

$passos = 1,2,3,4,5,6,7
#  1 senha do SQL no web app      (FINOPS_SQL_PASSWORD; o Terraform nao grava a senha)
#  2 dados: SQLite local -> Azure SQL (migrador; antes do codigo, para o app ja subir com tabelas)
#  3 codigo: dispara o workflow deploy-poc (publica a main)
#  4 Redirect URI na App Registration
#  5 secret do Easy Auth            (gera um NOVO a cada execucao: tire o 5 se ja houver um valido)
#  6 autorizar a conexao do Outlook (manual, no portal)
#  7 LOGIC_APP_URL + e-mail de teste (FINOPS_EMAIL_OVERRIDE_TO)

$repo    = Split-Path -Parent $PSScriptRoot
$infra   = Join-Path $repo "infra"
$dbLocal = Join-Path $repo "database\finops_dev.db"
$ProgressPreference = 'SilentlyContinue'

function Falhar($msg) { "ABORTADO: $msg"; exit 1 }
function TfOut($nome) { (terraform -chdir="$infra" output -raw $nome 2>$null) }

# ---------------------------------------------------------------- pre-requisitos e nomes
if (-not (Get-Command terraform -ErrorAction SilentlyContinue)) { Falhar "terraform nao esta no PATH" }
if (-not (az account show --query id -o tsv 2>$null)) { Falhar "rode 'az login' antes" }

$rg     = TfOut "resource_group"
$appUrl = TfOut "app_url"
$sqlFqdn = TfOut "sql_server_fqdn"
if (-not $rg -or -not $appUrl -or -not $sqlFqdn) { Falhar "sem 'terraform output' (o apply rodou? o state local esta em infra\?)" }
$app    = ([Uri]$appUrl).Host.Split('.')[0]
$srvSql = $sqlFqdn.Split('.')[0]

$tfvars = Join-Path $infra "terraform.tfvars"
$appId  = $null
if (Test-Path $tfvars) {
  $m = Select-String -Path $tfvars -Pattern '^\s*auth_client_id\s*=\s*"([^"]+)"' | Select-Object -First 1
  if ($m) { $appId = $m.Matches[0].Groups[1].Value }
}
if (($passos -contains 4 -or $passos -contains 5) -and -not $appId) { Falhar "auth_client_id nao encontrado em infra\terraform.tfvars" }
if ($passos -contains 3) {
  gh auth status *> $null
  if ($LASTEXITCODE -ne 0) { Falhar "rode 'gh auth login' antes (passo 3)" }
}
if ($passos -contains 2) {
  python -c "import pymssql" 2>$null
  if ($LASTEXITCODE -ne 0) { Falhar "ative o .venv e instale as dependencias (passo 2 precisa de pymssql)" }
  if (-not (Test-Path $dbLocal)) { Falhar "banco local nao encontrado: $dbLocal" }
}
if (-not (az webapp show -g $rg -n $app --query name -o tsv 2>$null)) { Falhar "web app $app nao existe em $rg (rode o terraform apply)" }

"RG: $rg | app: $app | SQL: $srvSql | passos: $($passos -join ',')"

# A senha do SQL e pedida uma vez so (passos 1 e 2).
$senhaSql = $null
if ($passos -contains 1 -or $passos -contains 2) {
  $sec = Read-Host "Senha do admin do SQL (a mesma de TF_VAR_sql_admin_password / secret SQL_ADMIN_PASSWORD)" -AsSecureString
  $senhaSql = [Runtime.InteropServices.Marshal]::PtrToStringBSTR([Runtime.InteropServices.Marshal]::SecureStringToBSTR($sec))
  if ($senhaSql.Length -lt 12) { Falhar "senha curta demais" }
}

# Grava appsettings por arquivo JSON: valores com & (URLs assinadas) quebram o az no Windows.
function GravarAppSettings($valores) {
  $f = Join-Path $env:TEMP ("app_settings_" + [Guid]::NewGuid().ToString("N") + ".json")
  try {
    $valores | ConvertTo-Json | Set-Content -Path $f -Encoding ascii
    az webapp config appsettings set -g $rg -n $app --settings "@$f" -o none
  } finally { Remove-Item $f -ErrorAction SilentlyContinue }
}

# ---------------------------------------------------------------- 1) senha do SQL no app
if ($passos -contains 1) {
  "== 1) FINOPS_SQL_PASSWORD no web app"
  GravarAppSettings @{ FINOPS_SQL_PASSWORD = $senhaSql }
  "OK"
}

# ---------------------------------------------------------------- 2) dados
if ($passos -contains 2) {
  "== 2) Dados: SQLite local -> Azure SQL (o SQLite local so e LIDO)"
  Set-Location $repo
  python tools\verifica_numeros.py VERIFICAR $dbLocal 2026-09
  if ($LASTEXITCODE -ne 0) { Falhar "o banco local nao bate com o golden de setembro; nada foi copiado" }
  $meuIp = (Invoke-RestMethod -UseBasicParsing https://api.ipify.org).Trim()
  "Liberando o IP $meuIp no firewall do SQL (regra temporaria 'meu-ip')"
  az sql server firewall-rule create -g $rg -s $srvSql -n meu-ip --start-ip-address $meuIp --end-ip-address $meuIp -o none
  $env:FINOPS_SQL_SERVER   = $sqlFqdn
  $env:FINOPS_SQL_DB       = (az webapp config appsettings list -g $rg -n $app --query "[?name=='FINOPS_SQL_DB'].value | [0]" -o tsv)
  $env:FINOPS_SQL_USER     = (az webapp config appsettings list -g $rg -n $app --query "[?name=='FINOPS_SQL_USER'].value | [0]" -o tsv)
  $env:FINOPS_SQL_PASSWORD = $senhaSql
  try {
    python tools\migrar_sqlite_para_azure_sql.py $dbLocal APLICAR
    if ($LASTEXITCODE -ne 0) { "FALHA na migracao: veja a saida acima" }
    else {
      "OK: carga conferida. Depois de testar o dash, recrie os triggers de competencia fechada:"
      "  python tools\migrar_sqlite_para_azure_sql.py $dbLocal APLICAR --triggers"
    }
  } finally {
    Remove-Item Env:FINOPS_SQL_PASSWORD, Env:FINOPS_SQL_SERVER, Env:FINOPS_SQL_DB, Env:FINOPS_SQL_USER -ErrorAction SilentlyContinue
  }
  "Quando terminar (inclusive o --triggers), feche o firewall:"
  "  az sql server firewall-rule delete -g $rg -s $srvSql -n meu-ip"
}

# ---------------------------------------------------------------- 3) codigo
if ($passos -contains 3) {
  "== 3) Codigo: dispara o workflow deploy-poc (mesmo caminho da pipeline; publica a main)"
  Set-Location $repo
  gh workflow run deploy-poc.yml --ref main
  "Acompanhe com: gh run watch   (leva uns 5 min)"
}

# ---------------------------------------------------------------- 4) Redirect URI
if ($passos -contains 4) {
  "== 4) Redirect URI na App Registration (precisa ser Owner da app)"
  $nova = TfOut "redirect_uri_a_cadastrar"
  $cur  = @(az ad app show --id $appId --query "web.redirectUris" -o json | ConvertFrom-Json)
  if ($cur -notcontains $nova) { $cur += $nova; az ad app update --id $appId --web-redirect-uris $cur 2>$null | Out-Null }
  # o az pode avisar erro mesmo gravando: confere lendo de volta
  $cur = @(az ad app show --id $appId --query "web.redirectUris" -o json | ConvertFrom-Json)
  if ($cur -contains $nova) { "OK: URI cadastrada" } else { "FALHA: URI nao esta na app (precisa ser Owner)" }
}

# ---------------------------------------------------------------- 5) secret do Easy Auth
if ($passos -contains 5) {
  "== 5) Secret do Easy Auth (gera um NOVO; o antigo nao e recuperavel)"
  $new = az ad app credential reset --id $appId --append --display-name ("rot-" + (Get-Date -Format yyyyMMdd-HHmm)) --years 1 --query password -o tsv
  if ($new.Length -ge 30) {
    GravarAppSettings @{ MICROSOFT_PROVIDER_AUTHENTICATION_SECRET = $new }
    $new | Set-Clipboard
    "OK: aplicado no app e COPIADO. Cole agora no GitHub: Settings > Environments > poc > EASYAUTH_CLIENT_SECRET"
    "Secrets da app (apague os antigos depois que o login funcionar; anote a validade):"
    az ad app credential list --id $appId --query "[].{nome:displayName,fim:endDateTime}" -o table
  } else { "FALHA: secret invalido, nada aplicado" }
}

# ---------------------------------------------------------------- 6) Outlook
if ($passos -contains 6) {
  "== 6) Conexao do Outlook (manual): portal > API connection 'outlook' > Edit API connection > Authorize > Save"
  Read-Host "Depois de autorizar, pressione Enter"
  $st = az resource show -g $rg -n outlook --resource-type Microsoft.Web/connections --query "properties.statuses[0].status" -o tsv
  "status da conexao: $st   (esperado: Connected)"
}

# ---------------------------------------------------------------- 7) LOGIC_APP_URL
if ($passos -contains 7) {
  "== 7) LOGIC_APP_URL e e-mail de teste"
  $mail = Read-Host "Seu e-mail para os testes (todo envio vai so para ele, com [TESTE] no assunto)"
  $id = az resource show -g $rg -n logic-finops-alerta-teste --resource-type Microsoft.Logic/workflows --query id -o tsv
  $u  = az rest --method post --url "https://management.azure.com$id/triggers/manual/listCallbackUrl?api-version=2016-06-01" --query value -o tsv
  if ($u.Length -gt 50) {
    GravarAppSettings @{ LOGIC_APP_URL = $u; FINOPS_EMAIL_OVERRIDE_TO = $mail }
    "OK. Para enviar de verdade depois: az webapp config appsettings delete -g $rg -n $app --setting-names FINOPS_EMAIL_OVERRIDE_TO"
  } else { "FALHA: URL do gatilho vazia (o apply criou o Logic App?)" }
}

"== appsettings (so os nomes):"
az webapp config appsettings list -g $rg -n $app --query "[].name" -o tsv
"== FIM. Teste o login em janela anonima e um envio de e-mail pelo dash."
