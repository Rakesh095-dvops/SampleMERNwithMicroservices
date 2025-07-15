# Sample MERN with Microservices


For `helloService`, create `.env` file with the content:
```bash
PORT=3001
```

For `profileService`, create `.env` file with the content:
```bash
PORT=3002
MONGO_URL="specifyYourMongoURLHereWithDatabaseNameInTheEnd"
```

Finally install packages in both the services by running the command `npm install`.

<br/>
For frontend, you have to install and start the frontend server:

```bash
cd frontend
npm install
npm start
```

Note: This will run the frontend in the development server. To run in production, build the application by running the command `npm run build`

https://jenkinsacademics.herovired.com/

Step 4: Update Deployment Scripts for Authentication
For the deployment scripts, modify them to accept AWS credentials:

```to be deleted ```

# Additional Steps for External Jenkins to Access Private ECR Repositories

When Jenkins is hosted outside of AWS (managed by external vendors), you need additional configuration to access private ECR repositories.

## Step 1: Create IAM User for Jenkins

```bash
# Use AWS CLI to create an IAM user
aws iam create-user --user-name jenkins-ecr-user

# Create a policy for ECR access
aws iam create-policy --policy-name JenkinsECRPolicy --policy-document '{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ecr:GetAuthorizationToken",
                "ecr:BatchCheckLayerAvailability",
                "ecr:GetDownloadUrlForLayer",
                "ecr:BatchGetImage",
                "ecr:InitiateLayerUpload",
                "ecr:UploadLayerPart",
                "ecr:CompleteLayerUpload",
                "ecr:PutImage"
            ],
            "Resource": "*"
        }
    ]
}'

# Attach the policy to the user
aws iam attach-user-policy --user-name jenkins-ecr-user --policy-arn arn:aws:iam::<AWS_ACCOUNT_ID>:policy/JenkinsECRPolicy

# Create access keys
aws iam create-access-key --user-name jenkins-ecr-user
```

Save the returned `AccessKeyId` and `SecretAccessKey` securely - you'll need these for Jenkins.

## Step 2: Configure AWS Credentials in Jenkins

1. Navigate to Jenkins dashboard
2. Go to "Manage Jenkins" > "Manage Credentials"
3. Click on the appropriate domain (usually "global")
4. Click "Add Credentials"
5. Select "AWS Credentials" as the kind
6. Fill in the form:
   - ID: `aws-ecr-credentials`
   - Description: `AWS Credentials for ECR access`
   - Access Key ID: `<Your AccessKeyId>`
   - Secret Access Key: `<Your SecretAccessKey>`
7. Click "OK"

## Step 3: Update Jenkinsfile for External Jenkins

```groovy
pipeline {
    agent any
    
    environment {
        AWS_ACCOUNT_ID = credentials('AWS_ACCOUNT_ID')
        AWS_REGION = 'us-east-1' // Change as needed
        ECR_REPO_BACKEND = "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/backend"
        ECR_REPO_FRONTEND = "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/frontend"
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Configure AWS CLI') {
            steps {
                withCredentials([[
                    $class: 'AmazonWebServicesCredentialsBinding',
                    credentialsId: 'aws-ecr-credentials',
                    accessKeyVariable: 'AWS_ACCESS_KEY_ID',
                    secretKeyVariable: 'AWS_SECRET_ACCESS_KEY'
                ]]) {
                    sh 'aws configure set aws_access_key_id $AWS_ACCESS_KEY_ID'
                    sh 'aws configure set aws_secret_access_key $AWS_SECRET_ACCESS_KEY'
                    sh 'aws configure set region ${AWS_REGION}'
                }
            }
        }
        
        stage('ECR Authentication') {
            steps {
                withCredentials([[
                    $class: 'AmazonWebServicesCredentialsBinding',
                    credentialsId: 'aws-ecr-credentials',
                    accessKeyVariable: 'AWS_ACCESS_KEY_ID',
                    secretKeyVariable: 'AWS_SECRET_ACCESS_KEY'
                ]]) {
                    sh """
                        aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com
                    """
                }
            }
        }
        
        stage('Build Backend Image') {
            steps {
                dir('backend') {
                    sh 'docker build -t ${ECR_REPO_BACKEND}:${BUILD_NUMBER} .'
                }
            }
        }
        
        stage('Build Frontend Image') {
            steps {
                dir('frontend') {
                    sh 'docker build -t ${ECR_REPO_FRONTEND}:${BUILD_NUMBER} .'
                }
            }
        }
        
        stage('Push to ECR') {
            steps {
                withCredentials([[
                    $class: 'AmazonWebServicesCredentialsBinding',
                    credentialsId: 'aws-ecr-credentials',
                    accessKeyVariable: 'AWS_ACCESS_KEY_ID',
                    secretKeyVariable: 'AWS_SECRET_ACCESS_KEY'
                ]]) {
                    sh """
                        docker push ${ECR_REPO_BACKEND}:${BUILD_NUMBER}
                        docker push ${ECR_REPO_FRONTEND}:${BUILD_NUMBER}
                    """
                }
            }
        }
        
        stage('Deploy') {
            steps {
                withCredentials([[
                    $class: 'AmazonWebServicesCredentialsBinding',
                    credentialsId: 'aws-ecr-credentials',
                    accessKeyVariable: 'AWS_ACCESS_KEY_ID',
                    secretKeyVariable: 'AWS_SECRET_ACCESS_KEY'
                ]]) {
                    sh """
                        python3 deployment/deploy_backend.py --image ${ECR_REPO_BACKEND}:${BUILD_NUMBER}
                        python3 deployment/deploy_frontend.py --image ${ECR_REPO_FRONTEND}:${BUILD_NUMBER}
                    """
                }
            }
        }
    }
    
    post {
        always {
            sh 'docker system prune -af'
        }
    }
}
```

## Step 4: Update Deployment Scripts for Authentication

For the deployment scripts, modify them to accept AWS credentials:

```python
import boto3
import argparse
import time
import json
import os

def parse_args():
    parser = argparse.ArgumentParser(description='Deploy backend to AWS')
    parser.add_argument('--image', required=True, help='ECR image URI for backend')
    return parser.parse_args()

def main():
    args = parse_args()
    image_uri = args.image
    
    # AWS credentials are passed as environment variables
    # AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY are set by the Jenkins withCredentials block
    
    # AWS clients
    ec2 = boto3.client('ec2')
    autoscaling = boto3.client('autoscaling')
    elb = boto3.client('elbv2')
    
    # Rest of the script remains the same
    # ...
```

## Step 5: Network Configuration

1. **Firewall Configuration**: Ensure your Jenkins server can communicate with AWS ECR endpoints:
   - Allow outbound traffic to ECR endpoints:
     - `<AWS_ACCOUNT_ID>.dkr.ecr.<AWS_REGION>.amazonaws.com` (TCP port 443)
   - Work with your network team to ensure proper access

2. **Create a VPC Endpoint for ECR (Optional but recommended)**:
   ```bash
   aws ec2 create-vpc-endpoint \
     --vpc-id <your-vpc-id> \
     --service-name com.amazonaws.<region>.ecr.api \
     --vpc-endpoint-type Interface
   
   aws ec2 create-vpc-endpoint \
     --vpc-id <your-vpc-id> \
     --service-name com.amazonaws.<region>.ecr.dkr \
     --vpc-endpoint-type Interface
   ```

3. **Consider setting up a VPN or AWS Direct Connect** for more secure, reliable connectivity between your Jenkins environment and AWS.

## Step 6: Update User Data Scripts

The user data scripts need to use IAM roles for EC2 instances to access the ECR:

```bash
# Example of modified user data script for backend EC2 instances
#!/bin/bash
amazon-linux-extras install docker -y
systemctl start docker
systemctl enable docker

# No need to run aws ecr get-login since the EC2 instance will use its IAM role
# The IAM role permissions will automatically allow docker to pull from ECR
docker pull ${image_uri}
docker run -d -p 8080:8080 ${image_uri}
```

## Step 7: Create Required IAM Roles for EC2 Instances

```bash
# Create IAM role for EC2 instances
aws iam create-role \
  --role-name EC2InstanceProfileForECR \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Principal": {
          "Service": "ec2.amazonaws.com"
        },
        "Action": "sts:AssumeRole"
      }
    ]
  }'

# Attach policy to role
aws iam attach-role-policy \
  --role-name EC2InstanceProfileForECR \
  --policy-arn arn:aws:iam::aws:policy/AmazonECR-FullAccess

# Create instance profile
aws iam create-instance-profile \
  --instance-profile-name EC2InstanceProfileForECR

# Add role to instance profile
aws iam add-role-to-instance-profile \
  --instance-profile-name EC2InstanceProfileForECR \
  --role-name EC2InstanceProfileForECR
```

These additional steps ensure that your externally hosted Jenkins can securely authenticate with and access private ECR repositories, while the EC2 instances deployed in AWS can also access those repositories using their IAM roles.

Similar code found with 2 license types



