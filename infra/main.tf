locals {
  hostname  = "${var.app_name}.azurewebsites.net"
  audiences = length(var.auth_allowed_audiences) > 0 ? var.auth_allowed_audiences : ["api://${var.auth_client_id}"]
}

resource "azurerm_resource_group" "this" {
  name     = var.resource_group_name
  location = var.location
  tags     = var.tags
}

# ---------------------------------------------------------------- App Service

resource "azurerm_service_plan" "this" {
  name                = var.plan_name
  resource_group_name = azurerm_resource_group.this.name
  location            = azurerm_resource_group.this.location
  os_type             = "Linux"
  sku_name            = var.plan_sku
  tags                = var.tags
}

resource "azurerm_linux_web_app" "this" {
  name                = var.app_name
  resource_group_name = azurerm_resource_group.this.name
  location            = azurerm_resource_group.this.location
  service_plan_id     = azurerm_service_plan.this.id
  https_only          = true
  tags                = var.tags

  site_config {
    always_on           = var.always_on
    ftps_state          = "FtpsOnly"
    minimum_tls_version = "1.2"
    app_command_line    = "python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 1"

    application_stack {
      python_version = "3.12"
    }
  }

  app_settings = {
    # FINOPS_DB_PATH e FINOPS_BACKUP so valem se o Azure SQL for desligado
    # (sem FINOPS_SQL_SERVER): o SQLite fica em /home, fora do pacote de deploy.
    FINOPS_DB_PATH                 = var.finops_db_path
    FINOPS_REQUIRE_AUTH            = "1"
    FINOPS_BACKUP                  = var.finops_backup
    WEBSITES_PORT                  = "8000"
    SCM_DO_BUILD_DURING_DEPLOYMENT = "true"
    FINOPS_SQL_SERVER              = azurerm_mssql_server.this.fully_qualified_domain_name
    FINOPS_SQL_DB                  = azurerm_mssql_database.finops.name
    FINOPS_SQL_USER                = var.sql_admin_login
    # FINOPS_SQL_PASSWORD: definido fora do Terraform (ver README).
  }

  # Retencao dos logs HTTP (no POC e o appsetting WEBSITE_HTTPLOGGING_RETENTION_DAYS,
  # que o provider so aceita por este bloco).
  logs {
    http_logs {
      file_system {
        retention_in_days = var.log_retention_days
        retention_in_mb   = 35
      }
    }
  }

  auth_settings_v2 {
    auth_enabled           = true
    require_authentication = true
    unauthenticated_action = "RedirectToLoginPage"
    default_provider       = "azureactivedirectory"
    require_https          = true

    login {}

    active_directory_v2 {
      client_id                  = var.auth_client_id
      client_secret_setting_name = "MICROSOFT_PROVIDER_AUTHENTICATION_SECRET"
      tenant_auth_endpoint       = "https://sts.windows.net/${var.tenant_id}/v2.0"
      allowed_audiences          = local.audiences
    }
  }

  lifecycle {
    # Deploy do codigo: zip/GitHub Actions, nao o Terraform.
    # O segredo do Easy Auth e definido FORA do Terraform (ver README) para
    # nunca entrar no state.
    ignore_changes = [
      zip_deploy_file,
      app_settings["MICROSOFT_PROVIDER_AUTHENTICATION_SECRET"],
      app_settings["LOGIC_APP_URL"],
      app_settings["FINOPS_EMAIL_OVERRIDE_TO"],
      app_settings["FINOPS_SQL_PASSWORD"],
    ]
  }
}

# ---------------------------------------------------------------- Logic App (alerta por e-mail)

data "azurerm_managed_api" "outlook" {
  name     = var.outlook_api_name
  location = var.logic_location
}

resource "azurerm_api_connection" "outlook" {
  name                = "outlook"
  resource_group_name = azurerm_resource_group.this.name
  managed_api_id      = data.azurerm_managed_api.outlook.id
  display_name        = "outlook"
  tags                = var.tags

  # A autorizacao OAuth da conexao e manual (portal > API connection >
  # Edit API connection > Authorize). O Terraform cria, mas ela fica
  # "Unauthenticated" ate alguem autorizar.
  lifecycle {
    ignore_changes = [parameter_values]
  }
}

resource "azurerm_logic_app_workflow" "alerta" {
  name                = "logic-finops-alerta-teste"
  resource_group_name = azurerm_resource_group.this.name
  location            = var.logic_location
  tags                = var.tags

  # Parametro $connections: liga a acao de e-mail a conexao do Outlook.
  workflow_parameters = {
    "$connections" = jsonencode({
      defaultValue = {}
      type         = "Object"
    })
  }

  parameters = {
    "$connections" = jsonencode({
      outlook = {
        connectionId   = azurerm_api_connection.outlook.id
        connectionName = "outlook"
        id             = data.azurerm_managed_api.outlook.id
      }
    })
  }
}

# Gatilho HTTP "manual" (igual ao do POC). A URL do gatilho e gerada pelo Azure
# e NAO entra no codigo nem no state: ver README (passo LOGIC_APP_URL).
resource "azurerm_logic_app_trigger_http_request" "manual" {
  name         = "manual"
  logic_app_id = azurerm_logic_app_workflow.alerta.id

  schema = jsonencode({
    type = "object"
  })
}

# Acao "Enviar_email": o dash envia email, assunto, corpoHtml e anexo no corpo do POST.
resource "azurerm_logic_app_action_custom" "enviar_email" {
  name         = "Enviar_email"
  logic_app_id = azurerm_logic_app_workflow.alerta.id

  body = jsonencode({
    type     = "ApiConnection"
    runAfter = {}
    inputs = {
      method = "post"
      path   = "/v2/Mail"
      host = {
        connection = {
          name = "@parameters('$connections')['outlook']['connectionId']"
        }
      }
      body = {
        To      = "@{triggerBody()?['email']}"
        Subject = "@{triggerBody()?['assunto']}"
        Body    = "@{triggerBody()?['corpoHtml']}"
        Attachments = [
          {
            Name         = "@{triggerBody()?['anexoNome']}"
            ContentBytes = "@{triggerBody()?['anexoBase64']}"
          }
        ]
      }
    }
  })

  depends_on = [azurerm_logic_app_trigger_http_request.manual]
}
