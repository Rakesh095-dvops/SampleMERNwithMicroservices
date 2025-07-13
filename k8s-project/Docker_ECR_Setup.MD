# Docker helpful commands
## 1. Build images 
```sh
docker build -t hello-service:latest .
docker build -t profile-service:latest .
docker build -t samplmernfrontend:latest .
```
## 2. Run Images locally 
```sh 
docker run -p 3001:3001 hello-service:latest
docker run --env-file .env -p 3002:3002 profile-service:latest
```
## 3. investigation on docker images 

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
# Configure AWS 
- run command  `aws configure` and configure the local workstation with aws CLI compatible.
- create ECR repositories 
- Retrieve an authentication token and authenticate your Docker client to your registry. Use the AWS CLI: 
    ```aws ecr get-login-password --region ap-south-1 | docker login --username **** --password-stdin ******.dkr.ecr.ap-south-1.amazonaws.com```
# push images to ECR 
```sh
#hello-service
docker tag hello-service:latest ******.dkr.ecr.ap-south-1.amazonaws.com/rikhrv/hello-service:latest
docker push ******.dkr.ecr.ap-south-1.amazonaws.com/rikhrv/hello-service:latest
#profile-service
docker tag profile-service:latest ******.dkr.ecr.ap-south-1.amazonaws.com/rikhrv/profile-service:latest
docker push ******.dkr.ecr.ap-south-1.amazonaws.com/rikhrv/profile-service:latest
#front-end 
docker tag samplmernfrontend:latest ******.dkr.ecr.ap-south-1.amazonaws.com/rikhrv/samplmernfrontend:latest
docker push ******.dkr.ecr.ap-south-1.amazonaws.com/rikhrv/samplmernfrontend:latest
```

