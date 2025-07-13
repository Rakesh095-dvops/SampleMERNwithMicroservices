# VPC for EKS
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 3.0"

  name = "${var.cluster_name}-vpc"
  cidr = var.vpc_cidr

  azs             = var.availability_zones
  private_subnets = var.private_subnets
  public_subnets  = var.public_subnets

  enable_nat_gateway   = true
  single_nat_gateway   = true
  enable_dns_hostnames = true

  public_subnet_tags = {
    "kubernetes.io/cluster/${var.cluster_name}" = "shared"
    "kubernetes.io/role/elb"                    = "1"
  }

  private_subnet_tags = {
    "kubernetes.io/cluster/${var.cluster_name}" = "shared"
    "kubernetes.io/role/internal-elb"           = "1"
  }

  tags = var.tags
}

# EKS Cluster
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 18.0"

  cluster_name    = var.cluster_name
  cluster_version = var.cluster_version

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  cluster_endpoint_private_access = true
  cluster_endpoint_public_access  = true

  # EKS Managed Node Group
  eks_managed_node_groups = {
    default = {
      min_size     = var.node_group_min_size
      max_size     = var.node_group_max_size
      desired_size = var.node_group_desired_size
      instance_types = ["t3.medium"]
      capacity_type  = "ON_DEMAND"
    }
  }

  # AWS Auth roles/users
  manage_aws_auth_configmap = true
  aws_auth_roles = [
    {
      rolearn  = aws_iam_role.eks_jenkins_role.arn
      username = "jenkins"
      groups   = ["system:masters"]
    }
  ]

  tags = var.tags
}

# Create CloudWatch Log Group for EKS
resource "aws_cloudwatch_log_group" "eks" {
  name              = "/aws/eks/${var.cluster_name}/cluster"
  retention_in_days = 7
}

# ECR Repositories for MERN app
resource "aws_ecr_repository" "hello_service" {
  name                 = "${var.ecr_prefix}/hello-service"
  image_tag_mutability = "MUTABLE"
}

resource "aws_ecr_repository" "profile_service" {
  name                 = "${var.ecr_prefix}/profile-service"
  image_tag_mutability = "MUTABLE"
}

resource "aws_ecr_repository" "frontend" {
  name                 = "${var.ecr_prefix}/samplmernfrontend"
  image_tag_mutability = "MUTABLE"
}

# IAM Role for Jenkins to access EKS
resource "aws_iam_role" "eks_jenkins_role" {
  name = "eks-jenkins-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          AWS = var.jenkins_role_arn
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "eks_admin_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
  role       = aws_iam_role.eks_jenkins_role.name
}

resource "aws_iam_role_policy_attachment" "ecr_full_access" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonECR-FullAccess"
  role       = aws_iam_role.eks_jenkins_role.name
}

data "aws_caller_identity" "current" {}