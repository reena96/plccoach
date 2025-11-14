#!/bin/bash
set -e

# Setup AWS Secrets Manager for PLC Coach Production
# This script creates all required secrets for the application

AWS_REGION="us-east-1"
echo "🔒 Setting up AWS Secrets Manager for PLC Coach"
echo "================================================"
echo ""

# Function to create or update secret
create_or_update_secret() {
    local secret_name=$1
    local secret_value=$2
    local description=$3

    # Check if secret exists
    if aws secretsmanager describe-secret --secret-id "$secret_name" --region "$AWS_REGION" &> /dev/null; then
        echo "  → Updating existing secret: $secret_name"
        aws secretsmanager put-secret-value \
            --secret-id "$secret_name" \
            --secret-string "$secret_value" \
            --region "$AWS_REGION" \
            --output text > /dev/null
    else
        echo "  → Creating new secret: $secret_name"
        aws secretsmanager create-secret \
            --name "$secret_name" \
            --description "$description" \
            --secret-string "$secret_value" \
            --region "$AWS_REGION" \
            --tags Key=Project,Value=plccoach Key=Environment,Value=production \
            --output text > /dev/null
    fi
}

# Google OAuth Credentials
echo "📝 Google OAuth Configuration"
echo "------------------------------"
echo "Get these from: https://console.cloud.google.com/apis/credentials"
echo ""
read -p "Google Client ID: " GOOGLE_CLIENT_ID
read -sp "Google Client Secret: " GOOGLE_CLIENT_SECRET
echo ""
echo ""

if [ -z "$GOOGLE_CLIENT_ID" ] || [ -z "$GOOGLE_CLIENT_SECRET" ]; then
    echo "❌ Google OAuth credentials are required"
    exit 1
fi

GOOGLE_SECRET=$(cat <<EOF
{
  "GOOGLE_CLIENT_ID": "$GOOGLE_CLIENT_ID",
  "GOOGLE_CLIENT_SECRET": "$GOOGLE_CLIENT_SECRET"
}
EOF
)

create_or_update_secret \
    "plccoach/production/google-oauth" \
    "$GOOGLE_SECRET" \
    "Google OAuth credentials for PLC Coach"

echo "✅ Google OAuth secret configured"
echo ""

# Clever SSO Credentials
echo "📝 Clever SSO Configuration"
echo "----------------------------"
echo "Get these from: https://apps.clever.com/"
echo ""
read -p "Clever Client ID: " CLEVER_CLIENT_ID
read -sp "Clever Client Secret: " CLEVER_CLIENT_SECRET
echo ""
echo ""

if [ -z "$CLEVER_CLIENT_ID" ] || [ -z "$CLEVER_CLIENT_SECRET" ]; then
    echo "❌ Clever SSO credentials are required"
    exit 1
fi

CLEVER_SECRET=$(cat <<EOF
{
  "CLEVER_CLIENT_ID": "$CLEVER_CLIENT_ID",
  "CLEVER_CLIENT_SECRET": "$CLEVER_CLIENT_SECRET"
}
EOF
)

create_or_update_secret \
    "plccoach/production/clever-sso" \
    "$CLEVER_SECRET" \
    "Clever SSO credentials for PLC Coach"

echo "✅ Clever SSO secret configured"
echo ""

# Session Secret
echo "📝 Session Secret Configuration"
echo "--------------------------------"
echo "This is used for encrypting session cookies"
echo ""
read -p "Generate random session secret? (Y/n): " GENERATE_SESSION
GENERATE_SESSION=${GENERATE_SESSION:-Y}

if [[ "$GENERATE_SESSION" =~ ^[Yy] ]]; then
    SESSION_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(64))")
    echo "✅ Generated secure random session secret"
else
    read -sp "Enter Session Secret (64+ characters): " SESSION_SECRET
    echo ""

    if [ ${#SESSION_SECRET} -lt 64 ]; then
        echo "⚠️  Warning: Session secret should be at least 64 characters"
        read -p "Continue anyway? (y/N): " CONTINUE
        if [[ ! "$CONTINUE" =~ ^[Yy] ]]; then
            exit 1
        fi
    fi
fi

SESSION_SECRET_JSON=$(cat <<EOF
{
  "SESSION_SECRET_KEY": "$SESSION_SECRET"
}
EOF
)

create_or_update_secret \
    "plccoach/production/session" \
    "$SESSION_SECRET_JSON" \
    "Session encryption key for PLC Coach"

echo "✅ Session secret configured"
echo ""

# Verify all secrets exist
echo "🔍 Verifying secrets..."
echo "------------------------"

SECRETS=(
    "plccoach-db-password"
    "plccoach/production/google-oauth"
    "plccoach/production/clever-sso"
    "plccoach/production/session"
)

ALL_EXIST=true
for secret in "${SECRETS[@]}"; do
    if aws secretsmanager describe-secret --secret-id "$secret" --region "$AWS_REGION" &> /dev/null; then
        ARN=$(aws secretsmanager describe-secret --secret-id "$secret" --region "$AWS_REGION" --query 'ARN' --output text)
        echo "  ✅ $secret"
        echo "     ARN: $ARN"
    else
        echo "  ❌ $secret - NOT FOUND"
        ALL_EXIST=false
    fi
done

echo ""

if [ "$ALL_EXIST" = true ]; then
    echo "🎉 All secrets configured successfully!"
    echo ""
    echo "📋 Next steps:"
    echo "  1. Update OAuth redirect URIs to production URLs"
    echo "  2. Run ./scripts/deploy-ecs-service.sh to deploy the API"
    echo "  3. Run ./scripts/deploy-frontend.sh to deploy the frontend"
else
    echo "❌ Some secrets are missing. Please check the errors above."
    exit 1
fi
