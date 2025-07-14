import boto3
import argparse
import time
import json

def parse_args():
    parser = argparse.ArgumentParser(description='Deploy frontend to AWS')
    parser.add_argument('--image', required=True, help='ECR image URI for frontend')
    return parser.parse_args()

def main():
    args = parse_args()
    image_uri = args.image
    
    # AWS clients
    ec2 = boto3.client('ec2')
    elb = boto3.client('elbv2')
    
    # Create security group for frontend
    security_group = ec2.create_security_group(
        GroupName=f'frontend-sg-{int(time.time())}',
        Description='Security group for frontend service'
    )
    sg_id = security_group['GroupId']
    
    # Allow inbound traffic on port 80
    ec2.authorize_security_group_ingress(
        GroupId=sg_id,
        IpPermissions=[
            {
                'IpProtocol': 'tcp',
                'FromPort': 80,
                'ToPort': 80,
                'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
            }
        ]
    )
    
    # Create user data script
    user_data = f'''#!/bin/bash
    amazon-linux-extras install docker -y
    systemctl start docker
    systemctl enable docker
    aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin {image_uri.split("/")[0]}
    docker pull {image_uri}
    docker run -d -p 80:80 -e "REACT_APP_API_URL=http://backend-lb-url" {image_uri}
    '''
    
    # Launch EC2 instance for frontend
    instance = ec2.run_instances(
        ImageId='ami-0c55b159cbfafe1f0',  # Amazon Linux 2 AMI (adjust as needed)
        InstanceType='t2.micro',
        MinCount=1,
        MaxCount=1,
        SecurityGroupIds=[sg_id],
        UserData=user_data,
        IamInstanceProfile={
            'Name': 'EC2InstanceProfileForECR'  # Same role as backend
        },
        TagSpecifications=[
            {
                'ResourceType': 'instance',
                'Tags': [
                    {
                        'Key': 'Name',
                        'Value': 'Frontend-Server'
                    }
                ]
            }
        ]
    )
    
    instance_id = instance['Instances'][0]['InstanceId']
    
    # Wait for instance to be running
    waiter = ec2.get_waiter('instance_running')
    waiter.wait(InstanceIds=[instance_id])
    
    # Get instance details
    instance_info = ec2.describe_instances(InstanceIds=[instance_id])
    public_dns = instance_info['Reservations'][0]['Instances'][0]['PublicDnsName']
    
    print(f"Frontend deployed successfully. Access at: http://{public_dns}")

if __name__ == '__main__':
    main()