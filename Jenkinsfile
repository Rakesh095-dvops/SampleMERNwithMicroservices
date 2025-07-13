pipeline {
    agent any
    
    environment {
        AWS_REGION = 'ap-south-1'
        CLUSTER_NAME = 'rikhrv-terraform-state-bucket'
        KUBECONFIG = "${env.WORKSPACE}/kubeconfig"
        EKS_ROLE_ARN = 'arn:aws:iam::975050024946:role/jenkins_rikhrv' // Replace with your role ARN
        CLOUDFLARE_API_TOKEN = credentials('cloudflare-api-token')
        CLOUDFLARE_ZONE_ID = credentials('cloudflare-zone-id')
        CLOUDFLARE_DOMAIN = 'www.rakeshchoudhury.site' // Replace with your domain
        ECR_REGISTRY = '975050024946.dkr.ecr.ap-south-1.amazonaws.com/rikhrv'
        GIT_COMMIT_SHORT = sh(script: "echo ${GIT_COMMIT} | cut -c1-8", returnStdout: true).trim()
    }
    
    stages {
        stage('Setup') {
            steps {
                sh '''
                    # Install kubectl, helm, aws-cli if not installed
                    which kubectl || curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" && chmod +x kubectl && sudo mv kubectl /usr/local/bin/
                    which helm || curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 && chmod +x get_helm.sh && ./get_helm.sh
                    
                    # Get kubeconfig for EKS
                    aws eks update-kubeconfig --region ${AWS_REGION} --name ${CLUSTER_NAME} --kubeconfig ${KUBECONFIG} --role-arn ${EKS_ROLE_ARN}
                    
                    # Create namespace if not exists
                    kubectl --kubeconfig=${KUBECONFIG} create namespace sample-mern --dry-run=client -o yaml | kubectl --kubeconfig=${KUBECONFIG} apply -f -
                '''
            }
        }
        
        stage('Build and Push Docker Images') {
            steps {
                withCredentials([[$class: 'AmazonWebServicesCredentialsBinding', 
                                credentialsId: 'aws-ecr-credentials',
                                accessKeyVariable: 'AWS_ACCESS_KEY_ID', 
                                secretKeyVariable: 'AWS_SECRET_ACCESS_KEY']]) {
                    sh '''
                        # Login to ECR
                        aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_REGISTRY}
                        
                        # Build and push Hello Service
                        cd backend/hello-service
                        docker build -t ${ECR_REGISTRY}/hello-service:${GIT_COMMIT_SHORT} .
                        docker push ${ECR_REGISTRY}/hello-service:${GIT_COMMIT_SHORT}
                        
                        # Build and push Profile Service
                        cd ../profile-service
                        docker build -t ${ECR_REGISTRY}/profile-service:${GIT_COMMIT_SHORT} .
                        docker push ${ECR_REGISTRY}/profile-service:${GIT_COMMIT_SHORT}
                        
                        # Build and push Frontend
                        cd ../../frontend
                        docker build -t ${ECR_REGISTRY}/samplmernfrontend:${GIT_COMMIT_SHORT} .
                        docker push ${ECR_REGISTRY}/samplmernfrontend:${GIT_COMMIT_SHORT}
                    '''
                }
            }
        }
        
        stage('Deploy with Helm') {
            steps {
                sh '''
                    # Create ECR Registry Secret
                    kubectl --kubeconfig=${KUBECONFIG} create secret docker-registry ecr-registry-secret \
                      --namespace sample-mern \
                      --docker-server=${ECR_REGISTRY} \
                      --docker-username=AWS \
                      --docker-password=$(aws ecr get-login-password --region ${AWS_REGION}) \
                      --dry-run=client -o yaml | kubectl --kubeconfig=${KUBECONFIG} apply -f -
                      
                    # Update Helm values for ECR images with current commit
                    cat > values-override.yaml << EOF
global:
  environment: eks
  registry:
    eks:
      url: ${ECR_REGISTRY}
frontend:
  image:
    tag: ${GIT_COMMIT_SHORT}
backend:
  helloService:
    image:
      tag: ${GIT_COMMIT_SHORT}
  profileService:
    image:
      tag: ${GIT_COMMIT_SHORT}
EOF
                    
                    # Deploy with Helm
                    helm --kubeconfig=${KUBECONFIG} upgrade --install mern-app ./mern-app \
                      --namespace sample-mern \
                      -f values-override.yaml
                '''
            }
        }
        
        stage('Validate Deployment') {
            steps {
                sh '''
                    # Wait for pods to be ready
                    kubectl --kubeconfig=${KUBECONFIG} -n sample-mern wait --for=condition=ready pod --selector=app=frontend --timeout=300s
                    kubectl --kubeconfig=${KUBECONFIG} -n sample-mern wait --for=condition=ready pod --selector=app=hello-service --timeout=300s
                    kubectl --kubeconfig=${KUBECONFIG} -n sample-mern wait --for=condition=ready pod --selector=app=profile-service --timeout=300s
                    
                    # Get service information
                    FRONTEND_LB=$(kubectl --kubeconfig=${KUBECONFIG} -n sample-mern get svc frontend -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
                    HELLO_LB=$(kubectl --kubeconfig=${KUBECONFIG} -n sample-mern get svc hello-service -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
                    PROFILE_LB=$(kubectl --kubeconfig=${KUBECONFIG} -n sample-mern get svc profile-service -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
                    
                    echo "Frontend LoadBalancer: $FRONTEND_LB"
                    echo "Hello Service LoadBalancer: $HELLO_LB"
                    echo "Profile Service LoadBalancer: $PROFILE_LB"
                    
                    # Store LB endpoints for CloudFlare configuration
                    echo "$FRONTEND_LB" > frontend-lb.txt
                    echo "$HELLO_LB" > hello-lb.txt
                    echo "$PROFILE_LB" > profile-lb.txt
                '''
            }
        }
        
        stage('Configure CloudFlare DNS') {
            steps {
                sh '''
                    # Get LoadBalancer endpoints
                    FRONTEND_LB=$(cat frontend-lb.txt)
                    HELLO_LB=$(cat hello-lb.txt)
                    PROFILE_LB=$(cat profile-lb.txt)
                    
                    # Configure CloudFlare DNS using API
                    # Frontend
                    curl -X POST "https://api.cloudflare.com/client/v4/zones/${CLOUDFLARE_ZONE_ID}/dns_records" \
                      -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}" \
                      -H "Content-Type: application/json" \
                      --data '{
                        "type": "CNAME",
                        "name": "app",
                        "content": "'"${FRONTEND_LB}"'",
                        "ttl": 1,
                        "proxied": true
                      }'
                    
                    # Hello Service
                    curl -X POST "https://api.cloudflare.com/client/v4/zones/${CLOUDFLARE_ZONE_ID}/dns_records" \
                      -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}" \
                      -H "Content-Type: application/json" \
                      --data '{
                        "type": "CNAME",
                        "name": "api-hello",
                        "content": "'"${HELLO_LB}"'",
                        "ttl": 1,
                        "proxied": true
                      }'
                    
                    # Profile Service
                    curl -X POST "https://api.cloudflare.com/client/v4/zones/${CLOUDFLARE_ZONE_ID}/dns_records" \
                      -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}" \
                      -H "Content-Type: application/json" \
                      --data '{
                        "type": "CNAME",
                        "name": "api-profile",
                        "content": "'"${PROFILE_LB}"'",
                        "ttl": 1,
                        "proxied": true
                      }'
                '''
            }
        }
        
        stage('Final Validation') {
            steps {
                sh '''
                    echo "MERN Application Deployed Successfully!"
                    echo "Frontend URL: https://app.${CLOUDFLARE_DOMAIN}"
                    echo "Hello Service API: https://api-hello.${CLOUDFLARE_DOMAIN}"
                    echo "Profile Service API: https://api-profile.${CLOUDFLARE_DOMAIN}"
                    
                    # Test endpoints
                    echo "Testing endpoints in 1 minute to allow DNS propagation..."
                    sleep 60
                    
                    # Using curl to test endpoints silently
                    curl -s -o /dev/null -w "Frontend Status: %{http_code}\\n" https://app.${CLOUDFLARE_DOMAIN}
                    curl -s -o /dev/null -w "Hello API Status: %{http_code}\\n" https://api-hello.${CLOUDFLARE_DOMAIN}/health
                    curl -s -o /dev/null -w "Profile API Status: %{http_code}\\n" https://api-profile.${CLOUDFLARE_DOMAIN}/health
                '''
            }
        }
    }
    
    post {
        always {
            cleanWs()
        }
        success {
            echo 'Deployment completed successfully!'
        }
        failure {
            echo 'Deployment failed!'
        }
    }
}