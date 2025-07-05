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

# Apply all resources:
```sh
echo -n "mongodb+srv://user:pass@cluster.mongodb.net/db" | base64
```
```sh
kubectl create ns sample-mern
kubectl apply -f k8s-project/misc/mngdbsecret.yaml
kubectl apply -f k8s-project/misc/configbackend.yaml
kubectl apply -f k8s-project/deployments/backend-deployment.yaml
kubectl apply -f k8s-project/services/backend-services.yaml
kubectl apply -f k8s-project/deployments/frontend-deployment.yaml
kubectl apply -f k8s-project/services/frontend-services.yaml 
```
```sh
kubectl logs deployment/frontend -n sample-mern

```

```sh
kubectl get all -n sample-mern -o wide
minikube service frontend -n sample-mern
kubectl port-forward svc/profile-service 3002:3002 -n sample-mern
kubectl port-forward svc/profile-service 3002:3002 -n sample-mern
kubectl delete all --all -n sample-mern
```
```sh 

kubectl exec -it {front_end_pod} -n sample-mern -- /bin/sh
kubectl exec -it $(kubectl get pods | grep frontend | awk '{print $1}') -- /bin/bash
curl http://hello-service:3001/health
curl http://hello-service:3001/
curl http://profile-service:3002/fetchuser

```

# helm chart 
```sh 
#creation 
helm create simple-mern-helm
#install 
helm install mern-app ./mern-app -n sample-mern --create-namespace
#verify Manifest files
helm get manifest mern-app -n sample-mern 
#upgrade HelmChart
helm upgrade mern-app ./mern-app -n sample-mern
#to custom values 
helm install mern-app ./mern-app -f my-values.yaml -n sample-mern
#uninstall helm 
helm uninstall mern-app -n sample-mern
```