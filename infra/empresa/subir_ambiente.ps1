# subir_ambiente.ps1 - cria o dash FinOps num Azure da empresa usando so PowerShell + az CLI (sem Terraform).
#
# Como rodar (na raiz do repo, com o .venv ativo):
#   copy infra\empresa\ambiente.example.json infra\empresa\ambiente.json   # 1a vez; preencher
#   az login
#   powershell -ExecutionPolicy Bypass -File infra\empresa\subir_ambiente.ps1                  # todos os passos
#   powershell -ExecutionPolicy Bypass -File infra\empresa\subir_ambiente.ps1 -Passos 1,2,3,7   # so RG + recursos
#
# Pode rodar de novo: o que ja existe e mantido (nao recria nem apaga nada).
# Nunca imprime senha, secret nem a URL do gatilho. ASCII only.

# -Passos chega como texto ("1,2,3,7") quando o script roda com -File: separar pelas virgulas.
param($Passos = "1,2,3,4,5,6,7,8,9")   # sem tipo: $passos (mesma variavel) vira lista de int abaixo
$passos = @($Passos -split '[,;\s]+' | Where-Object { $_ } | ForEach-Object { [int]$_ })
#  1 Resource Group
#  2 Azure SQL (servidor, banco Basic, regra AllowAzureServices)
#  3 App Service Plan + Web App + appsettings (inclusive a senha do SQL)
#  4 Login (Easy Auth): App Registration, Redirect URI, secret      -> ANTES do codigo: o app nunca fica aberto
#  5 Dados: SQLite local -> Azure SQL (confere setembro contra o golden antes de copiar)
#  6 Codigo: zip do git_ref (padrao origin/main) publicado com az webapp deploy
#  7 Logic App + conexao de e-mail (template logicapp.json)
#  8 Autorizar a conexao de e-mail (manual, no portal)
#  9 LOGIC_APP_URL + e-mail de teste (FINOPS_EMAIL_OVERRIDE_TO)

$aqui    = $PSScriptRoot
$repo    = Split-Path -Parent (Split-Path -Parent $aqui)
$dbLocal = Join-Path $repo "database\finops_dev.db"
$ProgressPreference = 'SilentlyContinue'

function Falhar($msg) { "ABORTADO: $msg"; exit 1 }
function Existe($cmd) { $r = Invoke-Expression "$cmd 2>`$null"; return [bool]$r }

# ---------------------------------------------------------------- configuracao
$cfgArq = Join-Path $aqui "ambiente.json"
if (-not (Test-Path $cfgArq)) { Falhar "crie $cfgArq a partir de ambiente.example.json" }
$c = Get-Content $cfgArq -Raw | ConvertFrom-Json
foreach ($k in 'subscription_id','tenant_id','resource_group','location','plan_name','plan_sku','app_name','sql_server','sql_location','sql_db','sql_admin','logic_name','logic_location','mail_connector','git_ref') {
  if (-not $c.$k -or "$($c.$k)" -match '^0{8}-') { Falhar "preencha '$k' em ambiente.json" }
}
$rg  = $c.resource_group
$app = $c.app_name
$tags = @()
if ($c.tags) { $c.tags.PSObject.Properties | Where-Object { $_.Value } | ForEach-Object { $tags += "$($_.Name)=$($_.Value)" } }
$tagArgs = @(); if ($tags.Count) { $tagArgs = @("--tags") + $tags }   # sem tags: nao passa --tags
$hostApp  = "$app.azurewebsites.net"
$redirect = "https://$hostApp/.auth/login/aad/callback"
$sqlFqdn  = "$($c.sql_server).database.windows.net"
$conn     = if ($c.mail_connection) { $c.mail_connection } else { $c.mail_connector }   # nome do recurso da conexao

# ---------------------------------------------------------------- pre-requisitos
if (-not (az account show --query id -o tsv 2>$null)) { Falhar "rode 'az login' antes" }
az account set --subscription $c.subscription_id
if ($LASTEXITCODE -ne 0) { Falhar "sem acesso a subscription $($c.subscription_id)" }
if ($passos -contains 5) {
  python -c "import pymssql" 2>$null
  if ($LASTEXITCODE -ne 0) { Falhar "ative o .venv e instale as dependencias (passo 5 precisa de pymssql)" }
  if (-not (Test-Path $dbLocal)) { Falhar "banco local nao encontrado: $dbLocal" }
}
if ($passos -contains 6) {
  git -C $repo fetch -q origin
  git -C $repo rev-parse --verify -q "$($c.git_ref)^{commit}" > $null
  if ($LASTEXITCODE -ne 0) { Falhar "git_ref '$($c.git_ref)' nao existe" }
}

"Subscription: $($c.subscription_id) | RG: $rg | app: $app | SQL: $($c.sql_server) | passos: $($passos -join ',')"

# A senha do SQL e pedida uma vez so (passos 2, 3 e 5).
$senhaSql = $null
if ($passos -contains 2 -or $passos -contains 3 -or $passos -contains 5) {
  $sec = Read-Host "Senha do admin do SQL (na criacao: minimo 12 caracteres, maiuscula, minuscula, numero e simbolo)" -AsSecureString
  $senhaSql = [Runtime.InteropServices.Marshal]::PtrToStringBSTR([Runtime.InteropServices.Marshal]::SecureStringToBSTR($sec))
  if ($senhaSql.Length -lt 12) { Falhar "senha curta demais" }
}

# Grava appsettings por arquivo JSON: valores com & (URLs assinadas) quebram o az no Windows.
function GravarAppSettings($valores) {
  $f = Join-Path $env:TEMP ("app_settings_" + [Guid]::NewGuid().ToString("N") + ".json")
  try {
    $valores | ConvertTo-Json | Set-Content -Path $f -Encoding ascii
    az webapp config appsettings set -g $rg -n $app --settings "@$f" -o none
    if ($LASTEXITCODE -ne 0) { Falhar "nao gravou os appsettings" }
  } finally { Remove-Item $f -ErrorAction SilentlyContinue }
}

# ---------------------------------------------------------------- 1) Resource Group
if ($passos -contains 1) {
  "== 1) Resource Group $rg"
  if ((az group exists -n $rg) -eq 'true') { "ja existe" }
  else {
    az group create -n $rg -l $c.location @tagArgs -o none
    if ($LASTEXITCODE -ne 0) { Falhar "nao criou o RG (permissao? policy de tags/regiao?)" }
    "OK"
  }
}

# ---------------------------------------------------------------- 2) Azure SQL
if ($passos -contains 2) {
  "== 2) Azure SQL $($c.sql_server) / $($c.sql_db)"
  if (Existe "az sql server show -g $rg -n $($c.sql_server) --query name -o tsv") { "servidor ja existe (a senha NAO e alterada)" }
  else {
    az sql server create -g $rg -n $c.sql_server -l $c.sql_location -u $c.sql_admin -p $senhaSql --minimal-tls-version 1.2 -o none
    if ($LASTEXITCODE -ne 0) { Falhar "nao criou o servidor SQL (nome em uso? policy exige login so Entra ID?)" }
    if ($tags) { az resource tag -g $rg -n $c.sql_server --resource-type Microsoft.Sql/servers @tagArgs -o none }
  }
  if (Existe "az sql db show -g $rg -s $($c.sql_server) -n $($c.sql_db) --query name -o tsv") { "banco ja existe" }
  else {
    az sql db create -g $rg -s $c.sql_server -n $c.sql_db --service-objective Basic --max-size 2GB --backup-storage-redundancy Local @tagArgs -o none
    if ($LASTEXITCODE -ne 0) { Falhar "nao criou o banco" }
  }
  if (-not (Existe "az sql server firewall-rule show -g $rg -s $($c.sql_server) -n AllowAzureServices --query name -o tsv")) {
    az sql server firewall-rule create -g $rg -s $c.sql_server -n AllowAzureServices --start-ip-address 0.0.0.0 --end-ip-address 0.0.0.0 -o none
  }
  "OK"
}

# ---------------------------------------------------------------- 3) App Service
if ($passos -contains 3) {
  "== 3) App Service Plan $($c.plan_name) + Web App $app"
  if (-not (Existe "az appservice plan show -g $rg -n $($c.plan_name) --query name -o tsv")) {
    az appservice plan create -g $rg -n $c.plan_name -l $c.location --is-linux --sku $c.plan_sku @tagArgs -o none
    if ($LASTEXITCODE -ne 0) { Falhar "nao criou o App Service Plan" }
  }
  if (-not (Existe "az webapp show -g $rg -n $app --query name -o tsv")) {
    az webapp create -g $rg -n $app -p $c.plan_name --runtime "PYTHON:3.12" @tagArgs -o none
    if ($LASTEXITCODE -ne 0) { Falhar "nao criou o Web App (nome '$app' ja usado no Azure?)" }
  }
  az webapp update -g $rg -n $app --https-only true -o none
  $alwaysOn = if ($c.always_on) { 'true' } else { 'false' }
  az webapp config set -g $rg -n $app --always-on $alwaysOn --ftps-state FtpsOnly --min-tls-version 1.2 `
    --startup-file "python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 1" -o none
  $ret = if ($c.log_retention_days) { "$($c.log_retention_days)" } else { "7" }
  GravarAppSettings @{
    FINOPS_REQUIRE_AUTH                 = "1"
    WEBSITES_PORT                       = "8000"
    SCM_DO_BUILD_DURING_DEPLOYMENT      = "true"
    WEBSITE_HTTPLOGGING_RETENTION_DAYS  = $ret
    FINOPS_SQL_SERVER                   = $sqlFqdn
    FINOPS_SQL_DB                       = $c.sql_db
    FINOPS_SQL_USER                     = $c.sql_admin
    FINOPS_SQL_PASSWORD                 = $senhaSql
  }
  "OK"
}

# ---------------------------------------------------------------- 4) Login (Easy Auth)
if ($passos -contains 4) {
  "== 4) Login com conta da empresa (Easy Auth)"
  $appId = "$($c.auth_client_id)"
  if (-not $appId) {
    "auth_client_id vazio: criando a App Registration '$($c.auth_app_display_name)' (precisa de permissao no Entra ID)"
    $appId = az ad app create --display-name $c.auth_app_display_name --sign-in-audience AzureADMyOrg `
      --web-redirect-uris $redirect --enable-id-token-issuance true --query appId -o tsv
    if (-not $appId) { Falhar "sem permissao para criar App Registration: peca uma ao time de identidade e preencha auth_client_id" }
    az ad sp create --id $appId -o none 2>$null
    "App Registration criada: $appId  -> grave em auth_client_id no ambiente.json"
  }
  $cur = @(az ad app show --id $appId --query "web.redirectUris" -o json | ConvertFrom-Json)
  if ($cur -notcontains $redirect) {
    $cur += $redirect
    az ad app update --id $appId --web-redirect-uris $cur --enable-id-token-issuance true 2>$null | Out-Null
    $cur = @(az ad app show --id $appId --query "web.redirectUris" -o json | ConvertFrom-Json)
  }
  if ($cur -contains $redirect) { "Redirect URI OK" }
  else { "ATENCAO: peca ao dono da App Registration para cadastrar a Redirect URI: $redirect" }

  $temSecret = (az webapp config appsettings list -g $rg -n $app --query "[?name=='MICROSOFT_PROVIDER_AUTHENTICATION_SECRET'].name | [0]" -o tsv)
  if ($temSecret) { "secret do Easy Auth ja configurado (mantido)" }
  else {
    $new = az ad app credential reset --id $appId --append --display-name ("dash-" + (Get-Date -Format yyyyMMdd)) --years 1 --query password -o tsv 2>$null
    if (-not $new -or $new.Length -lt 30) {
      $sec = Read-Host "Sem permissao para gerar secret. Cole o secret fornecido pelo dono da App Registration" -AsSecureString
      $new = [Runtime.InteropServices.Marshal]::PtrToStringBSTR([Runtime.InteropServices.Marshal]::SecureStringToBSTR($sec))
    }
    if ($new.Length -lt 30) { Falhar "secret invalido" }
    GravarAppSettings @{ MICROSOFT_PROVIDER_AUTHENTICATION_SECRET = $new }
    "secret gravado no app (validade 1 ano: anote para renovar)"
  }
  # authsettingsV2 pela API (os comandos 'az webapp auth microsoft' dependem de extensao).
  $auth = @{ properties = @{
    platform         = @{ enabled = $true; runtimeVersion = "~1" }
    globalValidation = @{ requireAuthentication = $true; unauthenticatedClientAction = "RedirectToLoginPage"; redirectToProvider = "azureactivedirectory" }
    httpSettings     = @{ requireHttps = $true }
    login            = @{ tokenStore = @{ enabled = $true } }
    identityProviders = @{ azureActiveDirectory = @{
      enabled      = $true
      registration = @{ clientId = $appId; clientSecretSettingName = "MICROSOFT_PROVIDER_AUTHENTICATION_SECRET"
                        openIdIssuer = "https://sts.windows.net/$($c.tenant_id)/v2.0" }
      validation   = @{ allowedAudiences = @("api://$appId") } } } } }
  $af = Join-Path $env:TEMP ("auth_" + [Guid]::NewGuid().ToString("N") + ".json")
  try {
    $auth | ConvertTo-Json -Depth 8 | Set-Content -Path $af -Encoding ascii
    az rest --method put --url "https://management.azure.com/subscriptions/$($c.subscription_id)/resourceGroups/$rg/providers/Microsoft.Web/sites/$app/config/authsettingsV2?api-version=2022-03-01" --body "@$af" -o none
    if ($LASTEXITCODE -ne 0) { Falhar "nao ligou o Easy Auth" }
  } finally { Remove-Item $af -ErrorAction SilentlyContinue }
  "OK: login obrigatorio ligado"
}

# ---------------------------------------------------------------- 5) Dados
if ($passos -contains 5) {
  "== 5) Dados: SQLite local -> Azure SQL (o SQLite local so e LIDO)"
  Set-Location $repo
  python tools\verifica_numeros.py VERIFICAR $dbLocal 2026-09
  if ($LASTEXITCODE -ne 0) { Falhar "o banco local nao bate com o golden de setembro; nada foi copiado" }
  $meuIp = (Invoke-RestMethod -UseBasicParsing https://api.ipify.org).Trim()
  "Liberando o IP $meuIp no firewall do SQL (regra temporaria 'meu-ip')"
  az sql server firewall-rule create -g $rg -s $c.sql_server -n meu-ip --start-ip-address $meuIp --end-ip-address $meuIp -o none
  $env:FINOPS_SQL_SERVER   = $sqlFqdn
  $env:FINOPS_SQL_DB       = $c.sql_db
  $env:FINOPS_SQL_USER     = $c.sql_admin
  $env:FINOPS_SQL_PASSWORD = $senhaSql
  try {
    python tools\migrar_sqlite_para_azure_sql.py $dbLocal APLICAR
    if ($LASTEXITCODE -ne 0) { "FALHA na migracao: veja a saida acima" }
    else {
      "OK: carga conferida. Depois de testar o dash, recrie os triggers de competencia fechada:"
      "  python tools\migrar_sqlite_para_azure_sql.py $dbLocal APLICAR --triggers   (com as mesmas variaveis FINOPS_SQL_*)"
    }
  } finally {
    Remove-Item Env:FINOPS_SQL_PASSWORD, Env:FINOPS_SQL_SERVER, Env:FINOPS_SQL_DB, Env:FINOPS_SQL_USER -ErrorAction SilentlyContinue
  }
  "Quando terminar (inclusive o --triggers), feche o firewall:"
  "  az sql server firewall-rule delete -g $rg -s $($c.sql_server) -n meu-ip"
}

# ---------------------------------------------------------------- 6) Codigo
if ($passos -contains 6) {
  $ref = $c.git_ref
  "== 6) Codigo: publica $ref ($(git -C $repo rev-parse --short $ref))"
  $zip = Join-Path $env:TEMP ("dash_" + [Guid]::NewGuid().ToString("N") + ".zip")
  try {
    git -C $repo archive --format=zip -o $zip $ref
    if ($LASTEXITCODE -ne 0) { Falhar "git archive falhou" }
    az webapp deploy -g $rg -n $app --src-path $zip --type zip --timeout 1200000 -o none
    if ($LASTEXITCODE -ne 0) { Falhar "deploy falhou (veja: az webapp log tail -g $rg -n $app)" }
  } finally { Remove-Item $zip -ErrorAction SilentlyContinue }
  "aguardando o app subir..."
  $code = 0
  for ($i = 0; $i -lt 12 -and @(200,301,302,401) -notcontains $code; $i++) {
    Start-Sleep -Seconds 15
    try { $code = (Invoke-WebRequest -UseBasicParsing -MaximumRedirection 0 -TimeoutSec 60 "https://$hostApp/" -ErrorAction Stop).StatusCode }
    catch { if ($_.Exception.Response) { $code = [int]$_.Exception.Response.StatusCode } }
  }
  if (@(200,301,302,401) -contains $code) { "OK: https://$hostApp responde (HTTP $code)" }
  else { "ATENCAO: o app nao respondeu (HTTP $code). Logs: az webapp log tail -g $rg -n $app" }
}

# ---------------------------------------------------------------- 7) Logic App
if ($passos -contains 7) {
  "== 7) Logic App $($c.logic_name) + conexao $conn ($($c.mail_connector))"
  $tagObj = @{}
  if ($c.tags) { $c.tags.PSObject.Properties | Where-Object { $_.Value } | ForEach-Object { $tagObj[$_.Name] = "$($_.Value)" } }
  $pf = Join-Path $env:TEMP ("logic_params_" + [Guid]::NewGuid().ToString("N") + ".json")
  try {
    @{ '$schema' = 'https://schema.management.azure.com/schemas/2019-04-01/deploymentParameters.json#'; contentVersion = '1.0.0.0'
       parameters = @{ location = @{ value = $c.logic_location }; workflowName = @{ value = $c.logic_name }
                       connectorName = @{ value = $c.mail_connector }; connectionName = @{ value = $conn }; tags = @{ value = $tagObj } } } |
      ConvertTo-Json -Depth 5 | Set-Content -Path $pf -Encoding ascii
    az deployment group create -g $rg -n dash-logicapp --template-file (Join-Path $aqui "logicapp.json") --parameters "@$pf" -o none
    if ($LASTEXITCODE -ne 0) { Falhar "nao criou o Logic App" }
  } finally { Remove-Item $pf -ErrorAction SilentlyContinue }
  "OK"
}

# ---------------------------------------------------------------- 8) autorizar e-mail
if ($passos -contains 8) {
  "== 8) Conexao de e-mail (manual): portal > RG $rg > API connection '$conn' > Edit API connection > Authorize > Save"
  "   Use a conta que vai ENVIAR os e-mails (de preferencia uma caixa de servico, nao a pessoal)."
  Read-Host "Depois de autorizar, pressione Enter"
  $st = az resource show -g $rg -n $conn --resource-type Microsoft.Web/connections --query "properties.statuses[0].status" -o tsv
  "status da conexao: $st   (esperado: Connected)"
}

# ---------------------------------------------------------------- 9) LOGIC_APP_URL
if ($passos -contains 9) {
  "== 9) LOGIC_APP_URL e e-mail de teste"
  $mail = Read-Host "Seu e-mail para os testes (todo envio vai so para ele, com [TESTE] no assunto)"
  $id = az resource show -g $rg -n $c.logic_name --resource-type Microsoft.Logic/workflows --query id -o tsv
  $u  = az rest --method post --url "https://management.azure.com$id/triggers/manual/listCallbackUrl?api-version=2016-06-01" --query value -o tsv
  if ($u.Length -gt 50) {
    GravarAppSettings @{ LOGIC_APP_URL = $u; FINOPS_EMAIL_OVERRIDE_TO = $mail }
    "OK. Para enviar de verdade depois: az webapp config appsettings delete -g $rg -n $app --setting-names FINOPS_EMAIL_OVERRIDE_TO"
  } else { "FALHA: URL do gatilho vazia (o passo 7 rodou?)" }
}

"== appsettings (so os nomes):"
az webapp config appsettings list -g $rg -n $app --query "[].name" -o tsv
"== FIM: https://$hostApp  -> teste o login em janela anonima, uma importacao e um envio de e-mail."
