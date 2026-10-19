terraform {
  required_version = ">= 1.6"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
  }

  # State remoto: descomente e preencha apos criar o Storage de state
  # (ver infra/README.md, secao 5). Nunca versionar o state no Git.
  # backend "azurerm" {
  #   resource_group_name  = "rg-tfstate"
  #   storage_account_name = "sttfstatexxxx"
  #   container_name       = "tfstate"
  #   key                  = "dash-finops.tfstate"
  #   use_oidc             = true
  # }
}

provider "azurerm" {
  features {}
  subscription_id = var.subscription_id
}
