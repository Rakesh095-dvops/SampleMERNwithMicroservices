# Docker helpful commands
## 1. Build images 
```sh
docker build -t hello-service:latest .
docker build -t profile-service:latest .
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

