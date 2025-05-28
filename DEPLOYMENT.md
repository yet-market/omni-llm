# Omni-LLM Deployment Guide

## Environment Variables & API Keys

### 🔧 How Environment Variables Work

Omni-LLM supports **two ways** to manage API keys and configuration:

#### 1. **Development Mode** (.env file)
- Add your API keys to `.env` file
- Keys are loaded as Lambda environment variables during deployment
- Perfect for development and testing
- **Never commit .env to git!**

#### 2. **Production Mode** (AWS Secrets Manager)
- API keys stored securely in AWS Secrets Manager
- Lambda function retrieves keys at runtime
- Recommended for production environments
- More secure and auditable

### 🚀 Quick Setup

#### Option A: Interactive Setup (Recommended)
```bash
# Set up your .env file interactively
./scripts/setup-env.sh

# Deploy with your API keys
./deployment/scripts/deploy.sh dev
```

#### Option B: Manual Setup
```bash
# 1. Copy template
cp ENV_TEMPLATE.env .env

# 2. Edit .env and add your API keys
nano .env  # or your preferred editor

# 3. Deploy
./deployment/scripts/deploy.sh dev
```

### 📝 Environment Variable Priority

The system checks for API keys in this order:

1. **Environment variables** (from .env file)
2. **AWS Secrets Manager** (production)
3. **Prompt during deployment** (fallback)

### 🔐 Security Features

#### Development Environment
- API keys loaded from `.env` file
- Keys set as Lambda environment variables
- Easy to test and iterate

#### Production Environment
- API keys stored in AWS Secrets Manager
- Lambda retrieves keys securely at runtime
- No keys visible in Lambda console
- Automatic key rotation support

### 📋 Supported Environment Variables

#### Required for Basic Functionality
```bash
# At least one LLM provider
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
MISTRAL_API_KEY=...
COHERE_API_KEY=...
GROQ_API_KEY=gsk_...
```

#### Optional Configuration
```bash
# Vector Stores
PINECONE_API_KEY=...
PINECONE_ENVIRONMENT=us-east1-gcp

# AWS Configuration
S3_BUCKET_NAME=your-bucket
AWS_REGION=eu-west-2

# Application Settings
LOG_LEVEL=INFO
RATE_LIMIT_PER_MINUTE=60
MAX_TOKENS_DEFAULT=4096
```

### 🎯 Deployment Examples

#### Deploy with OpenAI only
```bash
# In .env file
OPENAI_API_KEY=sk-your-openai-key

# Deploy
./deployment/scripts/deploy.sh dev
```

#### Deploy with multiple providers
```bash
# In .env file
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
GROQ_API_KEY=gsk-your-groq-key

# Deploy
./deployment/scripts/deploy.sh dev
```

#### Deploy to production with Secrets Manager
```bash
# Store keys in Secrets Manager first
aws secretsmanager create-secret \
  --name "omni-llm/providers-prod" \
  --secret-string '{"openai-api-key":"sk-...","anthropic-api-key":"sk-ant-..."}' \
  --region eu-west-2 \
  --profile yet

# Deploy without .env file
./deployment/scripts/deploy.sh prod
```

### 🔍 How to Check Your Configuration

#### Test locally
```bash
./test_deployment.py
```

#### Test deployed function
```bash
# The deploy script provides a test command at the end
curl -X POST \
  -H "Content-Type: application/json" \
  -H "x-api-key: YOUR-API-KEY" \
  -d '{"prompt": "Hello!", "model_provider": "openai", "model_name": "gpt-3.5-turbo"}' \
  "https://your-api-gateway-url/invoke"
```

### 📂 File Structure

```
omni-llm/
├── .env                     # Your API keys (NOT in git)
├── ENV_TEMPLATE.env         # Template with empty values
├── scripts/
│   ├── setup-env.sh         # Interactive environment setup
│   ├── setup-dev.sh         # Development environment setup
│   └── start-dev.sh         # Start local development server
└── deployment/
    └── scripts/
        └── deploy.sh         # Deployment script (reads .env)
```

### ⚠️ Security Best Practices

1. **Never commit .env to git** - it's in .gitignore
2. **Use Secrets Manager for production** - more secure
3. **Rotate API keys regularly** - especially for production
4. **Monitor usage** - set up CloudWatch alerts
5. **Use least privilege** - IAM roles have minimal permissions

### 🐛 Troubleshooting

#### "No provider available" error
- Check that at least one API key is configured
- Verify the API key format is correct
- Test the API key directly with the provider

#### Environment variables not loaded
- Check that .env file exists and has correct format
- Verify deployment script shows "Environment variables loaded from .env"
- Check Lambda function configuration in AWS console

#### API key validation fails
- Verify the API key is correct and active
- Check provider-specific key format requirements
- Test with a simple request first

## Summary

Yes, you can **add all your API keys to .env and they will be automatically added as Lambda environment variables** during deployment! The deployment script:

1. ✅ **Reads your .env file**
2. ✅ **Loads all environment variables** 
3. ✅ **Sets them as Lambda environment variables**
4. ✅ **Works for development environments**
5. ✅ **Falls back to Secrets Manager for production**

This gives you the best of both worlds - easy development with .env files and secure production with Secrets Manager.