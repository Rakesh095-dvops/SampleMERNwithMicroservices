import boto3
import argparse
import base64
from time import sleep
import json

# Initialize clients
ec2 = boto3.client('ec2')
autoscaling = boto3.client('autoscaling')
elbv2 = boto3.client('elbv2')
iam = boto3.client('iam')

def encode_user_data(user_data_script):
    """Encode user data script to base64"""
    return base64.b64encode(user_data_script.encode('utf-8')).decode('utf-8')

def get_vpc_subnets(vpc_id):
    """Get all available subnets for a VPC"""
    try:
        response = ec2.describe_subnets(
            Filters=[
                {
                    'Name': 'vpc-id',
                    'Values': [vpc_id]
                },
                {
                    'Name': 'state',
                    'Values': ['available']
                }
            ]
        )
        
        subnet_ids = [subnet['SubnetId'] for subnet in response['Subnets']]
        print(f"✓ Found {len(subnet_ids)} available subnets in VPC {vpc_id}")
        return subnet_ids
        
    except Exception as e:
        print(f"✗ Error getting subnets for VPC {vpc_id}: {str(e)}")
        return []

def create_launch_template(template_name, image_id, instance_type, security_group_ids, key_name, user_data, iam_instance_profile=None):
    """Create launch template for ASG"""
    try:
        # Encode user data
        encoded_user_data = encode_user_data(user_data)
        
        launch_template_data = {
            'ImageId': image_id,
            'InstanceType': instance_type,
            'UserData': encoded_user_data,
            'SecurityGroupIds': security_group_ids,
            'KeyName': key_name,
            'TagSpecifications': [
                {
                    'ResourceType': 'instance',
                    'Tags': [
                        {'Key': 'Name', 'Value': f'{template_name}-instance'},
                        {'Key': 'Environment', 'Value': 'production'}
                    ]
                }
            ]
        }
        
        # Add IAM instance profile if provided
        if iam_instance_profile:
            launch_template_data['IamInstanceProfile'] = {'Name': iam_instance_profile}
        
        response = ec2.create_launch_template(
            LaunchTemplateName=template_name,
            LaunchTemplateData=launch_template_data
        )
        
        print(f"Launch Template '{template_name}' created successfully")
        return response['LaunchTemplate']['LaunchTemplateId']
        
    except Exception as e:
        print(f" Error creating launch template '{template_name}': {str(e)}")
        return None

def create_target_group(name, vpc_id, port, protocol='HTTP', health_check_path='/health'):
    """Create target group for load balancer"""
    try:
        response = elbv2.create_target_group(
            Name=name,
            Protocol=protocol,
            Port=port,
            VpcId=vpc_id,
            TargetType='instance',
            HealthCheckPath=health_check_path,
            HealthCheckIntervalSeconds=30,
            HealthCheckTimeoutSeconds=5,
            HealthyThresholdCount=2,
            UnhealthyThresholdCount=3,
            Tags=[
                {'Key': 'Name', 'Value': name},
                {'Key': 'Environment', 'Value': 'production'}
            ]
        )
        
        target_group_arn = response['TargetGroups'][0]['TargetGroupArn']
        print(f" Target Group '{name}' created successfully")
        return target_group_arn
        
    except Exception as e:
        print(f" Error creating target group '{name}': {str(e)}")
        return None

def create_auto_scaling_group(asg_name, launch_template_id, min_size, max_size, desired_capacity, 
                            subnet_ids, target_group_arns=None, health_check_type='ELB'):
    """Create Auto Scaling Group"""
    try:
        asg_config = {
            'AutoScalingGroupName': asg_name,
            'LaunchTemplate': {
                'LaunchTemplateId': launch_template_id,
                'Version': '$Latest'
            },
            'MinSize': min_size,
            'MaxSize': max_size,
            'DesiredCapacity': desired_capacity,
            'VPCZoneIdentifier': ','.join(subnet_ids),
            'HealthCheckType': health_check_type,
            'HealthCheckGracePeriod': 300,
            'Tags': [
                {
                    'Key': 'Name',
                    'Value': asg_name,
                    'PropagateAtLaunch': True,
                    'ResourceId': asg_name,
                    'ResourceType': 'auto-scaling-group'
                }
            ]
        }
        
        # Add target group ARNs if provided
        if target_group_arns:
            asg_config['TargetGroupARNs'] = target_group_arns
        
        response = autoscaling.create_auto_scaling_group(**asg_config)
        print(f"Auto Scaling Group '{asg_name}' created successfully")
        return True
        
    except Exception as e:
        print(f" Error creating ASG '{asg_name}': {str(e)}")
        return False

def create_backend_asg():
    """Create backend Auto Scaling Group with microservices"""
    print("\n Creating Backend ASG...")
    
    # Backend configuration
    backend_user_data = """#!/bin/bash
apt-get update -y
apt-get install -y docker.io awscli

# Start Docker service
systemctl start docker
systemctl enable docker
usermod -a -G docker ubuntu

# Login to ECR
aws ecr get-login-password --region ap-south-1 | docker login --username AWS --password-stdin 975050024946.dkr.ecr.ap-south-1.amazonaws.com

# Pull and run backend services
docker pull 975050024946.dkr.ecr.ap-south-1.amazonaws.com/rikhrv/hello-service:latest
docker pull 975050024946.dkr.ecr.ap-south-1.amazonaws.com/rikhrv/profile-service:latest

# Run services with restart policy
docker run -d -e PORT=3001 --name hello-service --restart=unless-stopped -p 3001:3001 \
    975050024946.dkr.ecr.ap-south-1.amazonaws.com/rikhrv/hello-service:latest

docker run -d -e PORT=3002 -e MONGO_URL=mongodb+srv://mngadmin:iuC20DvYorfXKTdS@cluster0.i0pov.mongodb.net/userdb \
        --name profile-service --restart=unless-stopped -p 3002:3002 \
    975050024946.dkr.ecr.ap-south-1.amazonaws.com/rikhrv/profile-service:latest

"""

    # Replace with your actual values
    config = {
        'template_name': 'rikhrv-backend-launch-template',
        'image_id': 'ami-0f58b397bc5c1f2e8',  # Ubuntu 22.04 LTS AMI (ap-south-1)
        'instance_type': 't2.micro',
        'security_group_ids': ['sg-0243fbb5a34a23968'],  # Replace with your security group
        'key_name': 'rikhrv-ec2-2',  # Replace with your key pair
        'vpc_id': 'vpc-0056d809452f9f8ea',  # Replace with your VPC ID
        'iam_instance_profile': 'rikhrv-EC2-ECR-Role'  # IAM role with ECR permissions
    }

     # Auto-discover subnets from VPC
    subnet_ids = get_vpc_subnets(config['vpc_id'])
    if not subnet_ids:
        print(" No available subnets found in VPC")
        return False
    
    print(f" Using subnets: {subnet_ids}")
    
    
    # Create launch template
    launch_template_id = create_launch_template(
        config['template_name'],
        config['image_id'],
        config['instance_type'],
        config['security_group_ids'],
        config['key_name'],
        backend_user_data,
        config['iam_instance_profile']
    )
    
    if not launch_template_id:
        return False
    
    # Create target group
    target_group_arn = create_target_group(
        'backend-tg',
        config['vpc_id'],
        80,
        health_check_path='/health'
    )
    
    if not target_group_arn:
        return False
    
    # Create ASG
    success = create_auto_scaling_group(
        'rikhrv-mern-backend-asg',
        launch_template_id,
        min_size=1,
        max_size=4,
        desired_capacity=2,
        subnet_ids=subnet_ids,  # Use auto-discovered subnets
        target_group_arns=[target_group_arn]
    )
    
    return success

def create_frontend_asg():
    """Create frontend Auto Scaling Group"""
    print("\n Creating Frontend ASG...")
    
    # Frontend configuration - Fixed the user data to pull frontend image
    frontend_user_data = """#!/bin/bash
apt-get update -y
apt-get install -y docker.io awscli nginx

# Start Docker service
systemctl start docker
systemctl enable docker
usermod -a -G docker ubuntu


# Login to ECR
aws ecr get-login-password --region ap-south-1 | docker login --username AWS --password-stdin 975050024946.dkr.ecr.ap-south-1.amazonaws.com

# Pull and run frontend service
docker pull 975050024946.dkr.ecr.ap-south-1.amazonaws.com/rikhrv/samplmernfrontend:latest

# Run frontend with restart policy
docker run -d -e REACT_APP_HELLO_SERVICE_URL=http://backendsmplmern.rakeshchoudhury.site:3001 \
    -e REACT_APP_PROFILE_SERVICE_URL=http://backendsmplmern.rakeshchoudhury.site:3002 \
        --name frontend -p 80:3000 975050024946.dkr.ecr.ap-south-1.amazonaws.com/rikhrv/samplmernfrontend:latest

"""

    # Configuration with VPC ID - subnets will be auto-discovered
    config = {
        'template_name': 'rikhrv-frontend-launch-template',
        'image_id': 'ami-0f58b397bc5c1f2e8',  # Ubuntu 22.04 LTS AMI (ap-south-1)
        'instance_type': 't2.micro',
        'security_group_ids': ['sg-0243fbb5a34a23968'],  # Use your actual security group
        'key_name': 'rikhrv-ec2-2',  # Your key pair
        'vpc_id': 'vpc-0056d809452f9f8ea',  # Your VPC ID
        'iam_instance_profile': 'rikhrv-EC2-ECR-Role'  # IAM role with ECR permissions
    }
    
    # Auto-discover subnets from VPC
    subnet_ids = get_vpc_subnets(config['vpc_id'])
    if not subnet_ids:
        print(" No available subnets found in VPC")
        return False

    print(f" Using subnets: {subnet_ids}")

    # Create launch template
    launch_template_id = create_launch_template(
        config['template_name'],
        config['image_id'],
        config['instance_type'],
        config['security_group_ids'],
        config['key_name'],
        frontend_user_data,
        config['iam_instance_profile']
    )
    
    if not launch_template_id:
        return False
    
    # Create target group
    target_group_arn = create_target_group(
        'frontend-tg',
        config['vpc_id'],
        80,
        health_check_path='/health'
    )
    
    if not target_group_arn:
        return False
    
    # Create ASG with auto-discovered subnets
    success = create_auto_scaling_group(
        'rikhrv-mern-frontend-asg',
        launch_template_id,
        min_size=1,
        max_size=3,
        desired_capacity=1,
        subnet_ids=subnet_ids,  # Use auto-discovered subnets
        target_group_arns=[target_group_arn]
    )
    
    return success

def get_iam_instance_profile_if_exists(profile_name):
    """Get IAM instance profile if it exists, return None if not found"""
    try:
        response = iam.get_instance_profile(InstanceProfileName=profile_name)
        print(f" IAM Instance Profile '{profile_name}' found")
        return response['InstanceProfile']
    except iam.exceptions.NoSuchEntityException:
        print(f"ℹ IAM Instance Profile '{profile_name}' does not exist")
        return None
    except Exception as e:
        print(f" Error getting IAM Instance Profile: {str(e)}")
        return None

def create_iam_instance_profile():
    """Create IAM Instance Profile for EC2 instances"""
    instance_profile_name = 'rikhrv-EC2-ECR-Role'
    role_name = 'rikhrv-EC2-ECR-Role'
    
    # Check if instance profile already exists
    existing_profile = get_iam_instance_profile_if_exists(instance_profile_name)
    if existing_profile:
        return True
    
    try:
        # Create IAM role
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "ec2.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        
        iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description='Role for EC2 instances to access ECR'
        )
        
        # Attach ECR read-only policy
        iam.attach_role_policy(
            RoleName=role_name,
            PolicyArn='arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly'
        )
        
        # Create instance profile
        iam.create_instance_profile(
            InstanceProfileName=instance_profile_name
        )
        
        # Add role to instance profile
        iam.add_role_to_instance_profile(
            InstanceProfileName=instance_profile_name,
            RoleName=role_name
        )
        
        print(f" IAM Instance Profile '{instance_profile_name}' created successfully")
        return True
        
    except iam.exceptions.EntityAlreadyExistsException:
        print(f" IAM Instance Profile '{instance_profile_name}' already exists")
        return True
    except Exception as e:
        print(f" Error creating IAM Instance Profile: {str(e)}")
        return False

def get_existing_instances():
    """Get existing instances from ASGs"""
    try:
        backend_response = autoscaling.describe_auto_scaling_groups(
            AutoScalingGroupNames=['rikhrv-mern-backend-asg']
        )
        backend_instances = backend_response['AutoScalingGroups'][0]['Instances'] if backend_response['AutoScalingGroups'] else []
        
        frontend_response = autoscaling.describe_auto_scaling_groups(
            AutoScalingGroupNames=['rikhrv-mern-frontend-asg']
        )
        frontend_instances = frontend_response['AutoScalingGroups'][0]['Instances'] if frontend_response['AutoScalingGroups'] else []
        
        return backend_instances, frontend_instances
        
    except Exception as e:
        print(f" Error getting existing instances: {str(e)}")
        return [], []

def cleanup_alb_resources():
    """Clean up ALB and related resources"""
    print("\n Cleaning up ALB resources...")
    
    try:
        alb_name = 'rikhrv-mern-alb'
        
        # Get ALB ARN
        alb_arn = get_load_balancer_arn(alb_name)
        if not alb_arn:
            print(f" ALB '{alb_name}' not found")
            return
        
        # Delete listeners first
        print(" Deleting ALB listeners...")
        listeners = elbv2.describe_listeners(LoadBalancerArn=alb_arn)
        for listener in listeners['Listeners']:
            listener_arn = listener['ListenerArn']
            
            # Delete listener rules first
            rules = elbv2.describe_rules(ListenerArn=listener_arn)
            for rule in rules['Rules']:
                if not rule['IsDefault']:  # Don't delete default rule
                    elbv2.delete_rule(RuleArn=rule['RuleArn'])
                    print(f"✓ Deleted listener rule: {rule['RuleArn']}")
            
            # Delete listener
            elbv2.delete_listener(ListenerArn=listener_arn)
            print(f"✓ Deleted listener: {listener_arn}")
        
        # Delete ALB
        print(" Deleting Application Load Balancer...")
        elbv2.delete_load_balancer(LoadBalancerArn=alb_arn)
        print(f" ALB '{alb_name}' deletion initiated")
        
        # Wait for ALB to be deleted
        print(" Waiting for ALB deletion...")
        waiter = elbv2.get_waiter('load_balancers_deleted')
        waiter.wait(LoadBalancerArns=[alb_arn])
        print(" ALB deleted successfully")
        
    except Exception as e:
        print(f" Error cleaning up ALB resources: {str(e)}")

def cleanup_target_groups():
    """Clean up target groups"""
    print("\n Cleaning up target groups...")
    
    try:
        target_groups = ['backend-tg', 'frontend-tg']
        
        for tg_name in target_groups:
            try:
                # Get target group ARN
                tg_arn = get_target_group_arn(tg_name)
                if tg_arn:
                    # Delete target group
                    elbv2.delete_target_group(TargetGroupArn=tg_arn)
                    print(f" Target group '{tg_name}' deleted")
                else:
                    print(f" Target group '{tg_name}' not found")
            except Exception as e:
                print(f" Error deleting target group '{tg_name}': {str(e)}")
                
    except Exception as e:
        print(f" Error cleaning up target groups: {str(e)}")

def get_load_balancer_arn(alb_name):
    """Get ALB ARN by name"""
    try:
        response = elbv2.describe_load_balancers(Names=[alb_name])
        if response['LoadBalancers']:
            return response['LoadBalancers'][0]['LoadBalancerArn']
        return None
    except Exception as e:
        print(f"✗ Error getting ALB ARN for '{alb_name}': {str(e)}")
        return None

def get_target_group_arn(target_group_name):
    """Get target group ARN by name"""
    try:
        response = elbv2.describe_target_groups(Names=[target_group_name])
        if response['TargetGroups']:
            return response['TargetGroups'][0]['TargetGroupArn']
        return None
    except Exception as e:
        print(f" Error getting target group '{target_group_name}': {str(e)}")
        return None

def cleanup_resources():
    """Clean up all created resources"""
    print("\n Cleaning up all resources...")
    
    try:
        # Step 1: Clean up ALB resources first
        cleanup_alb_resources()
        
        # Step 2: Delete ASGs
        print("\n Deleting Auto Scaling Groups...")
        asg_names = ['rikhrv-mern-backend-asg', 'rikhrv-mern-frontend-asg']
        
        for asg_name in asg_names:
            try:
                autoscaling.delete_auto_scaling_group(
                    AutoScalingGroupName=asg_name,
                    ForceDelete=True
                )
                print(f" ASG '{asg_name}' deletion initiated")
            except Exception as e:
                print(f" Error deleting ASG '{asg_name}': {str(e)}")
        
        # Step 3: Wait for ASGs to be deleted
        print(" Waiting for ASGs to be deleted...")
        sleep(60)  # Increased wait time for proper cleanup
        
        # Step 4: Clean up target groups
        cleanup_target_groups()
        
        # Step 5: Delete launch templates
        print("\n Deleting launch templates...")
        templates = ['rikhrv-backend-launch-template', 'rikhrv-frontend-launch-template']
        
        for template_name in templates:
            try:
                ec2.delete_launch_template(LaunchTemplateName=template_name)
                print(f" Launch template '{template_name}' deleted")
            except Exception as e:
                print(f" Error deleting launch template '{template_name}': {str(e)}")
        
        print("\n Cleanup completed successfully!")
        
    except Exception as e:
        print(f" Error during cleanup: {str(e)}")

def cleanup_specific_resource(resource_type):
    """Clean up specific resource type"""
    if resource_type == 'alb':
        cleanup_alb_resources()
    elif resource_type == 'asg':
        print("\n🔄 Deleting Auto Scaling Groups...")
        asg_names = ['rikhrv-mern-backend-asg', 'rikhrv-mern-frontend-asg']
        for asg_name in asg_names:
            try:
                autoscaling.delete_auto_scaling_group(
                    AutoScalingGroupName=asg_name,
                    ForceDelete=True
                )
                print(f" ASG '{asg_name}' deletion initiated")
            except Exception as e:
                print(f" Error deleting ASG '{asg_name}': {str(e)}")
    elif resource_type == 'tg':
        cleanup_target_groups()
    elif resource_type == 'lt':
        print("\n Deleting launch templates...")
        templates = ['rikhrv-backend-launch-template', 'rikhrv-frontend-launch-template']
        for template_name in templates:
            try:
                ec2.delete_launch_template(LaunchTemplateName=template_name)
                print(f" Launch template '{template_name}' deleted")
            except Exception as e:
                print(f" Error deleting launch template '{template_name}': {str(e)}")
    else:
        print(f" Unknown resource type: {resource_type}")

# Update the main function to include ALB cleanup options
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Deploy MERN application with ASG')
    parser.add_argument('--create-new', choices=['yes', 'no'], required=True,
                       help='Create new infrastructure or use existing')
    parser.add_argument('--cleanup', action='store_true',
                       help='Clean up all created resources')
    parser.add_argument('--cleanup-specific', choices=['alb', 'asg', 'tg', 'lt'],
                       help='Clean up specific resource type (alb, asg, tg, lt)')
    
    args = parser.parse_args()
    
    if args.cleanup:
        cleanup_resources()
    elif args.cleanup_specific:
        cleanup_specific_resource(args.cleanup_specific)
    elif args.create_new == 'yes':
        print(" Creating new MERN infrastructure with ASG...")
        
        # Create IAM Instance Profile first
        iam_success = create_iam_instance_profile()
        if not iam_success:
            print("✗ Failed to create IAM Instance Profile. Exiting...")
            exit(1)
        
        # Wait a moment for IAM propagation
        print(" Waiting for IAM propagation...")
        sleep(10)
        
        backend_success = create_backend_asg()
        frontend_success = create_frontend_asg()
        
        if backend_success and frontend_success:
            print("\n Infrastructure created successfully!")
            print("\n Next steps:")
            print("1. Set up Application Load Balancer and attach target groups")
            print("2. Configure CloudFlare DNS for backend and frontend")
            print("3. Test the deployed services")
        else:
            print("\n Infrastructure creation failed!")
            
    else:
        print(" Using existing infrastructure...")
        backend_instances, frontend_instances = get_existing_instances()
        
        print(f"\n Backend instances ({len(backend_instances)}):")
        for instance in backend_instances:
            print(f"  - {instance['InstanceId']} ({instance['LifecycleState']})")
            
        print(f"\n Frontend instances ({len(frontend_instances)}):")
        for instance in frontend_instances:
            print(f"  - {instance['InstanceId']} ({instance['LifecycleState']})")