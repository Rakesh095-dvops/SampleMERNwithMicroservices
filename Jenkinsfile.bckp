pipeline {
    agent any
    
    environment {
        AWS_ACCOUNT_ID = "975050024946"  // Your AWS account ID
        AWS_REGION = 'ap-south-1' // Change as needed
        ECR_REPO_BACKEND = "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/backend"
        ECR_REPO_FRONTEND = "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/frontend"
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('ECR Authentication') {
            steps {
                withCredentials([[
                    $class: 'AmazonWebServicesCredentialsBinding',
                    credentialsId: 'your-existing-aws-credentials-id', // Use your existing credentials ID
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
                    credentialsId: 'your-existing-aws-credentials-id', // Use your existing credentials ID
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
                    credentialsId: 'your-existing-aws-credentials-id', // Use your existing credentials ID
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