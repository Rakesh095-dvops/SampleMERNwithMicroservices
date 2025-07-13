# EKS Setup and Deployment Guide for MERN Microservices
Collecting workspace information# EKS Setup and Deployment Guide for MERN Microservices

This guide outlines the steps needed to set up and deploy your MERN microservices application on AWS EKS using Terraform and Helm.

## Prerequisites and Resource Creation

Before running Terraform to create the EKS cluster, you need to set up the following resources:

### 1. AWS CLI Setup

```bash
# Install AWS CLI (if not already installed)
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Configure AWS CLI with your credentials
aws configure
```

### 2. Create S3 Bucket for Terraform State

This step has already been covered in [instruction.md](c:\Devops\CodeBase\k8s\SampleMERNwithMicroservices\terraform\instruction.md), but here are the commands again:

```bash
# Create the bucket
aws s3api create-bucket --bucket rikhrv-terraform-state-bucket --region ap-south-1 --create-bucket-configuration LocationConstraint=ap-south-1

# Enable versioning
aws s3api put-bucket-versioning --bucket rikhrv-terraform-state-bucket --versioning-configuration Status=Enabled

# Enable encryption
aws s3api put-bucket-encryption --bucket rikhrv-terraform-state-bucket --server-side-encryption-configuration '{"Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]}'
```

### 3. Create IAM Role for Jenkins


### 4. Running Terraform to Create EKS Cluster

Ensure `terraform` has been set up completely.

Now that the prerequisites are set up, you can run Terraform to create the EKS cluster:

```bash
cd terraform

# Initialize Terraform
terraform init

# Plan the changes
terraform plan -out=tfplan

# Apply the changes
terraform apply tfplan

# Capture outputs for later use
terraform output > terraform_outputs.txt

# output tfplan to json 
terraform show -json tfplan > myplan.json 
```

## Configure kubectl for EKS Access

```bash
# Update kubeconfig to connect to the EKS cluster
aws eks update-kubeconfig --region $(terraform output -raw region)  --name $(terraform output -raw cluster_name)   --kubeconfig ./kubeconfig

# Export KUBECONFIG to use the new config file
export KUBECONFIG=./kubeconfig

# Verify connection to the cluster
kubectl get nodes
```

## Build and Push Docker Images to ECR

```bash
# Get ECR repository URLs from Terraform outputs
HELLO_SERVICE_REPO=$(terraform output -raw ecr_hello_service_url)
PROFILE_SERVICE_REPO=$(terraform output -raw ecr_profile_service_url)
FRONTEND_REPO=$(terraform output -raw ecr_frontend_url)

# Login to ECR
aws ecr get-login-password --region ap-south-1 | docker login --username AWS --password-stdin $(echo $HELLO_SERVICE_REPO | cut -d'/' -f1)

# Build and push the Docker images
cd ../src/backend/hello-service
docker build -t $HELLO_SERVICE_REPO:latest .
docker push $HELLO_SERVICE_REPO:latest

cd ../profile-service
docker build -t $PROFILE_SERVICE_REPO:latest .
docker push $PROFILE_SERVICE_REPO:latest

cd ../../frontend
docker build -t $FRONTEND_REPO:latest .
docker push $FRONTEND_REPO:latest
```

## Create ECR Registry Secret in Kubernetes

```bash
# Create namespace
kubectl create namespace sample-mern

# Create ECR registry secret
kubectl create secret docker-registry ecr-registry-secret \
  --namespace sample-mern \
  --docker-server=$(echo $HELLO_SERVICE_REPO | cut -d'/' -f1) \
  --docker-username=AWS \
  --docker-password=$(aws ecr get-login-password --region ap-south-1) \
  --docker-email=no-reply@example.com
```

## Deploy with Helm

```bash
# Navigate to the root directory
cd ../../../

# Update Helm dependencies
helm dependency update mern-app

# Create values override file
cat > values-override.yaml << EOF
global:
  environment: eks
  registry:
    eks:
      url: $(echo $HELLO_SERVICE_REPO | cut -d'/' -f1)
EOF

# Deploy with Helm
helm install mern-app ./mern-app \
  --namespace sample-mern \
  --values values-override.yaml
```

## Verify Deployment

```bash
# Check pods
kubectl get pods -n sample-mern

# Check services
kubectl get services -n sample-mern

# Get LoadBalancer endpoints
FRONTEND_LB=$(kubectl get svc frontend -n sample-mern -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
HELLO_LB=$(kubectl get svc hello-service -n sample-mern -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
PROFILE_LB=$(kubectl get svc profile-service -n sample-mern -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

echo "Frontend URL: http://$FRONTEND_LB"
echo "Hello Service URL: http://$HELLO_LB"
echo "Profile Service URL: http://$PROFILE_LB"
```

## Configure CloudFlare (Optional)

If you want to set up CloudFlare as mentioned in [README_HELM_ECR.md](c:\Devops\CodeBase\k8s\SampleMERNwithMicroservices\README_HELM_ECR.md), you'll need to:

1. Create a CloudFlare account if you don't have one
2. Add your domain to CloudFlare
3. Get your CloudFlare API token and Zone ID
4. Add the following Terraform code to your configuration:

```terraform
provider "cloudflare" {
  api_token = var.cloudflare_api_token
}

resource "cloudflare_record" "frontend" {
  zone_id = var.cloudflare_zone_id
  name    = "app"
  value   = kubernetes_service.frontend.status[0].load_balancer[0].ingress[0].hostname
  type    = "CNAME"
  proxied = true
}
```

## Additional Notes

- The terraform.tfvars file contains configuration specific to your environment:
  - Region: ap-south-1
  - Cluster name: rikhrv-mern-app-cluster
  - ECR prefix: rikhrv
  - Jenkins role ARN: arn:aws:iam::975050024946:role/jenkins_rikhrv

- For CI/CD with Jenkins, you can use the provided [Jenkinsfile](c:\Devops\CodeBase\k8s\SampleMERNwithMicroservices\Jenkinsfile) which already contains the necessary steps to:
  - Set up kubectl and Helm
  - Update kubeconfig
  - Create namespace
  - Build and push Docker images
  - Deploy with Helm

- The Terraform resources create:
  - VPC with public and private subnets
  - EKS cluster with managed node groups
  - ECR repositories for your services
  - IAM roles for EKS and Jenkins integration
  - CloudWatch Log Group for EKS

