# atualizar_poc_dados.ps1 - deixa o banco da POC (Azure SQL) igual ao banco local (database\finops_dev.db).
#
# Como rodar (na raiz do repo, com o .venv ativo e depois de 'az login'):
#   powershell -ExecutionPolicy Bypass -File infra\atualizar_poc_dados.ps1
#
# SUBSTITUI os dados da POC pelos do local. Antes de apagar qualquer coisa:
#   - confere setembro do local contra o golden (se nao bater, nao copia nada);
#   - mostra as alteracoes que existem SO na POC e pede confirmacao se houver alguma.
# O app fica parado durante a copia (1-3 min) para nao ler tabelas pela metade e volta no fim.
# O Azure SQL guarda backup automatico (restauracao por ponto no tempo, 7 dias no Basic).
# Nomes vem do 'terraform output'. A senha do SQL e pedida e nao e gravada. ASCII only.

$repo    = Split-Path -Parent $PSScriptRoot
$infra   = Join-Path $repo "infra"
$dbLocal = Join-Path $repo "database\finops_dev.db"
$ProgressPreference = 'SilentlyContinue'

function Falhar($msg) { "ABORTADO: $msg"; exit 1 }
function TfOut($nome) { (terraform -chdir="$infra" output -raw $nome 2>$null) }

if (-not (az account show --query id -o tsv 2>$null)) { Falhar "rode 'az login' antes" }
python -c "import pymssql" 2>$null
if ($LASTEXITCODE -ne 0) { Falhar "ative o .venv (precisa de pymssql)" }
if (-not (Test-Path $dbLocal)) { Falhar "banco local nao encontrado: $dbLocal" }

$rg = TfOut "resource_group"; $appUrl = TfOut "app_url"; $sqlFqdn = TfOut "sql_server_fqdn"
if (-not $rg -or -not $appUrl -or -not $sqlFqdn) { Falhar "sem 'terraform output' em infra\" }
$app = ([Uri]$appUrl).Host.Split('.')[0]
$srvSql = $sqlFqdn.Split('.')[0]
$sqlDb   = az webapp config appsettings list -g $rg -n $app --query "[?name=='FINOPS_SQL_DB'].value | [0]" -o tsv
$sqlUser = az webapp config appsettings list -g $rg -n $app --query "[?name=='FINOPS_SQL_USER'].value | [0]" -o tsv
if (-not $sqlDb -or -not $sqlUser) { Falhar "nao li FINOPS_SQL_DB/FINOPS_SQL_USER do web app $app" }
"POC: $appUrl | SQL: $srvSql/$sqlDb | local: $dbLocal"

Set-Location $repo
"== 1) Setembro do local contra o golden"
python tools\verifica_numeros.py VERIFICAR $dbLocal 2026-09
if ($LASTEXITCODE -ne 0) { Falhar "o banco local nao bate com o golden de setembro; nada foi copiado" }

$sec = Read-Host "Senha do admin do SQL da POC" -AsSecureString
$env:FINOPS_SQL_PASSWORD = [Runtime.InteropServices.Marshal]::PtrToStringBSTR([Runtime.InteropServices.Marshal]::SecureStringToBSTR($sec))
$env:FINOPS_SQL_SERVER = $sqlFqdn; $env:FINOPS_SQL_DB = $sqlDb; $env:FINOPS_SQL_USER = $sqlUser

$meuIp = (Invoke-RestMethod -UseBasicParsing https://api.ipify.org).Trim()
"== 2) Liberando o IP $meuIp no SQL (regra temporaria 'meu-ip', removida no fim)"
az sql server firewall-rule create -g $rg -s $srvSql -n meu-ip --start-ip-address $meuIp --end-ip-address $meuIp -o none
$appParado = $false
try {
  "== 3) Alteracoes que existem SO na POC (somente leitura)"
  python tools\diferencas_poc.py $dbLocal
  $rc = $LASTEXITCODE
  if ($rc -eq 3) {
    $r = Read-Host "Essas alteracoes da POC serao PERDIDAS. Continuar mesmo assim? (s/n)"
    if ($r -ne 's') { Falhar "cancelado: refaca essas alteracoes no dash local e rode de novo" }
  } elseif ($rc -ne 0) { Falhar "nao consegui comparar com a POC (senha? firewall?)" }

  "== 4) Parando o app e copiando local -> POC (confere contagens, conteudo e somas)"
  az webapp stop -g $rg -n $app -o none; $appParado = $true
  python tools\migrar_sqlite_para_azure_sql.py $dbLocal APLICAR --recriar --triggers
  if ($LASTEXITCODE -ne 0) { Falhar "a copia/conferencia falhou: veja acima (o backup automatico do Azure SQL permite restaurar)" }
} finally {
  Remove-Item Env:FINOPS_SQL_PASSWORD, Env:FINOPS_SQL_SERVER, Env:FINOPS_SQL_DB, Env:FINOPS_SQL_USER -ErrorAction SilentlyContinue
  az sql server firewall-rule delete -g $rg -s $srvSql -n meu-ip -o none 2>$null
  "firewall: regra 'meu-ip' removida"
  if ($appParado) { az webapp start -g $rg -n $app -o none; "app iniciado de novo" }
}
"== FIM: a POC esta igual ao local. Abra $appUrl (o 1o acesso leva ~1 min para aquecer)."
