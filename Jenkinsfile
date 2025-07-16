pipeline {
    agent any
    
    environment {
        AWS_REGION = 'ap-south-1'
        AWS_ACCOUNT_ID = '975050024946'
        ECR_REGISTRY = "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
        BACKEND_ASG_NAME = 'mern-backend-asg'
        FRONTEND_ASG_NAME = 'mern-frontend-asg'
        DOCKERHUB_CREDENTIALS = credentials('dockerhub-credentials')
        AWS_CREDENTIALS = credentials('aws-credentials')
        GIT_REPO = 'https://github.com/Rakesh095-dvops/SampleMERNwithMicroservices.git'
        CLOUDFLARE_DNS = 'your-backend-dns.example.com'
    }
    
    stages {
        stage('Checkout SCM') {
            steps {
                git branch: 'main', url: env.GIT_REPO
            }
        }
        
        stage('Build Docker Images') {
            parallel {
                stage('Build Hello Service') {
                    steps {
                        dir('backend/helloService') {
                            sh 'docker build -t hello-service .'
                            sh "docker tag hello-service:latest ${ECR_REGISTRY}/rikhrv/hello-service:latest"
                        }
                    }
                }
                
                stage('Build Profile Service') {
                    steps {
                        dir('backend/profileService') {
                            sh 'docker build -t profile-service .'
                            sh "docker tag profile-service:latest ${ECR_REGISTRY}/rikhrv/profile-service:latest"
                        }
                    }
                }
                
                stage('Build Frontend') {
                    steps {
                        dir('frontend') {
                            sh 'docker build -t samplmernfrontend .'
                            sh "docker tag samplmernfrontend:latest ${ECR_REGISTRY}/rikhrv/samplmernfrontend:latest"
                        }
                    }
                }
            }
        }
        
        stage('Login to ECR') {
            steps {
                sh "aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_REGISTRY}"
            }
        }
        
        stage('Push Images to ECR') {
            parallel {
                stage('Push Hello Service') {
                    steps {
                        sh "docker push ${ECR_REGISTRY}/rikhrv/hello-service:latest"
                    }
                }
                
                stage('Push Profile Service') {
                    steps {
                        sh "docker push ${ECR_REGISTRY}/rikhrv/profile-service:latest"
                    }
                }
                
                stage('Push Frontend') {
                    steps {
                        sh "docker push ${ECR_REGISTRY}/rikhrv/samplmernfrontend:latest"
                    }
                }
            }
        }
        
        stage('Deploy Infrastructure') {
            steps {
                script {
                    def createNewInstances = input(
                        id: 'createInstances', 
                        message: 'Create new EC2 instances?', 
                        parameters: [
                            choice(
                                choices: ['yes', 'no'],
                                description: 'Create fresh instances or use existing',
                                name: 'CREATE_INSTANCES'
                            )
                        ]
                    )
                    
                    dir('deployment') {
                        withAWS(credentials: env.AWS_CREDENTIALS, region: env.AWS_REGION) {
                            if (createNewInstances == 'yes') {
                                sh 'python3 deploy_ec2.py --create-new yes'
                            } else {
                                sh 'python3 deploy_ec2.py --create-new no'
                            }
                        }
                    }
                }
            }
        }
        
        stage('Deploy Backend Services') {
            steps {
                sshagent(['ec2-ssh-key']) {
                    sh """
                        ssh -o StrictHostKeyChecking=no ec2-user@${env.BACKEND_INSTANCE_IP} << EOF
                        aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_REGISTRY}
                        docker pull ${ECR_REGISTRY}/rikhrv/hello-service:latest
                        docker pull ${ECR_REGISTRY}/rikhrv/profile-service:latest
                        docker stop hello-service profile-service || true
                        docker rm hello-service profile-service || true
                        docker run -d --name hello-service -p 3001:3001 -e BACKEND_DNS=${env.CLOUDFLARE_DNS} ${ECR_REGISTRY}/rikhrv/hello-service:latest
                        docker run -d --name profile-service -p 3002:3002 -e BACKEND_DNS=${env.CLOUDFLARE_DNS} ${ECR_REGISTRY}/rikhrv/profile-service:latest
                        EOF
                    """
                }
            }
        }
        
        stage('Deploy Frontend') {
            steps {
                sshagent(['ec2-ssh-key']) {
                    sh """
                        ssh -o StrictHostKeyChecking=no ec2-user@${env.FRONTEND_INSTANCE_IP} << EOF
                        aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_REGISTRY}
                        docker pull ${ECR_REGISTRY}/rikhrv/samplmernfrontend:latest
                        docker stop frontend || true
                        docker rm frontend || true
                        docker run -d --name frontend -p 3000:3000 -e REACT_APP_BACKEND_URL=http://${env.CLOUDFLARE_DNS} ${ECR_REGISTRY}/rikhrv/samplmernfrontend:latest
                        EOF
                    """
                }
            }
        }
        
        stage('Update Cloudflare DNS') {
            steps {
                script {
                    // This would use Cloudflare API to update DNS records
                    // Implementation depends on your Cloudflare setup
                    echo "Updating Cloudflare DNS to point to backend instances"
                }
            }
        }
    }
    
    post {
        success {
            slackSend(color: "good", message: "SUCCESS: Pipeline ${env.JOB_NAME} #${env.BUILD_NUMBER}")
        }
        failure {
            slackSend(color: "danger", message: "FAILED: Pipeline ${env.JOB_NAME} #${env.BUILD_NUMBER}")
        }
    }
}