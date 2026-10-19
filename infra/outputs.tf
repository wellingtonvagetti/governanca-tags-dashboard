output "app_url" {
  value = "https://${local.hostname}"
}

output "resource_group" {
  value = azurerm_resource_group.this.name
}

output "redirect_uri_a_cadastrar" {
  description = "Adicionar em Authentication > Redirect URIs da App Registration existente."
  value       = "https://${local.hostname}/.auth/login/aad/callback"
}

output "sql_server_fqdn" {
  value = azurerm_mssql_server.this.fully_qualified_domain_name
}
