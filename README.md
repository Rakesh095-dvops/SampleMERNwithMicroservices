## Step 1: Set Up Jenkins on EC2

### Jenkins Installation

Install Jenkins by following below steps as provided in jenkins official guide (https://www.jenkins.io/doc/tutorials/tutorial-for-installing-jenkins-on-AWS/)

```bash
# Install Docker
sudo yum install docker -y
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker jenkins
sudo usermod -aG docker ec2-user
sudo systemctl restart jenkins
```

### Jenkins Configuration

1. Access Jenkins at `http://<EC2-Public-IP>:8080`
2. Get initial admin password:
   ```bash
   sudo cat /var/lib/jenkins/secrets/initialAdminPassword
   ```
3. Install suggested plugins plus:
   - Docker Pipeline
   - Amazon ECR plugin
   - Blue Ocean
   - AWS SDK
   - Pipeline: AWS Steps

## Step 6: Docker build images and push 

### 1. Build images 
```sh
docker build -t hello-service:latest .
docker build -t profile-service:latest .
docker build -t samplmernfrontend:latest .
```
### 2. Run Images locally 
```sh 
docker run -p 3001:3001 hello-service:latest
docker run --env-file .env -p 3002:3002 profile-service:latest
docker run --env-file .env -p 3000:3000 samplmernfrontend:latest
```
### 3. investigation on docker images 

**List all images:**
```sh
docker images
```
**List all running containers:**
```sh
docker ps
```
**Get detailed info about a specific image:**
```sh
docker inspect <image_name_or_id>
```
**Get detailed info about a specific running container:**
```sh
docker inspect <container_id>
```
### Configure AWS 
- run command  `aws configure` and configure the local workstation with aws CLI compatible.
- create ECR repositories 
- Retrieve an authentication token and authenticate your Docker client to your registry. Use the AWS CLI: 
    ```aws ecr get-login-password --region ap-south-1 | docker login --username **** --password-stdin 975050024946.dkr.ecr.ap-south-1.amazonaws.com```
### push images to ECR 
```sh
#hello-service
docker tag hello-service:latest 975050024946dkr.ecr.ap-south-1.amazonaws.com/rikhrv/hello-service:latest
docker push 975050024946dkr.ecr.ap-south-1.amazonaws.com/rikhrv/hello-service:latest
#profile-service
docker tag profile-service:latest 975050024946.dkr.ecr.ap-south-1.amazonaws.com/rikhrv/profile-service:latest
docker push 975050024946.dkr.ecr.ap-south-1.amazonaws.com/rikhrv/profile-service:latest
#front-end 
docker tag samplmernfrontend:latest 975050024946.dkr.ecr.ap-south-1.amazonaws.com/rikhrv/samplmernfrontend:latest
docker push 975050024946.dkr.ecr.ap-south-1.amazonaws.com/rikhrv/samplmernfrontend:latest
```

## Step 3: Create Jenkins Pipeline

### Create Jenkins Job

1. In Jenkins, create a new Pipeline job
2. Configure SCM to point to your repository
3. Set the pipeline script path to `Jenkinsfile`
4. Configure webhook in your Git repository to trigger Jenkins job on push to main branch

## Step 4: Create Boto3 Deployment Scripts

### Backend Deployment Script

### Frontend Deployment Script

## Step 5: IAM Role Setup

Create an EC2 Instance Profile with permissions to access ECR:

1. In AWS Console, go to IAM
2. Create a new role for EC2
3. Attach the following policies:
   - AmazonECR-FullAccess
   - AmazonEC2FullAccess (or a more restrictive custom policy)
4. Name the role "EC2InstanceProfileForECR"

## Step 6: Create ECR Repositories

```bash
aws ecr create-repository --repository-name frontend
aws ecr create-repository --repository-name backend
```

