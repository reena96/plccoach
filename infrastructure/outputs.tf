# PLC Coach - Terraform Outputs

output "vpc_id" {
  description = "ID of the VPC"
  value       = data.aws_vpc.default.id
}

output "public_subnet_ids" {
  description = "IDs of public subnets"
  value       = [data.aws_subnet.default_az1.id, data.aws_subnet.default_az2.id]
}

output "private_subnet_ids" {
  description = "IDs of subnets used for RDS/ECS (using default VPC subnets)"
  value       = [data.aws_subnet.default_az1.id, data.aws_subnet.default_az2.id]
}

output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = aws_lb.main.dns_name
}

output "alb_zone_id" {
  description = "Zone ID of the Application Load Balancer"
  value       = aws_lb.main.zone_id
}

output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = aws_ecs_cluster.main.name
}

output "ecs_cluster_arn" {
  description = "ARN of the ECS cluster"
  value       = aws_ecs_cluster.main.arn
}

output "ecr_repository_url" {
  description = "URL of the ECR repository for API service"
  value       = aws_ecr_repository.api.repository_url
}

output "rds_endpoint" {
  description = "Endpoint of the RDS instance"
  value       = aws_db_instance.main.endpoint
  sensitive   = true
}

output "rds_database_name" {
  description = "Name of the database"
  value       = aws_db_instance.main.db_name
}

output "db_secret_arn" {
  description = "ARN of the database password secret"
  value       = aws_secretsmanager_secret.db_password.arn
  sensitive   = true
}

output "s3_content_bucket" {
  description = "Name of S3 bucket for content"
  value       = aws_s3_bucket.content.id
}

output "s3_exports_bucket" {
  description = "Name of S3 bucket for exports"
  value       = aws_s3_bucket.exports.id
}

output "s3_backups_bucket" {
  description = "Name of S3 bucket for backups"
  value       = aws_s3_bucket.backups.id
}

output "s3_frontend_bucket" {
  description = "Name of S3 bucket for frontend assets"
  value       = aws_s3_bucket.frontend.id
}

output "cloudfront_distribution_id" {
  description = "ID of CloudFront distribution"
  value       = aws_cloudfront_distribution.frontend.id
}

output "cloudfront_domain_name" {
  description = "Domain name of CloudFront distribution"
  value       = aws_cloudfront_distribution.frontend.domain_name
}

output "cloudwatch_log_group_api" {
  description = "Name of CloudWatch log group for API"
  value       = aws_cloudwatch_log_group.ecs_api.name
}

output "sns_alarms_topic_arn" {
  description = "ARN of SNS topic for alarms"
  value       = aws_sns_topic.alarms.arn
}

output "ecs_task_execution_role_arn" {
  description = "ARN of ECS task execution role"
  value       = aws_iam_role.ecs_task_execution.arn
}

output "ecs_task_role_arn" {
  description = "ARN of ECS task role"
  value       = aws_iam_role.ecs_task.arn
}

output "target_group_arn" {
  description = "ARN of the primary target group"
  value       = aws_lb_target_group.api.arn
}

output "target_group_arn_alternate" {
  description = "ARN of the alternate target group (for blue-green)"
  value       = aws_lb_target_group.api_alternate.arn
}

output "alb_security_group_id" {
  description = "ID of ALB security group"
  value       = aws_security_group.alb.id
}

output "ecs_security_group_id" {
  description = "ID of ECS tasks security group"
  value       = aws_security_group.ecs_tasks.id
}

output "rds_security_group_id" {
  description = "ID of RDS security group"
  value       = aws_security_group.rds.id
}
