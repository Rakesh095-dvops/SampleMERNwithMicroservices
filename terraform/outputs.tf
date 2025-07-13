output "cluster_name" {
  description = "The name of the EKS cluster"
  value       = module.eks.cluster_name
}

output "cluster_endpoint" {
  description = "Endpoint for EKS control plane"
  value       = module.eks.cluster_endpoint
}

output "cluster_security_group_id" {
  description = "Security group ID attached to the EKS cluster"
  value       = module.eks.cluster_security_group_id
}

output "cluster_certificate_authority_data" {
  description = "Base64 encoded certificate data required to communicate with the cluster"
  value       = module.eks.cluster_certificate_authority_data
  sensitive   = true
}

output "region" {
  description = "AWS region"
  value       = var.region
}

output "ecr_hello_service_url" {
  description = "ECR repository URL for hello service"
  value       = aws_ecr_repository.hello_service.repository_url
}

output "ecr_profile_service_url" {
  description = "ECR repository URL for profile service"
  value       = aws_ecr_repository.profile_service.repository_url
}

output "ecr_frontend_url" {
  description = "ECR repository URL for frontend"
  value       = aws_ecr_repository.frontend.repository_url
}

output "eks_jenkins_role_arn" {
  description = "ARN of the IAM role for Jenkins to access EKS"
  value       = aws_iam_role.eks_jenkins_role.arn
}