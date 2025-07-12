variable "region" {
  description = "AWS region"
  default     = "ap-south-1"
}

variable "project_name" {
  description = "Name of the project"
  default     = "mern-app"
}

variable "cluster_name" {
  description = "Name of the EKS cluster"
  default     = "my-eks-cluster"
}

variable "cluster_version" {
  description = "Kubernetes version"
  default     = "1.27"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
  default     = ["ap-south-1a", "ap-south-1b", "ap-south-1c"]
}

variable "private_subnets" {
  description = "List of private subnet CIDR blocks"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
}

variable "public_subnets" {
  description = "List of public subnet CIDR blocks"
  type        = list(string)
  default     = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]
}

variable "node_group_min_size" {
  description = "Minimum number of nodes"
  default     = 2
}

variable "node_group_max_size" {
  description = "Maximum number of nodes"
  default     = 5
}

variable "node_group_desired_size" {
  description = "Desired number of nodes"
  default     = 3
}

variable "ecr_prefix" {
  description = "Prefix for ECR repositories"
  default     = "rikhrv"
}

variable "tags" {
  description = "A map of tags to add to all resources"
  type        = map(string)
  default = {
    Environment = "Production"
    Project     = "MERN-Microservices"
    Terraform   = "true"
  }
}