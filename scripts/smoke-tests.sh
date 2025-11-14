#!/bin/bash
# Smoke Tests for Production Deployment
# Validates that deployment is working correctly

set -e

# Load configuration
AWS_REGION="us-east-1"
cd infrastructure
ALB_DNS=$(terraform output -json | jq -r '.alb_dns_name.value')
CLOUDFRONT_DOMAIN=$(terraform output -json | jq -r '.cloudfront_domain_name.value')
cd ..

API_URL="http://$ALB_DNS"
FRONTEND_URL="https://$CLOUDFRONT_DOMAIN"

echo "🔬 Running Smoke Tests"
echo "====================="
echo ""
echo "API: $API_URL"
echo "Frontend: $FRONTEND_URL"
echo ""

FAILED=0
PASSED=0

# Test function
test_endpoint() {
    local name=$1
    local url=$2
    local expected_status=$3
    local description=$4

    echo -n "Testing: $name... "

    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$url" -L)

    if [ "$HTTP_STATUS" = "$expected_status" ]; then
        echo "✅ PASSED (HTTP $HTTP_STATUS)"
        PASSED=$((PASSED + 1))
    else
        echo "❌ FAILED (Expected $expected_status, got $HTTP_STATUS)"
        echo "   $description"
        FAILED=$((FAILED + 1))
    fi
}

# Test health endpoint
test_endpoint \
    "Health endpoint" \
    "$API_URL/api/health" \
    "200" \
    "Health check should return 200 OK"

# Test ready endpoint
test_endpoint \
    "Ready endpoint" \
    "$API_URL/api/ready" \
    "200" \
    "Ready check should return 200 OK (database connected)"

# Test Google OAuth redirect
test_endpoint \
    "Google OAuth" \
    "$API_URL/auth/google/login" \
    "302" \
    "Google OAuth should redirect to Google login (302)"

# Test Clever SSO redirect
test_endpoint \
    "Clever SSO" \
    "$API_URL/auth/clever/login" \
    "302" \
    "Clever SSO should redirect to Clever login (302)"

# Test frontend loads
test_endpoint \
    "Frontend" \
    "$FRONTEND_URL" \
    "200" \
    "Frontend should load successfully"

# Test API CORS (if frontend is calling API)
echo -n "Testing: CORS headers... "
CORS_HEADER=$(curl -s -I "$API_URL/api/health" | grep -i "access-control-allow-origin" || true)
if [ -n "$CORS_HEADER" ]; then
    echo "✅ PASSED"
    PASSED=$((PASSED + 1))
else
    echo "⚠️  WARNING (No CORS headers found - may need configuration)"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test Results:"
echo "  ✅ Passed: $PASSED"
echo "  ❌ Failed: $FAILED"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ $FAILED -eq 0 ]; then
    echo "🎉 All smoke tests passed!"
    echo ""
    echo "Production deployment is healthy and ready for use."
    exit 0
else
    echo "⚠️  Some smoke tests failed!"
    echo ""
    echo "Please check the errors above and verify:"
    echo "  - ECS service is running"
    echo "  - Database is accessible"
    echo "  - OAuth credentials are configured"
    echo "  - Frontend build completed successfully"
    exit 1
fi
