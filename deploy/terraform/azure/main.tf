terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.12"
    }
  }
}

provider "azurerm" {
  features {}
}

resource "azurerm_resource_group" "rg" {
  name     = "${var.project_name}-rg"
  location = var.location
}

# AKS Cluster
resource "azurerm_kubernetes_cluster" "aks" {
  name                = "${var.project_name}-aks"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  dns_prefix          = "${var.project_name}aks"

  default_node_pool {
    name       = "default"
    node_count = 3
    vm_size    = "Standard_D2_v2"
  }

  identity {
    type = "SystemAssigned"
  }
}

# Azure Database for PostgreSQL Flexible Server
resource "azurerm_postgresql_flexible_server" "postgres" {
  name                = "${var.project_name}-psql"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  version             = "15"
  administrator_login = var.db_username
  administrator_password = var.db_password
  storage_mb          = 32768
  sku_name            = "Standard_B1ms"
  zone                = "1"
}

# Azure Cache for Redis
resource "azurerm_redis_cache" "redis" {
  name                = "${var.project_name}-redis"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  capacity            = 1
  family              = "C"
  sku_name            = "Basic"
}

provider "helm" {
  kubernetes {
    host                   = azurerm_kubernetes_cluster.aks.kube_config.0.host
    client_certificate     = base64decode(azurerm_kubernetes_cluster.aks.kube_config.0.client_certificate)
    client_key             = base64decode(azurerm_kubernetes_cluster.aks.kube_config.0.client_key)
    cluster_ca_certificate = base64decode(azurerm_kubernetes_cluster.aks.kube_config.0.cluster_ca_certificate)
  }
}

resource "helm_release" "coreason_platform" {
  name       = "coreason-platform"
  chart      = "../../../helm/coreason-platform"
  depends_on = [azurerm_kubernetes_cluster.aks, azurerm_postgresql_flexible_server.postgres, azurerm_redis_cache.redis]

  set {
    name  = "env.POSTGRES_HOST"
    value = azurerm_postgresql_flexible_server.postgres.fqdn
  }

  set {
    name  = "env.POSTGRES_USER"
    value = var.db_username
  }

  set {
    name  = "env.POSTGRES_PASSWORD"
    value = var.db_password
  }

  set {
    name  = "env.REDIS_URL"
    value = "redis://${azurerm_redis_cache.redis.hostname}:${azurerm_redis_cache.redis.ssl_port}/0"
  }
}
