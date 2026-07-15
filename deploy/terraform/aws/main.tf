terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.12"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# Network setup
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "${var.project_name}-vpc"
  cidr = var.vpc_cidr

  azs             = ["${var.aws_region}a", "${var.aws_region}b", "${var.aws_region}c"]
  private_subnets = var.private_subnets
  public_subnets  = var.public_subnets

  enable_nat_gateway = true
  single_nat_gateway = true
}

# EKS Cluster
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 19.0"

  cluster_name    = "${var.project_name}-cluster"
  cluster_version = "1.28"

  vpc_id                         = module.vpc.vpc_id
  subnet_ids                     = module.vpc.private_subnets
  cluster_endpoint_public_access = true

  eks_managed_node_groups = {
    coreason_nodes = {
      min_size     = 1
      max_size     = 10
      desired_size = 3
      instance_types = ["t3.large"]
    }
  }
}

# RDS Postgres
module "db" {
  source  = "terraform-aws-modules/rds/aws"
  version = "~> 6.0"

  identifier = "${var.project_name}-postgres"
  engine               = "postgres"
  engine_version       = "15"
  family               = "postgres15"
  major_engine_version = "15"
  instance_class       = "db.t3.micro"
  allocated_storage    = 20
  db_name              = "langgraph_state"
  username             = var.db_username
  password             = var.db_password
  port                 = 5432
  vpc_security_group_ids = [module.vpc.default_security_group_id]
  create_db_subnet_group = true
  subnet_ids             = module.vpc.private_subnets
}

# ElastiCache Redis
resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "${var.project_name}-redis"
  engine               = "redis"
  node_type            = "cache.t3.micro"
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  engine_version       = "7.1"
  port                 = 6379
  security_group_ids   = [module.vpc.default_security_group_id]
  subnet_group_name    = aws_elasticache_subnet_group.redis_subnet_group.name
}

resource "aws_elasticache_subnet_group" "redis_subnet_group" {
  name       = "${var.project_name}-redis-subnet"
  subnet_ids = module.vpc.private_subnets
}

provider "helm" {
  kubernetes {
    host                   = module.eks.cluster_endpoint
    cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority_data)
    exec {
      api_version = "client.authentication.k8s.io/v1beta1"
      args        = ["eks", "get-token", "--cluster-name", module.eks.cluster_name]
      command     = "aws"
    }
  }
}

resource "helm_release" "coreason_platform" {
  name       = "coreason-platform"
  chart      = "../../../helm/coreason-platform"
  depends_on = [module.eks, module.db, aws_elasticache_cluster.redis]

  set {
    name  = "env.POSTGRES_HOST"
    value = module.db.db_instance_address
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
    value = "redis://${aws_elasticache_cluster.redis.cache_nodes[0].address}:6379/0"
  }
}
