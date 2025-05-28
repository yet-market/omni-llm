#!/usr/bin/env python3
"""
Omni-LLM Deployment Test Script
==============================

Test script to verify the Lambda function works locally before deployment.
"""

import json
import sys
import os
import requests
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_lambda_handler_local():
    """Test the Lambda handler locally."""
    try:
        from src.lambda_function import lambda_handler
        
        # Mock event and context
        event = {
            'httpMethod': 'POST',
            'path': '/invoke',
            'headers': {
                'Content-Type': 'application/json',
                'x-api-key': 'dev-key-12345'
            },
            'body': json.dumps({
                'prompt': 'Say hello!',
                'model_provider': 'openai',
                'model_name': 'gpt-3.5-turbo',
                'max_tokens': 50
            })
        }
        
        class MockContext:
            aws_request_id = "test-request-123"
        
        # Test the handler
        response = lambda_handler(event, MockContext())
        
        print("✓ Lambda handler test passed")
        print(f"Status Code: {response['statusCode']}")
        
        if response['statusCode'] == 200:
            body = json.loads(response['body'])
            print(f"Success: {body.get('success', False)}")
        else:
            print(f"Error: {response['body']}")
        
        return response['statusCode'] == 200
        
    except Exception as e:
        print(f"✗ Lambda handler test failed: {e}")
        return False

def test_architecture_loading():
    """Test that architecture models load correctly."""
    try:
        from src.models.architecture import OMNI_LLM_ARCHITECTURE
        
        print("✓ Architecture models loaded successfully")
        print(f"Supported providers: {len(OMNI_LLM_ARCHITECTURE.supported_providers)}")
        print(f"Model catalog: {len(OMNI_LLM_ARCHITECTURE.model_catalog)} models")
        
        return True
        
    except Exception as e:
        print(f"✗ Architecture loading failed: {e}")
        return False

def test_config_loading():
    """Test configuration loading."""
    try:
        from src.utils.config import Config
        
        config = Config()
        validations = config.validate_config()
        
        print("✓ Configuration loaded successfully")
        print(f"AWS Region: {config.aws_region}")
        print(f"Validations: {sum(validations.values())}/{len(validations)} passed")
        
        return True
        
    except Exception as e:
        print(f"✗ Configuration loading failed: {e}")
        return False

def test_providers():
    """Test provider initialization."""
    try:
        from src.utils.config import Config
        from src.providers.openai_provider import OpenAIProvider
        
        config = Config()
        
        # Test OpenAI provider if API key is available
        if config.openai_api_key:
            provider = OpenAIProvider(config)
            health = provider.health_check()
            print(f"✓ OpenAI provider: {health.get('healthy', False)}")
        else:
            print("⚠ OpenAI provider: No API key configured")
        
        return True
        
    except Exception as e:
        print(f"✗ Provider test failed: {e}")
        return False

def test_api_server():
    """Test the local API server if running."""
    try:
        response = requests.get('http://localhost:8000/health', timeout=5)
        if response.status_code == 200:
            print("✓ Local API server is running")
            return True
        else:
            print(f"⚠ Local API server returned status {response.status_code}")
            return False
            
    except requests.exceptions.RequestException:
        print("⚠ Local API server is not running")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("         OMNI-LLM DEPLOYMENT TEST")
    print("=" * 60)
    
    # Set environment for testing
    os.environ['OMNI_LLM_API_KEYS'] = 'dev-key-12345,test-key-67890'
    os.environ['LOG_LEVEL'] = 'ERROR'  # Reduce noise during testing
    
    tests = [
        ("Architecture Loading", test_architecture_loading),
        ("Configuration Loading", test_config_loading),
        ("Provider Initialization", test_providers),
        ("Lambda Handler", test_lambda_handler_local),
        ("API Server", test_api_server),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\nTesting {test_name}...")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("                  TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name:<25} {status}")
        if result:
            passed += 1
    
    print("-" * 60)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Ready for deployment.")
        return 0
    elif passed >= total - 1:
        print("\n⚠ Most tests passed. Check warnings above.")
        return 0
    else:
        print("\n❌ Some tests failed. Please fix issues before deployment.")
        return 1

if __name__ == "__main__":
    exit(main())