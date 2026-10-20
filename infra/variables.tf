variable "subscription_id" {
  description = "Subscription onde a infra sera criada."
  type        = string
}

variable "tenant_id" {
  description = "Tenant do Entra ID (usado no issuer do Easy Auth)."
  type        = string
}

variable "resource_group_name" {
  description = "Nome do Resource Group a criar."
  type        = string
}

variable "app_name" {
  description = "Nome lógico do Web App. O hostname padrão real é retornado pelo Azure e pode conter hash/região."
  type        = string
}

variable "plan_name" {
  description = "Nome do App Service Plan."
  type        = string
}

variable "location" {
  description = "Regiao do plano e do Web App."
  type        = string
  default     = "centralus"
}

variable "logic_location" {
  description = "Regiao do Logic App e da conexao do Outlook."
  type        = string
  default     = "eastus2"
}

variable "plan_sku" {
  description = "SKU do plano (POC: B1)."
  type        = string
  default     = "B1"
}

variable "always_on" {
  description = "POC esta com false (cold start). Na empresa, true."
  type        = bool
  default     = false
}

variable "tags" {
  description = "Tags obrigatorias da empresa (POC nao tem nenhuma)."
  type        = map(string)
  default     = {}
}

# --- appsettings ---

variable "finops_db_path" {
  description = "Caminho do SQLite (so sem Azure SQL); tem que ficar em /home (persistente)."
  type        = string
  default     = "/home/data/finops.db"
}

variable "finops_backup" {
  description = "Valor de FINOPS_BACKUP (backup do SQLite; desligado com Azure SQL)."
  type        = string
  default     = "1"
}

variable "log_retention_days" {
  description = "Retencao dos logs HTTP em dias (WEBSITE_HTTPLOGGING_RETENTION_DAYS)."
  type        = number
  default     = 7
}

# --- Outlook / Logic App ---

variable "outlook_api_name" {
  description = "API gerenciada da conexao. POC: outlook (conta pessoal). Empresa: provavelmente office365."
  type        = string
  default     = "outlook"
}

# --- Easy Auth: usa App Registration EXISTENTE (com consent ja concedido) ---

variable "auth_client_id" {
  description = "Client ID da App Registration existente. O Terraform NAO cria nem altera a app."
  type        = string
}

variable "auth_allowed_audiences" {
  description = "Audiences aceitas. Vazio = api://<auth_client_id>. Conferir o que a app existente expoe."
  type        = list(string)
  default     = []
}

# --- Azure SQL ---

variable "sql_server_name" {
  description = "Nome do SQL Server logico (globalmente unico)."
  type        = string
  default     = "sql-dash-recomendacao-rb"
}

variable "sql_db_name" {
  type    = string
  default = "finops"
}

variable "sql_admin_login" {
  type    = string
  default = "dashadmin"
}

variable "sql_admin_password" {
  description = "Senha do admin. Usada so no 1o create; depois e ignorada (ignore_changes). Passe por TF_VAR_sql_admin_password."
  type        = string
  sensitive   = true
}

variable "sql_location" {
  description = "Regiao do SQL Server (no POC: centralus)."
  type        = string
  default     = "centralus"
}
