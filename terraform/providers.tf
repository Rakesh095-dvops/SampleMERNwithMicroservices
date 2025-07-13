terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
  
  backend "s3" {
    bucket = "rikhrv-terraform-state-bucket"
    key    = "eks/terraform.tfstate"
    region = "ap-south-1"
  }
}

provider "aws" {
  region = var.region
}