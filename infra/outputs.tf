output "app_url" {
  value = "https://${azurerm_linux_web_app.this.default_hostname}"
}

output "resource_group" {
  value = azurerm_resource_group.this.name
}

output "redirect_uri_a_cadastrar" {
  description = "Adicionar em Authentication > Redirect URIs da App Registration existente."
  value       = "https://${azurerm_linux_web_app.this.default_hostname}/.auth/login/aad/callback"
}

output "sql_server_fqdn" {
  value = azurerm_mssql_server.this.fully_qualified_domain_name
}
