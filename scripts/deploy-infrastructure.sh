#!/bin/bash
# PLC Coach - Infrastructure Deployment Script
# This script automates the infrastructure deployment process

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to check prerequisites
check_prerequisites() {
    print_info "Checking prerequisites..."

    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI is not installed. Please install it first."
        exit 1
    fi
    print_success "AWS CLI found"

    # Check Terraform
    if ! command -v terraform &> /dev/null; then
        print_error "Terraform is not installed. Please install it first."
        exit 1
    fi
    print_success "Terraform found ($(terraform version | head -n1))"

    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS credentials not configured. Run 'aws configure' first."
        exit 1
    fi
    print_success "AWS credentials configured"

    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    AWS_REGION=$(aws configure get region)
    print_info "AWS Account: $ACCOUNT_ID"
    print_info "AWS Region: $AWS_REGION"
}

# Function to setup Terraform
setup_terraform() {
    print_info "Setting up Terraform..."

    cd infrastructure

    # Check if terraform.tfvars exists
    if [ ! -f terraform.tfvars ]; then
        print_warning "terraform.tfvars not found. Creating from example..."
        cp terraform.tfvars.example terraform.tfvars
        print_warning "Please edit infrastructure/terraform.tfvars with your settings."
        read -p "Press enter when ready to continue..."
    fi

    # Initialize Terraform
    print_info "Initializing Terraform..."
    terraform init

    print_success "Terraform initialized"
}

# Function to plan deployment
plan_deployment() {
    print_info "Planning infrastructure deployment..."

    cd infrastructure
    terraform plan -out=tfplan

    print_success "Plan created successfully"
    print_warning "Review the plan above carefully."
}

# Function to deploy infrastructure
deploy_infrastructure() {
    print_info "Deploying infrastructure..."
    print_warning "This will take 15-20 minutes due to RDS creation."

    cd infrastructure

    if [ -f tfplan ]; then
        terraform apply tfplan
        rm tfplan
    else
        terraform apply
    fi

    print_success "Infrastructure deployed successfully!"
}

# Function to save outputs
save_outputs() {
    print_info "Saving Terraform outputs..."

    cd infrastructure
    terraform output > ../infrastructure-outputs.txt
    terraform output -json > ../infrastructure-outputs.json

    print_success "Outputs saved to infrastructure-outputs.txt and infrastructure-outputs.json"
}

# Function to post-deployment setup
post_deployment_setup() {
    print_info "Post-deployment setup..."

    cd infrastructure

    # Get important values
    ALB_DNS=$(terraform output -raw alb_dns_name)
    ECR_REPO=$(terraform output -raw ecr_repository_url)
    CF_DOMAIN=$(terraform output -raw cloudfront_domain_name)
    SNS_TOPIC=$(terraform output -raw sns_alarms_topic_arn)

    echo ""
    print_success "Infrastructure deployed successfully!"
    echo ""
    print_info "=== Important URLs and Values ==="
    echo ""
    echo "API Endpoint (ALB):       http://$ALB_DNS"
    echo "Frontend (CloudFront):    https://$CF_DOMAIN"
    echo "ECR Repository:           $ECR_REPO"
    echo ""
    print_info "=== Next Steps ==="
    echo ""
    echo "1. Subscribe to CloudWatch alarms:"
    echo "   aws sns subscribe --topic-arn $SNS_TOPIC \\"
    echo "     --protocol email --notification-endpoint your-email@example.com"
    echo ""
    echo "2. Set up GitHub Secrets for CI/CD:"
    echo "   - AWS_ROLE_TO_ASSUME"
    echo "   - API_URL: http://$ALB_DNS"
    echo ""
    echo "3. (Optional) Set up custom domain with ACM certificate"
    echo ""
    echo "4. Deploy your application code using GitHub Actions"
    echo ""
}

# Main execution
main() {
    echo ""
    echo "============================================"
    echo "PLC Coach - Infrastructure Deployment"
    echo "============================================"
    echo ""

    check_prerequisites
    setup_terraform
    plan_deployment

    echo ""
    read -p "Do you want to proceed with deployment? (yes/no): " -r
    echo ""
    if [[ $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        deploy_infrastructure
        save_outputs
        post_deployment_setup
    else
        print_warning "Deployment cancelled."
        exit 0
    fi
}

# Run main function
main
