# cloudshell_recursos.ps1 - cria SO o RG e os recursos do dash (sem login, dados nem codigo), pelo Cloud Shell do portal.
#
# Para quem nao pode criar pela maquina (login local so com Reader). Use uma conta com Contributor na assinatura
# (ou ative o papel pelo PIM antes):
#   1. portal.azure.com > Cloud Shell (icone >_) > PowerShell
#   2. Copie ESTE ARQUIVO INTEIRO e cole no Cloud Shell (Ctrl+V / Shift+Insert / botao direito). Colar so CARREGA a
#      funcao Dash-Recursos: nada e executado nem criado.
#   3. Dash-Recursos                 -> valida (NAO cria nada): conta, permissao, providers, nomes, conector de e-mail
#                                       na regiao, policies da assinatura e o que seria criado
#   4. Dash-Recursos -Modo criar     -> cria (pode rodar de novo: o que ja existe e mantido)
#   Se der erro, a mensagem aparece e o Cloud Shell continua aberto.
#
# Cria: RG, App Service Plan Linux, Web App Python 3.12 (pagina padrao, sem codigo), Azure SQL (servidor, banco
# Basic 2 GB, regra AllowAzureServices), Logic App Consumption (sem plano, cobra por execucao) + conexao Office 365.
# Depois, o resto (login, dados, codigo, e-mail) e com subir_ambiente.ps1 -Passos 4,5,6,8,9. ASCII only.

function Dash-Recursos {
  param([ValidateSet('validar', 'criar')][string]$Modo = 'validar')
  $modo = $Modo


  $subscription   = '4e7af638-eee0-4a27-afde-ed0c7e487463'
  $location       = 'brazilsouth'
  $rg             = 'rg-dash-rec-finops'
  $planName       = 'asp-dash-rec-finops'
  $planSku        = 'B1'
  $app            = 'app-dash-rec-finops'
  $alwaysOn       = 'true'
  $sqlServer      = 'sql-dash-rec-finops'
  $sqlDb          = 'sqldb-dash-rec-finops'
  $sqlAdmin       = 'dashadmin'
  $logicName      = 'logic-dash-rec-finops'
  $mailConnector  = 'office365'
  $mailConnection = 'con-office365-dash-rec-finops'
  $tags = [ordered]@{
    AMBIENTE = 'DEV'; BU = 'COMPARTILHADO'; CCOWNER = 'BRUNO CHEL'; CAPEX = 'NAO'; CC = '9020600'
    CLIENTE = 'EVERTEC'; PRODUTO = 'DASH FINOPS'; SQUAD = 'SQUAD.SRE@EVERTECINC.COM.BR'
  }

  # ------------------------------------------------------------------ apoio
  $ProgressPreference = 'SilentlyContinue'
  $tagArgs = @('--tags') + @($tags.Keys | ForEach-Object { "$_=$($tags[$_])" })
  $arm = "https://management.azure.com/subscriptions/$subscription/resourceGroups/$rg/providers"
  $apiId = "/subscriptions/$subscription/providers/Microsoft.Web/locations/$location/managedApis/$mailConnector"
  function Falhar($msg) { throw "ABORTADO: $msg" }   # throw (e nao exit): nao fecha o Cloud Shell
  function Existe([string[]]$cmd) { $r = & az @cmd 2>$null; return [bool]$r }
  function PutArm($url, $corpo) {
    $f = Join-Path $HOME ("arm_" + [Guid]::NewGuid().ToString("N") + ".json")
    try {
      $corpo | ConvertTo-Json -Depth 20 | Set-Content -Path $f
      az rest --method put --url $url --body "@$f" -o none
      if ($LASTEXITCODE -ne 0) { Falhar "PUT falhou: $url" }
    } finally { Remove-Item $f -ErrorAction SilentlyContinue }
  }

  # ------------------------------------------------------------------ conferencias (os dois modos)
  az account set --subscription $subscription
  if ($LASTEXITCODE -ne 0) { Falhar "sem acesso a assinatura $subscription" }
  "Conta: $(az account show --query user.name -o tsv) | assinatura: $(az account show --query name -o tsv) | modo: $modo"

  "== Permissao na assinatura (Owner ou Contributor necessario para criar)"
  $me = az ad signed-in-user show --query id -o tsv 2>$null
  $papeis = @()
  if ($me) {
    $papeis = @(az role assignment list --assignee $me --include-groups --include-inherited --scope "/subscriptions/$subscription" --query "[].roleDefinitionName" -o tsv 2>$null)
  }
  $papeis = @($papeis | Sort-Object -Unique)
  if ($papeis.Count) { "papeis: $($papeis -join ', ')" } else { "papeis: nenhum encontrado (ou sem permissao para ler)" }
  $podeCriar = [bool]($papeis | Where-Object { $_ -in 'Owner', 'Contributor' })
  # papeis personalizados (ex.: "Contributor - Controlled Scope"): mostra o que eles NAO permitem
  foreach ($nome in $papeis) {
    $def = az role definition list --name $nome --query "[0].{tipo:roleType, acoes:permissions[0].actions, nao:permissions[0].notActions}" -o json 2>$null | ConvertFrom-Json
    if ($def -and $def.tipo -eq 'CustomRole') {
      "papel personalizado '$nome': permite [$(@($def.acoes) -join ', ')]"
      if (@($def.nao).Count) { "  NAO permite: $(@($def.nao) -join ', ')" } else { "  sem restricoes (notActions vazio)" }
      if (@($def.acoes) -contains '*') { $podeCriar = $true }
    }
  }
  if (-not $podeCriar) { "ATENCAO: nenhum papel com '*' (Owner/Contributor). Se usa PIM, ative o papel e rode de novo." }

  "== Resource providers (precisam estar Registered)"
  $naoRegistrados = @()
  foreach ($p in 'Microsoft.Web', 'Microsoft.Sql', 'Microsoft.Logic') {
    $st = az provider show -n $p --query registrationState -o tsv
    "$p : $st"
    if ($st -ne 'Registered') { $naoRegistrados += $p }
  }
  if ($naoRegistrados.Count) { "  -> no modo criar, o script registra: $($naoRegistrados -join ', ') (leva 1-3 min)" }

  "== Nomes (Web App e SQL precisam ser unicos no Azure inteiro)"
  if ((az group exists -n $rg) -eq 'true') { "RG $rg ja existe (sera mantido)" } else { "RG $rg sera criado" }
  foreach ($h in "$app.azurewebsites.net", "$sqlServer.database.windows.net") {
    try { [Net.Dns]::GetHostAddresses($h) | Out-Null; "em uso: $h (ok se for deste RG; senao, troque o nome)" }
    catch { "livre: $h" }
  }

  "== Conector de e-mail '$mailConnector' em $location"
  $api = az rest --method get --url "https://management.azure.com$($apiId)?api-version=2016-06-01" --query "properties.generalInformation.displayName" -o tsv 2>$null
  if ($api) { "disponivel: $api" } else { "ATENCAO: conector nao encontrado na regiao (ou bloqueado)" }

  "== Policies que valem na assinatura, inclusive herdadas do management group (podem barrar regiao, tags ou SKU)"
  $pol = @(az policy assignment list --scope "/subscriptions/$subscription" --disable-scope-strict-match --query "[].{n:displayName, e:enforcementMode}" -o json 2>$null | ConvertFrom-Json | ForEach-Object { $_ } | Where-Object { $_.n })
  if ($pol.Count) { $pol | ForEach-Object { "  - $($_.n) [$($_.e)]" } } else { "  (nenhuma encontrada ou sem permissao para ler)" }

  "== Sera criado em $rg ($location), com as tags: $(($tags.Keys | ForEach-Object { "$_=$($tags[$_])" }) -join '; ')"
  "  App Service Plan  $planName (Linux $planSku)"
  "  Web App           $app (Python 3.12, always on $alwaysOn, so HTTPS, TLS 1.2)"
  "  SQL Server        $sqlServer (admin $sqlAdmin, TLS 1.2) + regra AllowAzureServices"
  "  Banco             $sqlDb (Basic, 2 GB, backup local)"
  "  Conexao           $mailConnection ($mailConnector, precisa autorizar depois no portal)"
  "  Logic App         $logicName (Consumption, gatilho HTTP + acao Enviar_email)"

  if ($modo -ne 'criar') {
    "== FIM da validacao: nada foi criado. Se estiver tudo certo, rode: Dash-Recursos -Modo criar"
    return
  }
  if (-not $podeCriar) {
    $r = Read-Host "Nenhum papel com permissao total foi encontrado. Tentar criar mesmo assim? (s/n)"
    if ($r -ne 's') { Falhar "cancelado pelo usuario" }
  }

  # ------------------------------------------------------------------ criacao
  do { $sec = Read-Host "Senha do admin do SQL (min. 12: maiuscula, minuscula, numero e simbolo). GUARDE: e pedida de novo depois" -AsSecureString } while ($sec.Length -eq 0)   # vazio = colagem nao entrou: pergunta de novo
  $senhaSql = ConvertFrom-SecureString $sec -AsPlainText   # Cloud Shell e PowerShell 7 (no Linux, Marshal::PtrToString* falha)
  if ($senhaSql.Length -lt 12) { Falhar "senha curta demais" }

  foreach ($p in $naoRegistrados) {
    "== Registrando o provider $p (1-3 min)"
    az provider register -n $p --wait -o none
    if ($LASTEXITCODE -ne 0) { Falhar "nao registrou $p (peca ao time de cloud: az provider register -n $p)" }
  }

  "== 1) Resource Group"
  if ((az group exists -n $rg) -eq 'true') { "ja existe" }
  else { az group create -n $rg -l $location @tagArgs -o none; if ($LASTEXITCODE -ne 0) { Falhar "nao criou o RG" }; "OK" }

  "== 2) Azure SQL"
  if (Existe @('sql', 'server', 'show', '-g', $rg, '-n', $sqlServer, '--query', 'name', '-o', 'tsv')) { "servidor ja existe (a senha NAO e alterada)" }
  else {
    az sql server create -g $rg -n $sqlServer -l $location -u $sqlAdmin -p $senhaSql --minimal-tls-version 1.2 -o none
    if ($LASTEXITCODE -ne 0) { Falhar "nao criou o servidor SQL" }
    az resource tag -g $rg -n $sqlServer --resource-type Microsoft.Sql/servers @tagArgs -o none
  }
  if (Existe @('sql', 'db', 'show', '-g', $rg, '-s', $sqlServer, '-n', $sqlDb, '--query', 'name', '-o', 'tsv')) { "banco ja existe" }
  else {
    az sql db create -g $rg -s $sqlServer -n $sqlDb --service-objective Basic --max-size 2GB --backup-storage-redundancy Local @tagArgs -o none
    if ($LASTEXITCODE -ne 0) { Falhar "nao criou o banco" }
  }
  if (-not (Existe @('sql', 'server', 'firewall-rule', 'show', '-g', $rg, '-s', $sqlServer, '-n', 'AllowAzureServices', '--query', 'name', '-o', 'tsv'))) {
    az sql server firewall-rule create -g $rg -s $sqlServer -n AllowAzureServices --start-ip-address 0.0.0.0 --end-ip-address 0.0.0.0 -o none
  }
  "OK"

  "== 3) App Service Plan + Web App"
  if (-not (Existe @('appservice', 'plan', 'show', '-g', $rg, '-n', $planName, '--query', 'name', '-o', 'tsv'))) {
    az appservice plan create -g $rg -n $planName -l $location --is-linux --sku $planSku @tagArgs -o none
    if ($LASTEXITCODE -ne 0) { Falhar "nao criou o App Service Plan" }
  }
  if (-not (Existe @('webapp', 'show', '-g', $rg, '-n', $app, '--query', 'name', '-o', 'tsv'))) {
    az webapp create -g $rg -n $app -p $planName --runtime "PYTHON:3.12" @tagArgs -o none
    if ($LASTEXITCODE -ne 0) { Falhar "nao criou o Web App" }
  }
  az webapp update -g $rg -n $app --https-only true -o none
  az webapp config set -g $rg -n $app --always-on $alwaysOn --ftps-state FtpsOnly --min-tls-version 1.2 `
    --startup-file "python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 1" -o none
  $f = Join-Path $HOME ("app_settings_" + [Guid]::NewGuid().ToString("N") + ".json")
  try {
    [ordered]@{
      FINOPS_REQUIRE_AUTH = "1"; WEBSITES_PORT = "8000"; SCM_DO_BUILD_DURING_DEPLOYMENT = "true"
      WEBSITE_HTTPLOGGING_RETENTION_DAYS = "7"; FINOPS_SQL_SERVER = "$sqlServer.database.windows.net"
      FINOPS_SQL_DB = $sqlDb; FINOPS_SQL_USER = $sqlAdmin; FINOPS_SQL_PASSWORD = $senhaSql
    } | ConvertTo-Json | Set-Content -Path $f
    az webapp config appsettings set -g $rg -n $app --settings "@$f" -o none
    if ($LASTEXITCODE -ne 0) { Falhar "nao gravou os appsettings" }
  } finally { Remove-Item $f -ErrorAction SilentlyContinue }   # o arquivo tinha a senha do SQL
  "OK"

  "== 7) Conexao de e-mail + Logic App (Consumption)"
  PutArm "$arm/Microsoft.Web/connections/$($mailConnection)?api-version=2016-06-01" @{
    location = $location; tags = $tags
    properties = @{ displayName = $mailConnection; api = @{ id = $apiId } }
  }
  $connId = "/subscriptions/$subscription/resourceGroups/$rg/providers/Microsoft.Web/connections/$mailConnection"
  PutArm "$arm/Microsoft.Logic/workflows/$($logicName)?api-version=2019-05-01" @{
    location = $location; tags = $tags
    properties = @{
      state = 'Enabled'
      definition = @{
        '$schema' = 'https://schema.management.azure.com/providers/Microsoft.Logic/schemas/2016-06-01/workflowdefinition.json#'
        contentVersion = '1.0.0.0'
        parameters = @{ '$connections' = @{ defaultValue = @{}; type = 'Object' } }
        triggers = @{ manual = @{ type = 'Request'; kind = 'Http'; inputs = @{ schema = @{ type = 'object' } } } }
        actions = @{
          Enviar_email = @{
            type = 'ApiConnection'; runAfter = @{}
            inputs = @{
              method = 'post'; path = '/v2/Mail'
              host = @{ connection = @{ name = "@parameters('`$connections')['email']['connectionId']" } }
              body = @{
                To = "@{triggerBody()?['email']}"; Subject = "@{triggerBody()?['assunto']}"; Body = "@{triggerBody()?['corpoHtml']}"
                Attachments = @(@{ Name = "@{triggerBody()?['anexoNome']}"; ContentBytes = "@{triggerBody()?['anexoBase64']}" })
              }
            }
          }
        }
        outputs = @{}
      }
      parameters = @{ '$connections' = @{ value = @{ email = @{ connectionId = $connId; connectionName = $mailConnection; id = $apiId } } } }
    }
  }
  "OK"

  "== Recursos em ${rg}:"
  az resource list -g $rg --query "[].{nome:name, tipo:type}" -o table
  "== FIM. Peca o App Registration com a Redirect URI: https://$app.azurewebsites.net/.auth/login/aad/callback"
  "   Depois: autorizar a conexao '$mailConnection' no portal (API connection > Edit API connection > Authorize > Save)."

}

"Funcao Dash-Recursos carregada (nada foi executado). Para validar: Dash-Recursos   |   para criar: Dash-Recursos -Modo criar"
