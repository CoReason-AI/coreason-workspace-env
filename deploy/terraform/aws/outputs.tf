output "eks_cluster_endpoint" {
  description = "Endpoint for EKS cluster"
  value       = module.eks.cluster_endpoint
}

output "postgres_endpoint" {
  description = "Endpoint for RDS Postgres"
  value       = module.db.db_instance_address
}

output "redis_endpoint" {
  description = "Endpoint for ElastiCache Redis"
  value       = aws_elasticache_cluster.redis.cache_nodes[0].address
}
