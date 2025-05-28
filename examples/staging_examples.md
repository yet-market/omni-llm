# Staging Environment Examples
# ============================

This document provides examples specific to the staging environment for testing and development.

## Environment URLs

- **Staging**: `https://your-staging-api.execute-api.region.amazonaws.com/staging/invoke`
- **Production**: `https://your-production-api.execute-api.region.amazonaws.com/prod/invoke`

## 🚧 Staging Environment Testing

### Basic LangChain Fallback Test

```bash
# Test basic fallback functionality
curl -X POST https://your-staging-api.execute-api.eu-west-2.amazonaws.com/staging/invoke \
  -H "Content-Type: application/json" \
  -H "x-api-key: staging-api-key-12345" \
  -d '{
    "prompt": "Test staging environment with a simple question: What is 2+2?",
    "fallback_strategy": "balanced",
    "enable_fallback": true,
    "max_tokens": 100
  }'
```

### Structured Output Test

```bash
# Test structured output in staging
curl -X POST https://your-staging-api.execute-api.eu-west-2.amazonaws.com/staging/invoke \
  -H "Content-Type: application/json" \
  -H "x-api-key: staging-api-key-12345" \
  -d '{
    "prompt": "Analyze this test data for staging: Sales increased 15% last quarter",
    "fallback_strategy": "quality_optimized",
    "structured_output_enabled": true,
    "structured_output_schema": {
      "metric": "string",
      "change_percentage": "number",
      "time_period": "string",
      "sentiment": "string"
    }
  }'
```

### Cost-Optimized Fallback Chain Test

```bash
# Test cost-optimized chain (perfect for staging)
curl -X POST https://your-staging-api.execute-api.eu-west-2.amazonaws.com/staging/invoke \
  -H "Content-Type: application/json" \
  -H "x-api-key: staging-api-key-12345" \
  -d '{
    "prompt": "Generate a brief test response for staging validation",
    "fallback_strategy": "cost_optimized",
    "enable_fallback": true,
    "max_fallback_attempts": 3
  }'
```

### Performance Testing

```bash
# Test performance-optimized chain (Groq first)
curl -X POST https://your-staging-api.execute-api.eu-west-2.amazonaws.com/staging/invoke \
  -H "Content-Type: application/json" \
  -H "x-api-key: staging-api-key-12345" \
  -d '{
    "prompt": "Quick response needed for staging latency test",
    "fallback_strategy": "performance_optimized",
    "max_tokens": 50
  }'
```

## 🔧 Staging-Specific Features

### Debug Mode Testing

```python
import requests
import json

# Staging API endpoint with debug features
STAGING_URL = "https://your-staging-api.execute-api.eu-west-2.amazonaws.com/staging/invoke"
STAGING_API_KEY = "staging-api-key-12345"

def test_staging_debug():
    """Test staging environment with debug information."""
    
    payload = {
        "prompt": "Test staging environment debug features",
        "fallback_strategy": "balanced",
        "enable_fallback": True,
        "max_tokens": 100,
        # Staging-specific debug options
        "debug_mode": True,
        "include_metadata": True
    }
    
    response = requests.post(
        STAGING_URL,
        headers={
            "Content-Type": "application/json",
            "x-api-key": STAGING_API_KEY
        },
        json=payload
    )
    
    result = response.json()
    
    # Print debug information available in staging
    print("🚧 Staging Debug Info:")
    print(f"Status Code: {response.status_code}")
    print(f"Response Time: {response.elapsed.total_seconds():.2f}s")
    print(f"Success: {result.get('success', False)}")
    
    if 'metadata' in result:
        metadata = result['metadata']
        print(f"Provider Used: {metadata.get('provider', 'unknown')}")
        print(f"Fallback Attempts: {metadata.get('fallback_attempts', 0)}")
        print(f"Total Tokens: {metadata.get('usage', {}).get('total_tokens', 0)}")
        print(f"Cost: ${metadata.get('usage', {}).get('cost_usd', 0):.4f}")
    
    return result

# Run staging test
if __name__ == "__main__":
    test_staging_debug()
```

### Load Testing Script

```python
import asyncio
import aiohttp
import time
from concurrent.futures import ThreadPoolExecutor

async def staging_load_test():
    """Simple load test for staging environment."""
    
    url = "https://your-staging-api.execute-api.eu-west-2.amazonaws.com/staging/invoke"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": "staging-api-key-12345"
    }
    
    payload = {
        "prompt": "Load test prompt",
        "fallback_strategy": "cost_optimized",
        "max_tokens": 50
    }
    
    async with aiohttp.ClientSession() as session:
        start_time = time.time()
        
        # Send 10 concurrent requests (within staging limits)
        tasks = []
        for i in range(10):
            task = session.post(url, headers=headers, json=payload)
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        
        print(f"🚧 Staging Load Test Results:")
        print(f"Total Requests: 10")
        print(f"Total Time: {end_time - start_time:.2f}s")
        print(f"Successful: {sum(1 for r in responses if not isinstance(r, Exception))}")
        print(f"Failed: {sum(1 for r in responses if isinstance(r, Exception))}")

# Run load test
# asyncio.run(staging_load_test())
```

## 🔍 Environment Validation Checklist

### Pre-Production Checklist

```bash
# 1. Test basic functionality
curl -X POST $STAGING_URL/invoke \
  -H "Content-Type: application/json" \
  -H "x-api-key: $STAGING_API_KEY" \
  -d '{"prompt": "Test basic functionality", "fallback_strategy": "balanced"}'

# 2. Test fallback mechanisms
curl -X POST $STAGING_URL/invoke \
  -H "Content-Type: application/json" \
  -H "x-api-key: $STAGING_API_KEY" \
  -d '{"prompt": "Test fallback", "model_name": "invalid-model", "enable_fallback": true}'

# 3. Test structured output
curl -X POST $STAGING_URL/invoke \
  -H "Content-Type: application/json" \
  -H "x-api-key: $STAGING_API_KEY" \
  -d '{
    "prompt": "Extract data: John Doe, age 30, engineer",
    "structured_output_enabled": true,
    "structured_output_schema": {"name": "string", "age": "number", "job": "string"}
  }'

# 4. Test health endpoint
curl -X GET $STAGING_URL/health

# 5. Test error handling
curl -X POST $STAGING_URL/invoke \
  -H "Content-Type: application/json" \
  -H "x-api-key: invalid-key" \
  -d '{"prompt": "This should fail authentication"}'
```

## 📊 Staging Monitoring

### CloudWatch Metrics to Monitor

- **Lambda Duration**: Should be < 30s for most requests
- **API Gateway 4xx/5xx Errors**: Should be < 5%
- **Throttling**: Should not exceed staging limits (100 req/s)
- **Memory Usage**: Monitor for optimization

### Key Logs to Watch

```bash
# View Lambda logs
aws logs tail /aws/lambda/omni-llm-gateway-staging --follow --profile yet --region eu-west-2

# Filter for errors
aws logs filter-log-events \
  --log-group-name /aws/lambda/omni-llm-gateway-staging \
  --filter-pattern "ERROR" \
  --profile yet --region eu-west-2
```

## 🚀 Ready for Production?

After successful staging validation:

1. ✅ All basic functionality tests pass
2. ✅ Fallback mechanisms work correctly  
3. ✅ Structured output generates valid JSON
4. ✅ Performance meets expectations
5. ✅ Error handling behaves properly
6. ✅ No critical errors in logs

**Deploy to production:**
```bash
git checkout master
git merge staging
./deployment/scripts/deploy.sh prod
```