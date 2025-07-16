import boto3
import argparse
from time import sleep

# Initialize clients
ec2 = boto3.client('ec2')
autoscaling = boto3.client('autoscaling')
elbv2 = boto3.client('elbv2')

def create_launch_template(template_name, image_id, user_data,security_group_ids, key_name):
    response = ec2.create_launch_template(
        LaunchTemplateName=template_name,
        LaunchTemplateData={
            'ImageId': image_id,
            'InstanceType': 't2.micro',
            'UserData': user_data,
            'SecurityGroupIds': [security_group_ids],  # Replace with your security group ID
            'KeyName': key_name,  # Replace with your key pair name
        }
    )
    print(f"Launch Template {template_name} created successfully.")
    return response['LaunchTemplate']['LaunchTemplateId']

def create_target_group(name, vpc_id, port):
    response = elbv2.create_target_group(
        Name=name,
        Protocol='HTTP',
        Port=port,
        VpcId=vpc_id,
        TargetType='instance'
    )
    print(f"Target Group {name} created successfully.")
    return response['TargetGroups'][0]['TargetGroupArn']

def create_auto_scaling_group(asg_name, launch_template_id, target_group_arn, availability_zones, min_size, max_size, desired_capacity):
    response = autoscaling.create_auto_scaling_group(
        AutoScalingGroupName=asg_name,
        LaunchTemplate={
            'LaunchTemplateId': launch_template_id,
            'Version': '$Latest'
        },
        MinSize=min_size,
        MaxSize=max_size,
        DesiredCapacity=desired_capacity,
        TargetGroupARNs=[target_group_arn],
        AvailabilityZones=availability_zones
    )
    print(f"Auto Scaling Group {asg_name} created successfully.")
    return response

def create_backend_asg():
    # User data script for backend instances
    backend_user_data = """#!/bin/bash
    yum install -y docker
    systemctl start docker
    aws ecr get-login-password --region ap-south-1 | docker login --username AWS --password-stdin 975050024946.dkr.ecr.ap-south-1.amazonaws.com
    docker pull 975050024946.dkr.ecr.ap-south-1.amazonaws.com/rikhrv/hello-service:latest
    docker pull 975050024946.dkr.ecr.ap-south-1.amazonaws.com/rikhrv/profile-service:latest
    docker run -d --name hello-service -p 3001:3001 975050024946.dkr.ecr.ap-south-1.amazonaws.com/rikhrv/hello-service:latest
    docker run -d -e MONGO_URL="mongodb+srv://mngadmin:iuC20DvYorfXKTdS@cluster0.i0pov.mongodb.net/userdb" -e PORT=3002 --name profile-service -p 3002:3002  975050024946.dkr.ecr.ap-south-1.amazonaws.com/rikhrv/profile-service:latest
    """

    # Create resources
    # Replace 'sg-xyz' and 'rikhrv-ec2-2' with your actual security group ID and key pair name
    launch_template_id = create_launch_template('backend-launch-template', 'ami-08abeca95324c9c91', backend_user_data, 'sg-0243fbb5a34a23968', 'rikhrv-ec2-2')
    target_group_arn = create_target_group('backend-tg', 'vpc-xyz', 80)
    create_auto_scaling_group('mern-backend-asg', launch_template_id, target_group_arn, ['ap-south-1a', 'ap-south-1b'], 2, 4, 2)

def create_frontend_asg():
    # User data script for frontend instances
    frontend_user_data = """#!/bin/bash
    yum install -y docker
    systemctl start docker
    aws ecr get-login-password --region ap-south-1 | docker login --username AWS --password-stdin 975050024946.dkr.ecr.ap-south-1.amazonaws.com
    docker pull 975050024946.dkr.ecr.ap-south-1.amazonaws.com/rikhrv/samplmernfrontend:latest
    docker run -d -e REACT_APP_HELLO_SERVICE_URL=http://backendsmplmern.rakeshchoudhury.site:3001 -e REACT_APP_PROFILE_SERVICE_URL=http://backendsmplmern.rakeshchoudhury.site:3002 --name frontend -p 80:3000 975050024946.dkr.ecr.ap-south-1.amazonaws.com/rikhrv/samplmernfrontend:latest
    """
    sleep(100)  # Wait for backend services to be ready
    # Create resources
    # Replace 'sg-xyz' and 'rikhrv-ec2-2' with your actual security group ID and key pair name
    launch_template_id = create_launch_template('frontend-launch-template', 'ami-08abeca95324c9c91', frontend_user_data, 'sg-0243fbb5a34a23968', 'rikhrv-ec2-2')
    target_group_arn = create_target_group('frontend-tg', 'vpc-xyz', 80)
    create_auto_scaling_group('mern-frontend-asg', launch_template_id, target_group_arn, ['ap-south-1a', 'ap-south-1b'], 1, 2, 1)

def get_existing_instances():
    # Get existing instances from ASGs
    backend_instances = autoscaling.describe_auto_scaling_groups(
        AutoScalingGroupNames=['mern-backend-asg']
    )['AutoScalingGroups'][0]['Instances']
    
    frontend_instances = autoscaling.describe_auto_scaling_groups(
        AutoScalingGroupNames=['mern-frontend-asg']
    )['AutoScalingGroups'][0]['Instances']
    
    return backend_instances, frontend_instances

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--create-new', choices=['yes', 'no'], required=True)
    args = parser.parse_args()
    
    if args.create_new == 'yes':
        print("Creating new infrastructure...")
        create_backend_asg()
        create_frontend_asg()
        print("Infrastructure created successfully")
    else:
        print("Using existing infrastructure...")
        backend_instances, frontend_instances = get_existing_instances()
        print(f"Backend instances: {backend_instances}")
        print(f"Frontend instances: {frontend_instances}")