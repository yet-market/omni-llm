#!/bin/bash

# Omni-LLM Environment Setup Script
# ================================
# Helps you set up your .env file with API keys

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

print_status "Setting up .env file for Omni-LLM..."

# Check if .env already exists
if [ -f ".env" ]; then
    read -p "⚠️  .env file already exists. Do you want to overwrite it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_status "Keeping existing .env file. You can edit it manually."
        exit 0
    fi
fi

# Copy template
cp ENV_TEMPLATE.env .env

print_success ".env file created from template"

echo
echo "=================================================================="
echo "           CONFIGURE YOUR API KEYS"
echo "=================================================================="
echo
echo "I'll help you set up your API keys. You can skip any provider"
echo "you don't want to use right now."
echo

# Function to securely read API key
read_api_key() {
    local provider=$1
    local var_name=$2
    local description=$3
    
    echo
    read -sp "Enter your $provider API Key ($description) [press Enter to skip]: " api_key
    echo
    
    if [ -n "$api_key" ]; then
        # Escape special characters for sed
        escaped_key=$(printf '%s\n' "$api_key" | sed 's/[[\.*^$()+?{|]/\\&/g')
        sed -i.bak "s/^${var_name}=.*/${var_name}=${escaped_key}/" .env
        print_success "$provider API key added"
    else
        print_status "$provider API key skipped"
    fi
}

# Configure API keys
read_api_key "OpenAI" "OPENAI_API_KEY" "get from https://platform.openai.com/api-keys"
read_api_key "Anthropic" "ANTHROPIC_API_KEY" "get from https://console.anthropic.com/"
read_api_key "Mistral AI" "MISTRAL_API_KEY" "get from https://console.mistral.ai/"
read_api_key "Cohere" "COHERE_API_KEY" "get from https://dashboard.cohere.ai/"
read_api_key "Groq" "GROQ_API_KEY" "get from https://console.groq.com/"

echo
echo "----------------------------------------------------------------"
echo "Optional: Vector Store Configuration"
echo "----------------------------------------------------------------"

read_api_key "Pinecone" "PINECONE_API_KEY" "get from https://app.pinecone.io/"

if grep -q "PINECONE_API_KEY=.\+" .env; then
    echo
    read -p "Enter your Pinecone Environment (e.g., us-east1-gcp) [press Enter for default]: " pinecone_env
    if [ -n "$pinecone_env" ]; then
        sed -i.bak "s/^PINECONE_ENVIRONMENT=.*/PINECONE_ENVIRONMENT=${pinecone_env}/" .env
    fi
fi

echo
echo "----------------------------------------------------------------"
echo "Optional: AWS Configuration"
echo "----------------------------------------------------------------"

read -p "Enter your S3 bucket name for RAG documents [press Enter to skip]: " s3_bucket
if [ -n "$s3_bucket" ]; then
    sed -i.bak "s/^S3_BUCKET_NAME=.*/S3_BUCKET_NAME=${s3_bucket}/" .env
    print_success "S3 bucket configured"
fi

# Clean up backup file
rm -f .env.bak

echo
echo "=================================================================="
echo "           CONFIGURATION COMPLETE"
echo "=================================================================="
echo

# Check what was configured
configured_providers=()
if grep -q "OPENAI_API_KEY=.\+" .env; then
    configured_providers+=("OpenAI")
fi
if grep -q "ANTHROPIC_API_KEY=.\+" .env; then
    configured_providers+=("Anthropic")
fi
if grep -q "MISTRAL_API_KEY=.\+" .env; then
    configured_providers+=("Mistral")
fi
if grep -q "COHERE_API_KEY=.\+" .env; then
    configured_providers+=("Cohere")
fi
if grep -q "GROQ_API_KEY=.\+" .env; then
    configured_providers+=("Groq")
fi

if [ ${#configured_providers[@]} -gt 0 ]; then
    echo "✅ Configured providers: ${configured_providers[*]}"
else
    print_warning "No provider API keys configured. You can add them later by editing .env"
fi

echo
echo "Your .env file is ready! Here's what you can do next:"
echo
echo "1. Test locally:"
echo "   ./scripts/setup-dev.sh"
echo "   ./scripts/start-dev.sh"
echo
echo "2. Deploy to AWS:"
echo "   ./deployment/scripts/deploy.sh dev"
echo
echo "3. Edit .env manually if you want to add more configuration"
echo

print_success "Environment setup complete!"

echo
print_warning "IMPORTANT: Never commit your .env file to git!"
print_warning "Your API keys are now in .env and will be loaded automatically."