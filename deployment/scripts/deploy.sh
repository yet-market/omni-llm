#!/bin/bash

# Omni-LLM Deployment Script
# ==========================
# Deploys the Lambda function and infrastructure to AWS
# Uses the 'yet' profile and eu-west-2 region

set -e

# Configuration
AWS_PROFILE="yet"
AWS_REGION="eu-west-2"
ENVIRONMENT="${1:-staging}"
STACK_NAME="omni-llm-${ENVIRONMENT}"

# Validate environment
if [[ "$ENVIRONMENT" != "staging" && "$ENVIRONMENT" != "prod" ]]; then
    print_error "Environment must be 'staging' or 'prod'. Got: $ENVIRONMENT"
    echo "Usage: $0 [staging|prod]"
    echo "  staging - Development/testing environment"
    echo "  prod    - Production environment"
    exit 1
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    print_error "AWS CLI is not installed. Please install it first."
    exit 1
fi

# Check if Docker is installed and running
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install it first."
    exit 1
fi

if ! docker info &> /dev/null; then
    print_error "Docker is not running. Please start Docker first."
    exit 1
fi

# Validate AWS profile
if ! aws sts get-caller-identity --profile "$AWS_PROFILE" &> /dev/null; then
    print_error "AWS profile '$AWS_PROFILE' is not configured or invalid."
    exit 1
fi

print_status "Starting deployment to environment: $ENVIRONMENT"
print_status "Using AWS profile: $AWS_PROFILE"
print_status "Target region: $AWS_REGION"
print_status "Stack name: $STACK_NAME"

# Environment-specific configuration
if [ "$ENVIRONMENT" = "staging" ]; then
    print_status "🚧 STAGING DEPLOYMENT - Development/Testing Environment"
    LAMBDA_MEMORY_SIZE=1024
    API_THROTTLE_RATE=100
    API_THROTTLE_BURST=200
else
    print_status "🚀 PRODUCTION DEPLOYMENT - Live Environment"
    LAMBDA_MEMORY_SIZE=2048
    API_THROTTLE_RATE=1000
    API_THROTTLE_BURST=2000
fi

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Change to project root
cd "$PROJECT_ROOT"

# Create build directory
BUILD_DIR="$PROJECT_ROOT/deployment/build"
mkdir -p "$BUILD_DIR"

print_status "Building Docker image..."

# Build Docker image
docker build -t omni-llm:latest .

print_status "Creating Lambda deployment package..."

# Create a container to extract the deployment package
docker run --rm \
    -v "$BUILD_DIR:/output" \
    omni-llm:latest \
    sh -c "cd /var/task && zip -r /output/lambda-deployment.zip . -x '*.pyc' '*/__pycache__/*'"

# Check if deployment package was created
if [ ! -f "$BUILD_DIR/lambda-deployment.zip" ]; then
    print_error "Failed to create deployment package"
    exit 1
fi

print_success "Deployment package created: $(du -h $BUILD_DIR/lambda-deployment.zip | cut -f1)"

# Load environment-specific configuration
ENV_CONFIG_FILE="$PROJECT_ROOT/deployment/config/${ENVIRONMENT}.env"
if [ -f "$ENV_CONFIG_FILE" ]; then
    print_status "Loading $ENVIRONMENT environment configuration..."
    set -a
    source "$ENV_CONFIG_FILE"
    set +a
    print_success "Environment configuration loaded from $ENV_CONFIG_FILE"
fi

# Load local .env file for additional overrides (primarily for staging)
if [ -f "$PROJECT_ROOT/.env" ]; then
    print_status "Loading local .env overrides..."
    set -a
    source "$PROJECT_ROOT/.env"
    set +a
    print_success "Local environment variables loaded from .env"
else
    print_warning ".env file not found, using environment-specific config only"
fi

# Prompt for API keys if not provided
if [ -z "$OPENAI_API_KEY" ]; then
    read -sp "Enter your OpenAI API Key (or press Enter to skip): " OPENAI_API_KEY
    echo
fi

if [ -z "$API_KEY_VALUE" ]; then
    # Generate a random API key if not provided
    API_KEY_VALUE="omni-$(openssl rand -hex 16)"
    print_warning "Generated API key: $API_KEY_VALUE"
    print_warning "Please save this API key securely!"
fi

print_status "Deploying CloudFormation stack..."

# Deploy CloudFormation stack
aws cloudformation deploy \
    --template-file deployment/cloudformation/infrastructure.yaml \
    --stack-name "$STACK_NAME" \
    --parameter-overrides \
        Environment="$ENVIRONMENT" \
        OpenAIAPIKey="$OPENAI_API_KEY" \
        APIKeyValue="$API_KEY_VALUE" \
        LambdaMemorySize="$LAMBDA_MEMORY_SIZE" \
        APIThrottleRate="$API_THROTTLE_RATE" \
        APIThrottleBurst="$API_THROTTLE_BURST" \
    --capabilities CAPABILITY_NAMED_IAM \
    --region "$AWS_REGION" \
    --profile "$AWS_PROFILE" \
    --no-fail-on-empty-changeset

if [ $? -eq 0 ]; then
    print_success "CloudFormation stack deployed successfully"
else
    print_error "CloudFormation deployment failed"
    exit 1
fi

# Get Lambda function name from stack outputs
LAMBDA_FUNCTION_NAME=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$AWS_REGION" \
    --profile "$AWS_PROFILE" \
    --query "Stacks[0].Outputs[?OutputKey=='LambdaFunctionArn'].OutputValue" \
    --output text | cut -d':' -f7)

if [ -z "$LAMBDA_FUNCTION_NAME" ]; then
    print_error "Could not retrieve Lambda function name from stack outputs"
    exit 1
fi

print_status "Updating Lambda function code..."

# Update Lambda function code
aws lambda update-function-code \
    --function-name "$LAMBDA_FUNCTION_NAME" \
    --zip-file "fileb://$BUILD_DIR/lambda-deployment.zip" \
    --region "$AWS_REGION" \
    --profile "$AWS_PROFILE" \
    > /dev/null

if [ $? -eq 0 ]; then
    print_success "Lambda function code updated successfully"
else
    print_error "Failed to update Lambda function code"
    exit 1
fi

# Wait for function to be updated
print_status "Waiting for function update to complete..."
aws lambda wait function-updated \
    --function-name "$LAMBDA_FUNCTION_NAME" \
    --region "$AWS_REGION" \
    --profile "$AWS_PROFILE"

# Update Lambda environment variables with API keys from .env
print_status "Updating Lambda environment variables..."

# Build environment variables JSON
ENV_VARS='{"Variables":{'
ENV_VARS+='"ENVIRONMENT":"'$ENVIRONMENT'",'
ENV_VARS+='"AWS_REGION":"'$AWS_REGION'",'
ENV_VARS+='"S3_BUCKET_NAME":"'$S3_BUCKET'",'
ENV_VARS+='"API_KEYS_SECRET_NAME":"omni-llm/api-keys-'$ENVIRONMENT'",'
ENV_VARS+='"LLM_PROVIDERS_SECRET_NAME":"omni-llm/providers-'$ENVIRONMENT'",'
ENV_VARS+='"LOG_LEVEL":"'${LOG_LEVEL:-INFO}'",'
ENV_VARS+='"ENABLE_XRAY_TRACING":"'${ENABLE_XRAY_TRACING:-true}'",'
ENV_VARS+='"ENABLE_METRICS":"'${ENABLE_METRICS:-true}'",'
ENV_VARS+='"METRICS_NAMESPACE":"'${METRICS_NAMESPACE:-OmniLLM}'"'

# Add API keys if provided (for staging environment)
if [ "$ENVIRONMENT" = "staging" ] && [ -n "$OPENAI_API_KEY" ]; then
    ENV_VARS+=', "OPENAI_API_KEY":"'$OPENAI_API_KEY'"'
fi

if [ "$ENVIRONMENT" = "staging" ] && [ -n "$ANTHROPIC_API_KEY" ]; then
    ENV_VARS+=', "ANTHROPIC_API_KEY":"'$ANTHROPIC_API_KEY'"'
fi

if [ "$ENVIRONMENT" = "staging" ] && [ -n "$MISTRAL_API_KEY" ]; then
    ENV_VARS+=', "MISTRAL_API_KEY":"'$MISTRAL_API_KEY'"'
fi

if [ "$ENVIRONMENT" = "staging" ] && [ -n "$COHERE_API_KEY" ]; then
    ENV_VARS+=', "COHERE_API_KEY":"'$COHERE_API_KEY'"'
fi

if [ "$ENVIRONMENT" = "staging" ] && [ -n "$GROQ_API_KEY" ]; then
    ENV_VARS+=', "GROQ_API_KEY":"'$GROQ_API_KEY'"'
fi

if [ -n "$PINECONE_API_KEY" ]; then
    ENV_VARS+=', "PINECONE_API_KEY":"'$PINECONE_API_KEY'"'
fi

if [ -n "$PINECONE_ENVIRONMENT" ]; then
    ENV_VARS+=', "PINECONE_ENVIRONMENT":"'$PINECONE_ENVIRONMENT'"'
fi

ENV_VARS+='}}'

# Update Lambda environment variables
aws lambda update-function-configuration \
    --function-name "$LAMBDA_FUNCTION_NAME" \
    --environment "$ENV_VARS" \
    --region "$AWS_REGION" \
    --profile "$AWS_PROFILE" \
    > /dev/null

if [ $? -eq 0 ]; then
    print_success "Lambda environment variables updated"
else
    print_warning "Failed to update Lambda environment variables (function still works with Secrets Manager)"
fi

# Get stack outputs
print_status "Retrieving deployment information..."

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

S3_BUCKET=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$AWS_REGION" \
    --profile "$AWS_PROFILE" \
    --query "Stacks[0].Outputs[?OutputKey=='S3BucketName'].OutputValue" \
    --output text)

# Test the deployment
print_status "Testing deployment..."

TEST_RESPONSE=$(curl -s \
    -X POST \
    -H "Content-Type: application/json" \
    -H "x-api-key: $API_KEY_VALUE" \
    -d '{
        "prompt": "Hello, world! Please respond with a simple greeting.",
        "fallback_strategy": "balanced",
        "max_tokens": 50
    }' \
    "$API_ENDPOINT/invoke")

if echo "$TEST_RESPONSE" | grep -q '"success": true'; then
    print_success "Deployment test passed!"
else
    print_warning "Deployment test may have failed. Response: $TEST_RESPONSE"
fi

# Clean up build directory
rm -rf "$BUILD_DIR"

# Print deployment summary
echo
echo "=================================================================="
echo "                    DEPLOYMENT SUMMARY"
echo "=================================================================="
echo "Environment:      $ENVIRONMENT"
echo "Stack Name:       $STACK_NAME"
echo "Region:           $AWS_REGION"
echo "API Endpoint:     $API_ENDPOINT"
echo "API Key:          $API_KEY_VALUE"
echo "S3 Bucket:        $S3_BUCKET"
echo "Lambda Function:  $LAMBDA_FUNCTION_NAME"
echo
echo "Test your deployment:"
echo "curl -X POST \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -H \"x-api-key: $API_KEY_VALUE\" \\"
echo "  -d '{\"prompt\": \"Hello!\", \"fallback_strategy\": \"balanced\"}' \\"
echo "  \"$API_ENDPOINT/invoke\""
echo
echo "Environment URLs:"
if [ "$ENVIRONMENT" = "staging" ]; then
    echo "🚧 Staging:    $API_ENDPOINT"
    echo "🚀 Production: https://api-prod.your-domain.com (deploy with: ./deploy.sh prod)"
else
    echo "🚧 Staging:    https://api-staging.your-domain.com"
    echo "🚀 Production: $API_ENDPOINT"
fi
echo
echo "=================================================================="

print_success "Deployment completed successfully!"