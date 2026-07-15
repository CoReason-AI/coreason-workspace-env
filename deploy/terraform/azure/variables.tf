variable "location" {
  description = "The Azure region to deploy to"
  type        = string
  default     = "East US"
}

variable "project_name" {
  description = "Project name prefix for resources"
  type        = string
  default     = "coreason"
}

variable "db_username" {
  description = "Postgres Administrator Login"
  type        = string
  default     = "coreason_admin"
}

variable "db_password" {
  description = "Postgres Administrator Password"
  type        = string
  sensitive   = true
}
