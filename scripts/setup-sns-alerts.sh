#!/bin/bash
set -e

# Setup SNS Email Alerts for CloudWatch Alarms
# Subscribes an email address to receive production alerts

AWS_REGION="us-east-1"

echo "📧 Setting up SNS Email Alerts"
echo "==============================="
echo ""

if [ -z "$1" ]; then
    echo "Usage: $0 <email@example.com>"
    echo ""
    echo "Example:"
    echo "  $0 your-email@example.com"
    exit 1
fi

EMAIL=$1

# Load SNS topic ARN from Terraform
cd infrastructure
SNS_TOPIC_ARN=$(terraform output -json | jq -r '.sns_alarms_topic_arn.value')
cd ..

echo "SNS Topic: $SNS_TOPIC_ARN"
echo "Email: $EMAIL"
echo ""

# Subscribe email to SNS topic
echo "📬 Subscribing email to SNS topic..."

SUBSCRIPTION_ARN=$(aws sns subscribe \
    --topic-arn "$SNS_TOPIC_ARN" \
    --protocol email \
    --notification-endpoint "$EMAIL" \
    --region $AWS_REGION \
    --output text)

echo "  ✅ Subscription created: $SUBSCRIPTION_ARN"
echo ""
echo "⚠️  IMPORTANT: Check your email inbox for confirmation!"
echo ""
echo "AWS has sent a confirmation email to: $EMAIL"
echo "You must click the confirmation link to start receiving alerts."
echo ""
echo "Once confirmed, you'll receive notifications for:"
echo "  - High API error rate (>5%)"
echo "  - Slow API response times (>10 seconds)"
echo "  - High database connection usage (>80%)"
echo "  - Unhealthy ECS tasks"
echo ""
echo "You can manage subscriptions at:"
echo "https://console.aws.amazon.com/sns/v3/home?region=$AWS_REGION#/topic/$SNS_TOPIC_ARN"
