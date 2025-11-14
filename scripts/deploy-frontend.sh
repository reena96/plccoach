#!/bin/bash
set -e

# Deploy Frontend to S3 and CloudFront
# Builds the frontend and deploys to production

AWS_REGION="us-east-1"

echo "🎨 Deploying Frontend to S3/CloudFront"
echo "======================================"
echo ""

# Load Terraform outputs
cd infrastructure
TERRAFORM_OUTPUTS=$(terraform output -json)
cd ..

S3_BUCKET=$(echo $TERRAFORM_OUTPUTS | jq -r '.s3_frontend_bucket.value')
CLOUDFRONT_ID=$(echo $TERRAFORM_OUTPUTS | jq -r '.cloudfront_distribution_id.value')
CLOUDFRONT_DOMAIN=$(echo $TERRAFORM_OUTPUTS | jq -r '.cloudfront_domain_name.value')
ALB_DNS=$(echo $TERRAFORM_OUTPUTS | jq -r '.alb_dns_name.value')

echo "📦 Configuration:"
echo "  S3 Bucket: $S3_BUCKET"
echo "  CloudFront ID: $CLOUDFRONT_ID"
echo "  CloudFront Domain: $CLOUDFRONT_DOMAIN"
echo "  API Endpoint: http://$ALB_DNS"
echo ""

# Check if frontend directory exists
if [ ! -d "frontend" ]; then
    echo "❌ frontend directory not found"
    echo "   This project doesn't have a frontend yet (Story 1.7 may not be complete)"
    exit 1
fi

cd frontend

# Install dependencies
echo "📥 Installing dependencies..."
npm ci --silent

# Build frontend
echo "🔨 Building frontend..."
echo "   Using API endpoint: http://$ALB_DNS"

# Set API endpoint for build
export VITE_API_URL="http://$ALB_DNS"

npm run build

echo "  ✅ Build complete"
echo ""

# Upload to S3
echo "📤 Uploading to S3..."
aws s3 sync dist/ s3://$S3_BUCKET/ \
    --region $AWS_REGION \
    --delete \
    --cache-control "public, max-age=31536000, immutable" \
    --exclude "index.html"

# Upload index.html with no-cache
aws s3 cp dist/index.html s3://$S3_BUCKET/index.html \
    --region $AWS_REGION \
    --cache-control "no-cache, no-store, must-revalidate" \
    --content-type "text/html"

echo "  ✅ Uploaded to S3"
echo ""

# Invalidate CloudFront cache
echo "🔄 Invalidating CloudFront cache..."
INVALIDATION_ID=$(aws cloudfront create-invalidation \
    --distribution-id $CLOUDFRONT_ID \
    --paths "/*" \
    --query 'Invalidation.Id' \
    --output text)

echo "  ✅ Invalidation created: $INVALIDATION_ID"
echo "     (This may take 1-2 minutes to complete)"
echo ""

cd ..

echo "🎉 Frontend Deployment Complete!"
echo "================================="
echo ""
echo "🌐 Access URLs:"
echo "  Frontend: https://$CLOUDFRONT_DOMAIN"
echo "  Backend API: http://$ALB_DNS"
echo ""
echo "📝 Next steps:"
echo "  1. Open browser: https://$CLOUDFRONT_DOMAIN"
echo "  2. Test OAuth login flows"
echo "  3. Verify all features work in production"
