# ---------------------------------------------------------------- Azure SQL (banco da POC)
#
# Recursos criados a mao antes do Terraform: adote com `terraform import`
# (comandos no README desta pasta). A senha do admin NAO e gerenciada aqui
# (ignore_changes) e a variavel so serve para satisfazer o provider.
# Atencao: destroy + apply recria o banco VAZIO; depois rode
# tools/migrar_sqlite_para_azure_sql.py para recarregar os dados.

resource "azurerm_mssql_server" "this" {
  name                         = var.sql_server_name
  resource_group_name          = azurerm_resource_group.this.name
  location                     = var.sql_location
  version                      = "12.0"
  administrator_login          = var.sql_admin_login
  administrator_login_password = var.sql_admin_password
  minimum_tls_version          = "1.2"
  tags                         = var.tags

  lifecycle {
    ignore_changes = [administrator_login_password]
  }
}

resource "azurerm_mssql_database" "finops" {
  name        = var.sql_db_name
  server_id   = azurerm_mssql_server.this.id
  sku_name    = "Basic"
  max_size_gb = 2
  tags        = var.tags

  # Collation/redundancia de backup podem divergir do default do provider no
  # banco criado a mao; nao force recriacao por isso.
  lifecycle {
    ignore_changes = [collation, storage_account_type, license_type]
  }
}

# 0.0.0.0 - 0.0.0.0 = "Permitir servicos do Azure" (o web app acessa por aqui).
# Regras de IP pessoais (meu-ip, pc-rafael-evertec) ficam FORA do Terraform.
resource "azurerm_mssql_firewall_rule" "azure_services" {
  name             = "AllowAzureServices"
  server_id        = azurerm_mssql_server.this.id
  start_ip_address = "0.0.0.0"
  end_ip_address   = "0.0.0.0"
}
