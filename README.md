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
kubectl create ns smple-mern
kubectl apply -f k8s-project/misc/mngdbsecret.yaml
kubectl apply -f k8s-project/misc/configbackend.yaml
kubectl apply -f k8s-project/deployments/backend-deployments.yaml
kubectl apply -f k8s-project/services/backend-services.yaml
```

```sh
kubectl delete all --all -n smple-mern
```