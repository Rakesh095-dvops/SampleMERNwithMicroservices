# PowerShell script to set up AWS ECR and create a Kubernetes secret

# Set your AWS region
$AWS_REGION = "ap-south-1"

# Get your AWS Account ID automatically
$AWS_ACCOUNT_ID = (aws sts get-caller-identity --query Account --output text).Trim()
$ECR_PASSWORD = (aws ecr get-login-password --region $AWS_REGION).Trim()
$ECR_SERVER = "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"

Write-Host "AWS Account ID: $AWS_ACCOUNT_ID"
Write-Host "ECR Password is $ECR_PASSWORD"
Write-Host "ECR Server is $ECR_SERVER"

kubectl create secret docker-registry ecr-registry-secret `
  --docker-server=$ECR_SERVER `
  --docker-username=AWS `
  --docker-password=$ECR_PASSWORD `
  --docker-email="no-reply@example.com" -n sample-mern

