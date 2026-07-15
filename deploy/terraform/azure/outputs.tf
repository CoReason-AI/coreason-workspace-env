output "aks_cluster_name" {
  description = "Name of the AKS cluster"
  value       = azurerm_kubernetes_cluster.aks.name
}

output "postgres_fqdn" {
  description = "FQDN for PostgreSQL"
  value       = azurerm_postgresql_flexible_server.postgres.fqdn
}

output "redis_hostname" {
  description = "Hostname for Redis Cache"
  value       = azurerm_redis_cache.redis.hostname
}
