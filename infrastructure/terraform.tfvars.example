# PLC Coach - Terraform Variables Example
# Copy this file to terraform.tfvars and customize for your environment

aws_region  = "us-east-1"
environment = "production"

# Project Configuration
project_name = "plccoach"

# Network Configuration
vpc_cidr = "10.0.0.0/16"

# Database Configuration
db_instance_class = "db.t3.medium"  # Use db.t3.small for dev/staging
db_name           = "plccoach"
db_username       = "plccoach_admin"
enable_multi_az   = true  # Set to false for dev/staging to save costs

# ECS Configuration
ecs_task_cpu    = 512   # 0.5 vCPU
ecs_task_memory = 1024  # 1 GB RAM

# Logging
cloudwatch_log_retention_days = 90  # 30 for dev/staging

# Domain (optional - leave empty to use ALB DNS)
# domain_name = "plccoach.example.com"
domain_name = ""
