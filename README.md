# Sample MERN with Microservices (JENKINS[DOCKER+AWS(BOTO3)] + EKS(HELM/k8s))

## **JENKINS+DOCKER+AWS(BOTO3)**

## 1.  Set Up Jenkins on EC2

### Jenkins Installation on EC2

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
2. Get initial admin password: .create user for jenkins
   ```bash
   sudo cat /var/lib/jenkins/secrets/initialAdminPassword
   ```
3. Install suggested plugins plus:
   - Docker Pipeline
   - Amazon ECR plugin
   - AWS SDK

## 2.  Create Jenkins Pipeline

### Create Jenkins Job

1. In Jenkins, create a new Pipeline job
2. Configure SCM to point to your repository
3. Set the pipeline script path to `Jenkinsfile`
4. Configure webhook in your Git repository to trigger Jenkins job on push to main branch
5. Jenkins will provision resources and destroy on build fails.

```sh
python deploy_ec2.py --cleanup --create-new no # to cleanup resources
python deploy_ec2.py --create-new yes # to create new resources
python deploy_ec2.py --create-new no # get ec2 instances details
```

> Verify the same from running front end LB and backend LB. 

### Note : troubleshoot 
Docker build images and push for workstation

####  Build images 
```sh
docker build -t hello-service:latest .
docker build -t profile-service:latest .
docker build -t samplmernfrontend:latest .
```
####  Run Images locally 
```sh 
docker run -p 3001:3001 hello-service:latest
docker run --env-file .env -p 3002:3002 profile-service:latest
docker run --env-file .env -p 3000:3000 samplmernfrontend:latest
```
####  investigation on docker images 

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
#### Configure AWS 
- run command  `aws configure` and configure the local workstation with aws CLI compatible.
- create ECR repositories 
- Retrieve an authentication token and authenticate your Docker client to your registry. Use the AWS CLI: 
    ```aws ecr get-login-password --region ap-south-1 | docker login --username **** --password-stdin 975050024946.dkr.ecr.ap-south-1.amazonaws.com```
#### push images to ECR 
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
----
# EKS implementation 

Refer  ```eks``` branch for helm-chart deployment. 




