output "name" {
  description = "The name of the application"
  value       = var.name
}

output "vpc_id" {
  description = "The ID of the VPC"
  value       = module.vpc.vpc_id
}

output "ecs_cluster_name" {
  description = "The name of the ecs cluster that was created or referenced"
  value       = module.ecs_cluster.name
}

output "ecs_cluster_arn" {
  description = "The arn of the ecs cluster that was created or referenced"
  value       = module.ecs_cluster.arn
}

output "ecs_service_name" {
  description = "The arn of the fargate ecs service that was created"
  value       = module.ecs_service.name
}

output "lb_arn" {
  description = "The arn of the load balancer"
  value       = module.alb.arn
}

output "lb_dns" {
  description = "The load balancer DNS name"
  value       = module.alb.dns_name
}

output "endpoint" {
  description = "The web application endpoint"
  value       = "http://${module.alb.dns_name}"
}

output "db_cluster_endpoint" {
  description = "The write endpoint for the database cluster"
  value       = module.aurora_postgres.cluster_endpoint
}

output "db_cluster_arn" {
  description = "The ARN of the database cluster"
  value       = local.aurora_cluster_arn
}

output "db_creds_secret_arn" {
  description = "The ARN of the secret that contains the database credentials"
  value       = local.aurora_secret_arn
}

output "db_creds_bedrock_secret_arn" {
  description = "The name of the secret that contains the database credentials for Bedrock"
  value       = local.bedrock_user_secret
}

output "bedrock_knowledge_base_id" {
  description = "the id of the created bedrock knowledge base"
  value       = aws_bedrockagent_knowledge_base.main.id
}

output "bedrock_knowledge_base_data_source_id" {
  description = "the id of the created bedrock knowledge base data source"
  value       = aws_bedrockagent_data_source.main.data_source_id
}

output "s3_bucket_name" {
  description = "The name of the s3 bucket that was created"
  value       = aws_s3_bucket.main.bucket
}
