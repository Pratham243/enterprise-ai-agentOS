# =============================================================================
# Enterprise AI AgentOS — Terraform (Azure)
# =============================================================================
# Defines the cloud infrastructure as code. Apply with:
#   cd infrastructure && terraform init && terraform plan
#
# This creates:
# - A resource group
# - An Azure Container Instance running the Docker image
# - An Azure Database for PostgreSQL (flexible server)
# =============================================================================

terraform {
  required_version = ">= 1.5"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
}

variable "project_name" {
  default = "agentos"
}

variable "location" {
  default = "East US"
}

# --- Resource Group -----------------------------------------------------------
resource "azurerm_resource_group" "main" {
  name     = "rg-${var.project_name}"
  location = var.location
}

# --- PostgreSQL ---------------------------------------------------------------
resource "azurerm_postgresql_flexible_server" "main" {
  name                   = "${var.project_name}-pgserver"
  resource_group_name    = azurerm_resource_group.main.name
  location               = azurerm_resource_group.main.location
  version                = "16"
  administrator_login    = "agentosadmin"
  administrator_password = var.db_password
  sku_name               = "B_Standard_B1ms"
  storage_mb             = 32768
  zone                   = "1"
}

variable "db_password" {
  description = "PostgreSQL administrator password"
  type        = string
  sensitive   = true
}

resource "azurerm_postgresql_flexible_server_database" "main" {
  name      = var.project_name
  server_id = azurerm_postgresql_flexible_server.main.id
  charset   = "UTF8"
  collation = "en_US.utf8"
}

# --- Container Instance (API) ------------------------------------------------
resource "azurerm_container_group" "api" {
  name                = "${var.project_name}-api"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  os_type             = "Linux"
  ip_address_type     = "Public"

  container {
    name   = "api"
    image  = "${var.project_name}.azurecr.io/${var.project_name}:latest"
    cpu    = "1"
    memory = "1.5"

    ports {
      port     = 8000
      protocol = "TCP"
    }

    environment_variables = {
      APP_ENV = "production"
    }

    secure_environment_variables = {
      DATABASE_URL = "postgresql+asyncpg://${azurerm_postgresql_flexible_server.main.administrator_login}:${var.db_password}@${azurerm_postgresql_flexible_server.main.fqdn}:5432/${var.project_name}"
    }
  }
}

# --- Outputs ------------------------------------------------------------------
output "api_url" {
  value = "http://${azurerm_container_group.api.ip_address}:8000"
}

output "db_host" {
  value = azurerm_postgresql_flexible_server.main.fqdn
}
