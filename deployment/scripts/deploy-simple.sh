#!/bin/bash

# Simple Lambda Container Deployment Script
set -e

# Configuration
AWS_PROFILE="yet"
AWS_REGION="eu-west-2"
ENVIRONMENT="${1:-staging}"
STACK_NAME="omni-llm-${ENVIRONMENT}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Get project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT"

print_status "Starting simple deployment to environment: $ENVIRONMENT"

# Step 1: Deploy CloudFormation stack (creates ECR repo and Lambda with base image)
print_status "Deploying CloudFormation stack..."

aws cloudformation deploy \
    --template-file deployment/cloudformation/infrastructure-simple.yaml \
    --stack-name "$STACK_NAME" \
    --parameter-overrides \
        Environment="$ENVIRONMENT" \
        APIKeyValue="omni-$(openssl rand -hex 16)" \
        LambdaMemorySize="1024" \
        LambdaTimeout="900" \
    --capabilities CAPABILITY_IAM \
    --region "$AWS_REGION" \
    --profile "$AWS_PROFILE" \
    --no-fail-on-empty-changeset

if [ $? -eq 0 ]; then
    print_success "CloudFormation stack deployed successfully"
else
    print_error "CloudFormation deployment failed"
    exit 1
fi

# Step 2: Get ECR repository URI
ECR_REPO_URI=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$AWS_REGION" \
    --profile "$AWS_PROFILE" \
    --query "Stacks[0].Outputs[?OutputKey=='ECRRepositoryURI'].OutputValue" \
    --output text)

print_status "ECR Repository: $ECR_REPO_URI"

# Step 3: Login to ECR
print_status "Logging into ECR..."
aws ecr get-login-password --region "$AWS_REGION" --profile "$AWS_PROFILE" | \
    docker login --username AWS --password-stdin "$(echo $ECR_REPO_URI | cut -d'/' -f1)"

# Step 4: Build Docker image
print_status "Building Docker image..."
docker build -t omni-llm:latest .

# Step 5: Tag image for ECR
print_status "Tagging image for ECR..."
docker tag omni-llm:latest "${ECR_REPO_URI}:latest"

# Step 6: Push image to ECR
print_status "Pushing image to ECR..."
docker push "${ECR_REPO_URI}:latest"

if [ $? -eq 0 ]; then
    print_success "Docker image pushed to ECR successfully"
else
    print_error "Failed to push Docker image to ECR"
    exit 1
fi

# Step 7: Get Lambda function name and recreate with container package type
LAMBDA_FUNCTION_NAME=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$AWS_REGION" \
    --profile "$AWS_PROFILE" \
    --query "Stacks[0].Outputs[?OutputKey=='LambdaFunctionName'].OutputValue" \
    --output text)

print_status "Converting Lambda function to container package type: $LAMBDA_FUNCTION_NAME"

# Get the Lambda execution role ARN
LAMBDA_ROLE_ARN=$(aws lambda get-function \
    --function-name "$LAMBDA_FUNCTION_NAME" \
    --region "$AWS_REGION" \
    --profile "$AWS_PROFILE" \
    --query "Configuration.Role" \
    --output text)

# Delete the existing ZIP-based function
print_status "Deleting ZIP-based Lambda function..."
aws lambda delete-function \
    --function-name "$LAMBDA_FUNCTION_NAME" \
    --region "$AWS_REGION" \
    --profile "$AWS_PROFILE"

# Wait a moment for deletion to complete
sleep 10

# Create new container-based function
print_status "Creating container-based Lambda function..."
aws lambda create-function \
    --function-name "$LAMBDA_FUNCTION_NAME" \
    --role "$LAMBDA_ROLE_ARN" \
    --code ImageUri="${ECR_REPO_URI}:latest" \
    --package-type Image \
    --architectures arm64 \
    --memory-size 1024 \
    --timeout 900 \
    --environment Variables="{ENVIRONMENT=$ENVIRONMENT}" \
    --region "$AWS_REGION" \
    --profile "$AWS_PROFILE" \
    > /dev/null

if [ $? -eq 0 ]; then
    print_success "Container-based Lambda function created successfully"
else
    print_error "Failed to create container-based Lambda function"
    exit 1
fi

# Step 8: Wait for function to be updated
print_status "Waiting for function update to complete..."
aws lambda wait function-updated \
    --function-name "$LAMBDA_FUNCTION_NAME" \
    --region "$AWS_REGION" \
    --profile "$AWS_PROFILE"

# Get deployment outputs
API_ENDPOINT=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$AWS_REGION" \
    --profile "$AWS_PROFILE" \
    --query "Stacks[0].Outputs[?OutputKey=='APIEndpoint'].OutputValue" \
    --output text)

API_KEY_ID=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$AWS_REGION" \
    --profile "$AWS_PROFILE" \
    --query "Stacks[0].Outputs[?OutputKey=='APIKey'].OutputValue" \
    --output text)

# Get the actual API key value
API_KEY_VALUE=$(aws apigateway get-api-key \
    --api-key "$API_KEY_ID" \
    --include-value \
    --region "$AWS_REGION" \
    --profile "$AWS_PROFILE" \
    --query "value" \
    --output text)

# Test the deployment
print_status "Testing deployment..."
TEST_RESPONSE=$(curl -s -w "%{http_code}" \
    -X POST \
    -H "Content-Type: application/json" \
    -H "x-api-key: $API_KEY_VALUE" \
    -d '{"prompt": "Hello, world! Please respond with a simple greeting.", "max_tokens": 50}' \
    "$API_ENDPOINT/invoke")

HTTP_CODE="${TEST_RESPONSE: -3}"
RESPONSE_BODY="${TEST_RESPONSE%???}"

if [ "$HTTP_CODE" = "200" ]; then
    print_success "Deployment test passed!"
else
    print_warning "Deployment test returned HTTP $HTTP_CODE. Response: $RESPONSE_BODY"
fi

print_success "Deployment completed successfully!"
echo "=================================================================="
echo "                    DEPLOYMENT SUMMARY"
echo "=================================================================="
echo "Environment:      $ENVIRONMENT"
echo "Stack Name:       $STACK_NAME"
echo "Region:           $AWS_REGION"
echo "API Endpoint:     $API_ENDPOINT"
echo "API Key:          $API_KEY_VALUE"
echo "ECR Repository:   $ECR_REPO_URI"
echo "Lambda Function:  $LAMBDA_FUNCTION_NAME"
echo ""
echo "Test your deployment:"
echo "curl -X POST \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -H \"x-api-key: $API_KEY_VALUE\" \\"
echo "  -d '{\"prompt\": \"Hello!\", \"max_tokens\": 50}' \\"
echo "  \"$API_ENDPOINT/invoke\""
echo ""
echo "Health check:"
echo "curl \"$API_ENDPOINT/health\""
echo "=================================================================="