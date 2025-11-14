#!/bin/bash
set -e

# Deploy ECS Service for PLC Coach API
# Requires: ECR image already pushed, secrets configured

AWS_REGION="us-east-1"
AWS_ACCOUNT_ID="971422717446"
CLUSTER_NAME="plccoach-cluster"
SERVICE_NAME="plccoach-api-service"
TASK_FAMILY="plccoach-api-task"

echo "🚀 Deploying PLC Coach API to ECS"
echo "=================================="
echo ""

# Load Terraform outputs
cd infrastructure
TERRAFORM_OUTPUTS=$(terraform output -json)
cd ..

# Extract values
ECR_REPO=$(echo $TERRAFORM_OUTPUTS | jq -r '.ecr_repository_url.value')
TASK_EXECUTION_ROLE=$(echo $TERRAFORM_OUTPUTS | jq -r '.ecs_task_execution_role_arn.value')
TASK_ROLE=$(echo $TERRAFORM_OUTPUTS | jq -r '.ecs_task_role_arn.value')
TARGET_GROUP_ARN=$(echo $TERRAFORM_OUTPUTS | jq -r '.target_group_arn.value')
ECS_SECURITY_GROUP=$(echo $TERRAFORM_OUTPUTS | jq -r '.ecs_security_group_id.value')
PRIVATE_SUBNETS=$(echo $TERRAFORM_OUTPUTS | jq -r '.private_subnet_ids.value | join(",")')
DB_SECRET_ARN=$(echo $TERRAFORM_OUTPUTS | jq -r '.db_secret_arn.value')
ALB_DNS=$(echo $TERRAFORM_OUTPUTS | jq -r '.alb_dns_name.value')

# Get full secret ARNs dynamically
GOOGLE_OAUTH_SECRET_ARN=$(aws secretsmanager describe-secret --secret-id plccoach/production/google-oauth --region $AWS_REGION --query 'ARN' --output text)
CLEVER_SSO_SECRET_ARN=$(aws secretsmanager describe-secret --secret-id plccoach/production/clever-sso --region $AWS_REGION --query 'ARN' --output text)
SESSION_SECRET_ARN=$(aws secretsmanager describe-secret --secret-id plccoach/production/session --region $AWS_REGION --query 'ARN' --output text)

echo "📦 Configuration:"
echo "  ECR Repository: $ECR_REPO"
echo "  Cluster: $CLUSTER_NAME"
echo "  Service: $SERVICE_NAME"
echo ""

# Check if image exists in ECR
echo "🔍 Checking for Docker image in ECR..."
IMAGE_TAG="latest"
IMAGE_URI="$ECR_REPO:$IMAGE_TAG"

if aws ecr describe-images --repository-name plccoach/api --image-ids imageTag=$IMAGE_TAG --region $AWS_REGION &> /dev/null; then
    echo "  ✅ Image found: $IMAGE_URI"
else
    echo "  ❌ No image found with tag '$IMAGE_TAG'"
    echo ""
    echo "  Please build and push the Docker image first:"
    echo "    cd api-service"
    echo "    docker build -t $ECR_REPO:$IMAGE_TAG ."
    echo "    aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REPO"
    echo "    docker push $ECR_REPO:$IMAGE_TAG"
    exit 1
fi

# Create ECS Task Definition
echo ""
echo "🔧 Configuring ALB and Target Group..."

# Get ALB listener ARN
ALB_ARN=$(echo $TERRAFORM_OUTPUTS | jq -r '.alb_arn.value // empty')
if [ -z "$ALB_ARN" ]; then
    ALB_ARN="arn:aws:elasticloadbalancing:$AWS_REGION:$AWS_ACCOUNT_ID:loadbalancer/app/plccoach-alb/0497c3ffc2e6d833"
fi

LISTENER_ARN=$(aws elbv2 describe-listeners --load-balancer-arn $ALB_ARN --region $AWS_REGION --query 'Listeners[0].ListenerArn' --output text)

# Configure ALB listener to forward to target group
aws elbv2 modify-listener \
    --listener-arn $LISTENER_ARN \
    --default-actions Type=forward,TargetGroupArn=$TARGET_GROUP_ARN \
    --region $AWS_REGION > /dev/null 2>&1

# Configure target group health check
aws elbv2 modify-target-group \
    --target-group-arn $TARGET_GROUP_ARN \
    --health-check-path /api/health \
    --health-check-interval-seconds 30 \
    --health-check-timeout-seconds 5 \
    --healthy-threshold-count 2 \
    --unhealthy-threshold-count 3 \
    --region $AWS_REGION > /dev/null

echo "  ✅ ALB and health check configured"
echo ""
echo "📝 Creating ECS Task Definition..."

TASK_DEF_JSON=$(cat <<EOF
{
  "family": "$TASK_FAMILY",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "$TASK_EXECUTION_ROLE",
  "taskRoleArn": "$TASK_ROLE",
  "containerDefinitions": [
    {
      "name": "api",
      "image": "$IMAGE_URI",
      "essential": true,
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "ENVIRONMENT",
          "value": "production"
        },
        {
          "name": "LOG_LEVEL",
          "value": "INFO"
        },
        {
          "name": "OAUTH_REDIRECT_BASE_URL",
          "value": "http://$ALB_DNS"
        }
      ],
      "secrets": [
        {
          "name": "DATABASE_URL",
          "valueFrom": "$DB_SECRET_ARN:database_url::"
        },
        {
          "name": "GOOGLE_CLIENT_ID",
          "valueFrom": "$GOOGLE_OAUTH_SECRET_ARN:GOOGLE_CLIENT_ID::"
        },
        {
          "name": "GOOGLE_CLIENT_SECRET",
          "valueFrom": "$GOOGLE_OAUTH_SECRET_ARN:GOOGLE_CLIENT_SECRET::"
        },
        {
          "name": "CLEVER_CLIENT_ID",
          "valueFrom": "$CLEVER_SSO_SECRET_ARN:CLEVER_CLIENT_ID::"
        },
        {
          "name": "CLEVER_CLIENT_SECRET",
          "valueFrom": "$CLEVER_SSO_SECRET_ARN:CLEVER_CLIENT_SECRET::"
        },
        {
          "name": "SESSION_SECRET_KEY",
          "valueFrom": "$SESSION_SECRET_ARN:SESSION_SECRET_KEY::"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/plccoach/api",
          "awslogs-region": "$AWS_REGION",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/api/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ]
}
EOF
)

TASK_DEF_ARN=$(aws ecs register-task-definition \
    --cli-input-json "$TASK_DEF_JSON" \
    --region $AWS_REGION \
    --query 'taskDefinition.taskDefinitionArn' \
    --output text)

echo "  ✅ Task Definition created: $TASK_DEF_ARN"

# Check if service exists
echo ""
echo "🔍 Checking for existing ECS service..."

SERVICE_STATUS=$(aws ecs describe-services --cluster $CLUSTER_NAME --services $SERVICE_NAME --region $AWS_REGION --query 'services[0].status' --output text 2>/dev/null || echo "NONE")

if [ "$SERVICE_STATUS" = "ACTIVE" ]; then
    echo "  ℹ️  Service exists - updating..."

    aws ecs update-service \
        --cluster $CLUSTER_NAME \
        --service $SERVICE_NAME \
        --task-definition $TASK_FAMILY \
        --network-configuration "awsvpcConfiguration={subnets=[$PRIVATE_SUBNETS],securityGroups=[$ECS_SECURITY_GROUP],assignPublicIp=ENABLED}" \
        --region $AWS_REGION \
        --output text > /dev/null

    echo "  ✅ Service updated"
else
    echo "  ℹ️  Service doesn't exist or is inactive - creating..."

    # Create service (using public subnets with public IP enabled)
    aws ecs create-service \
        --cluster $CLUSTER_NAME \
        --service-name $SERVICE_NAME \
        --task-definition $TASK_FAMILY \
        --desired-count 2 \
        --launch-type FARGATE \
        --platform-version LATEST \
        --network-configuration "awsvpcConfiguration={subnets=[$PRIVATE_SUBNETS],securityGroups=[$ECS_SECURITY_GROUP],assignPublicIp=ENABLED}" \
        --load-balancers "targetGroupArn=$TARGET_GROUP_ARN,containerName=api,containerPort=8000" \
        --health-check-grace-period-seconds 60 \
        --deployment-configuration "deploymentCircuitBreaker={enable=true,rollback=true},maximumPercent=200,minimumHealthyPercent=100" \
        --region $AWS_REGION \
        --output text > /dev/null

    echo "  ✅ Service created"
fi

echo ""
echo "⏳ Waiting for service to stabilize (this may take 2-3 minutes)..."

aws ecs wait services-stable \
    --cluster $CLUSTER_NAME \
    --services $SERVICE_NAME \
    --region $AWS_REGION

echo ""
echo "🎉 Deployment Complete!"
echo "======================="
echo ""
echo "📊 Service Status:"
aws ecs describe-services \
    --cluster $CLUSTER_NAME \
    --services $SERVICE_NAME \
    --region $AWS_REGION \
    --query 'services[0].{Name:serviceName,Status:status,Running:runningCount,Desired:desiredCount,Pending:pendingCount}' \
    --output table

echo ""
echo "🌐 Access URLs:"
echo "  API Endpoint: http://$ALB_DNS"
echo "  Health Check: http://$ALB_DNS/api/health"
echo "  Ready Check:  http://$ALB_DNS/api/ready"
echo ""
echo "📝 Next steps:"
echo "  1. Test health endpoint: curl http://$ALB_DNS/api/health"
echo "  2. Run smoke tests: ./scripts/smoke-tests.sh"
echo "  3. Deploy frontend: ./scripts/deploy-frontend.sh"
echo "  4. Update OAuth redirect URLs to: http://$ALB_DNS/auth/google/callback"
