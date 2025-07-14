import boto3
import argparse
import time
import json
import os

def parse_args():
    parser = argparse.ArgumentParser(description='Deploy backend to AWS')
    parser.add_argument('--image', required=True, help='ECR image URI for backend')
    return parser.parse_args()

def main():
    args = parse_args()
    image_uri = args.image
    
    # AWS credentials are passed as environment variables
    # AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY are set by the Jenkins withCredentials block
    
    # AWS clients
    ec2 = boto3.client('ec2')
    autoscaling = boto3.client('autoscaling')
    elb = boto3.client('elbv2')
    
    # Create security group for backend
    security_group = ec2.create_security_group(
        GroupName=f'backend-sg-{int(time.time())}',
        Description='Security group for backend service'
    )
    sg_id = security_group['GroupId']
    
    # Allow inbound traffic on port 8080
    ec2.authorize_security_group_ingress(
        GroupId=sg_id,
        IpPermissions=[
            {
                'IpProtocol': 'tcp',
                'FromPort': 8080,
                'ToPort': 8080,
                'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
            }
        ]
    )
    
    # Create launch template
    user_data = f'''#!/bin/bash
    amazon-linux-extras install docker -y
    systemctl start docker
    systemctl enable docker
    aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin {image_uri.split("/")[0]}
    docker pull {image_uri}
    docker run -d -p 8080:8080 {image_uri}
    '''
    
    # Encode user data
    import base64
    user_data_encoded = base64.b64encode(user_data.encode()).decode()
    
    # Create launch template
    launch_template = ec2.create_launch_template(
        LaunchTemplateName=f'backend-template-{int(time.time())}',
        VersionDescription='Initial version',
        LaunchTemplateData={
            'ImageId': 'ami-0c55b159cbfafe1f0',  # Amazon Linux 2 AMI (adjust as needed)
            'InstanceType': 't2.micro',
            'SecurityGroupIds': [sg_id],
            'UserData': user_data_encoded,
            'IamInstanceProfile': {
                'Name': 'EC2InstanceProfileForECR'  # You need to create this role with ECR access
            }
        }
    )
    
    template_id = launch_template['LaunchTemplate']['LaunchTemplateId']
    
    # Create target group for load balancer
    vpc_id = ec2.describe_vpcs()['Vpcs'][0]['VpcId']  # Get default VPC
    target_group = elb.create_target_group(
        Name=f'backend-tg-{int(time.time())}',
        Protocol='HTTP',
        Port=8080,
        VpcId=vpc_id,
        HealthCheckPath='/api/health',  # Adjust based on your app
        HealthCheckProtocol='HTTP',
        TargetType='instance'
    )
    
    tg_arn = target_group['TargetGroups'][0]['TargetGroupArn']
    
    # Create load balancer
    load_balancer = elb.create_load_balancer(
        Name=f'backend-lb-{int(time.time())}',
        Subnets=[
            subnet['SubnetId'] for subnet in 
            ec2.describe_subnets()['Subnets'][:2]  # Use first two subnets
        ],
        SecurityGroups=[sg_id]
    )
    
    lb_arn = load_balancer['LoadBalancers'][0]['LoadBalancerArn']
    
    # Create listener
    listener = elb.create_listener(
        LoadBalancerArn=lb_arn,
        Protocol='HTTP',
        Port=80,
        DefaultActions=[{
            'Type': 'forward',
            'TargetGroupArn': tg_arn
        }]
    )
    
    # Create auto scaling group
    asg = autoscaling.create_auto_scaling_group(
        AutoScalingGroupName=f'backend-asg-{int(time.time())}',
        LaunchTemplate={
            'LaunchTemplateId': template_id,
            'Version': '$Latest'
        },
        MinSize=2,
        MaxSize=5,
        DesiredCapacity=2,
        TargetGroupARNs=[tg_arn],
        VPCZoneIdentifier=','.join([
            subnet['SubnetId'] for subnet in 
            ec2.describe_subnets()['Subnets'][:2]  # Use first two subnets
        ])
    )
    
    # Create scaling policies
    autoscaling.put_scaling_policy(
        AutoScalingGroupName=asg['AutoScalingGroupName'],
        PolicyName='CPU-ScaleUp',
        PolicyType='TargetTrackingScaling',
        TargetTrackingConfiguration={
            'PredefinedMetricSpecification': {
                'PredefinedMetricType': 'ASGAverageCPUUtilization'
            },
            'TargetValue': 70.0
        }
    )
    
    print(f"Backend deployed successfully. Load balancer DNS: {load_balancer['LoadBalancers'][0]['DNSName']}")

if __name__ == '__main__':
    main()