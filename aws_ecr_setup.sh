#!/bin/bash  
# Bash script  
echo "Hello World!"  
# This script sets up an AWS ECR repository and configures Docker to use it.
# Set your AWS region
AWS_REGION="ap-south-1" 
# Get your AWS Account ID automatically
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_PASSWORD=$(aws ecr get-login-password --region $AWS_REGION)
ECR_SERVER="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

echo "AWS Account ID: $AWS_ACCOUNT_ID"
echo "ECR Password is $ECR_PASSWORD"
echo "ECR Server is $ECR_SERVER"

kubectl create secret docker-registry ecr-registry-secret  --docker-server=$ECR_SERVER  --docker-username=AWS  --docker-password=$ECR_PASSWORD  --docker-email="no-reply@example.com"

echo "Docker registry secret 'ecr-registry-secret' created successfully."
# Verify the secret creation
kubectl get secret ecr-registry-secret
if [ $? -eq 0 ]; then
    echo "Secret 'ecr-registry-secret' created successfully."
else
    echo "Failed to create secret 'ecr-registry-secret'."
    exit 1
