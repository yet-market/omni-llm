#!/usr/bin/env python3
"""
Comprehensive API Testing Script for Omni-LLM Gateway
====================================================

Tests all API endpoints and use cases to ensure the deployment is working correctly.
"""

import json
import requests
import time
import sys
from typing import Dict, Any, List
from dataclasses import dataclass

@dataclass
class TestResult:
    name: str
    passed: bool
    response_code: int
    response_time: float
    response_data: Dict[str, Any]
    error_message: str = ""

class OmniLLMAPITester:
    def __init__(self, api_endpoint: str, api_key: str):
        self.api_endpoint = api_endpoint.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'x-api-key': api_key
        })
        self.results: List[TestResult] = []

    def run_test(self, name: str, method: str, endpoint: str, payload: Dict[str, Any] = None, 
                 headers: Dict[str, str] = None, expect_status: int = 200) -> TestResult:
        """Run a single API test."""
        print(f"\n🧪 Testing: {name}")
        print(f"   Endpoint: {method} {endpoint}")
        
        url = f"{self.api_endpoint}{endpoint}"
        test_headers = self.session.headers.copy()
        if headers:
            test_headers.update(headers)
        
        start_time = time.time()
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, headers=test_headers, timeout=30)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=payload, headers=test_headers, timeout=30)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response_time = time.time() - start_time
            
            try:
                response_data = response.json()
            except:
                response_data = {"raw_response": response.text}
            
            passed = response.status_code == expect_status
            
            result = TestResult(
                name=name,
                passed=passed,
                response_code=response.status_code,
                response_time=response_time,
                response_data=response_data,
                error_message="" if passed else f"Expected status {expect_status}, got {response.status_code}"
            )
            
            if passed:
                print(f"   ✅ PASSED ({response.status_code}) - {response_time:.2f}s")
            else:
                print(f"   ❌ FAILED ({response.status_code}) - {response_time:.2f}s")
                print(f"   Error: {result.error_message}")
            
            if response_data and not passed:
                print(f"   Response: {json.dumps(response_data, indent=2)[:500]}...")
            
        except Exception as e:
            response_time = time.time() - start_time
            result = TestResult(
                name=name,
                passed=False,
                response_code=0,
                response_time=response_time,
                response_data={},
                error_message=str(e)
            )
            print(f"   ❌ FAILED - Exception: {str(e)}")
        
        self.results.append(result)
        return result

    def test_health_check(self):
        """Test health check endpoint."""
        return self.run_test(
            name="Health Check",
            method="GET",
            endpoint="/health",
            headers={'x-api-key': ''}  # Health check should not require API key
        )

    def test_basic_chat_completion(self):
        """Test basic chat completion."""
        payload = {
            "prompt": "Hello! Please respond with a simple greeting.",
            "max_tokens": 50
        }
        return self.run_test(
            name="Basic Chat Completion",
            method="POST",
            endpoint="/invoke",
            payload=payload
        )

    def test_specific_model_request(self):
        """Test request with specific model."""
        payload = {
            "prompt": "What is artificial intelligence?",
            "model_name": "gpt-4o-mini",
            "max_tokens": 100
        }
        return self.run_test(
            name="Specific Model Request (GPT-4o-mini)",
            method="POST",
            endpoint="/invoke",
            payload=payload
        )

    def test_anthropic_model_request(self):
        """Test request with Anthropic model."""
        payload = {
            "prompt": "Explain quantum computing in simple terms.",
            "model_name": "claude-3-5-haiku-20241022",
            "max_tokens": 150
        }
        return self.run_test(
            name="Anthropic Model Request (Claude Haiku)",
            method="POST",
            endpoint="/invoke",
            payload=payload
        )

    def test_fallback_strategy_fast(self):
        """Test fast fallback strategy."""
        payload = {
            "prompt": "Generate a short poem about AI.",
            "fallback_strategy": "fast",
            "max_tokens": 100
        }
        return self.run_test(
            name="Fast Fallback Strategy",
            method="POST",
            endpoint="/invoke",
            payload=payload
        )

    def test_fallback_strategy_balanced(self):
        """Test balanced fallback strategy."""
        payload = {
            "prompt": "Summarize the benefits of renewable energy.",
            "fallback_strategy": "balanced",
            "max_tokens": 150
        }
        return self.run_test(
            name="Balanced Fallback Strategy",
            method="POST",
            endpoint="/invoke",
            payload=payload
        )

    def test_fallback_strategy_quality(self):
        """Test quality fallback strategy."""
        payload = {
            "prompt": "Write a technical explanation of machine learning algorithms.",
            "fallback_strategy": "quality",
            "max_tokens": 200
        }
        return self.run_test(
            name="Quality Fallback Strategy",
            method="POST",
            endpoint="/invoke",
            payload=payload
        )

    def test_streaming_request(self):
        """Test streaming response."""
        payload = {
            "prompt": "Count from 1 to 10 with explanations.",
            "stream": True,
            "max_tokens": 200
        }
        return self.run_test(
            name="Streaming Response",
            method="POST",
            endpoint="/invoke",
            payload=payload
        )

    def test_temperature_control(self):
        """Test temperature parameter."""
        payload = {
            "prompt": "Generate a creative story about space exploration.",
            "temperature": 0.8,
            "max_tokens": 150
        }
        return self.run_test(
            name="Temperature Control (0.8)",
            method="POST",
            endpoint="/invoke",
            payload=payload
        )

    def test_system_message(self):
        """Test system message functionality."""
        payload = {
            "prompt": "What is your role?",
            "system_message": "You are a helpful AI assistant specialized in science and technology.",
            "max_tokens": 100
        }
        return self.run_test(
            name="System Message",
            method="POST",
            endpoint="/invoke",
            payload=payload
        )

    def test_invalid_model(self):
        """Test handling of invalid model name."""
        payload = {
            "prompt": "This should trigger fallback.",
            "model_name": "invalid-model-name",
            "max_tokens": 50
        }
        return self.run_test(
            name="Invalid Model Fallback",
            method="POST",
            endpoint="/invoke",
            payload=payload
        )

    def test_large_context(self):
        """Test large context handling."""
        large_prompt = "Analyze this text: " + "Lorem ipsum dolor sit amet. " * 100
        payload = {
            "prompt": large_prompt,
            "max_tokens": 100
        }
        return self.run_test(
            name="Large Context Handling",
            method="POST",
            endpoint="/invoke",
            payload=payload
        )

    def test_unauthorized_request(self):
        """Test request without API key."""
        payload = {
            "prompt": "This should fail.",
            "max_tokens": 50
        }
        return self.run_test(
            name="Unauthorized Request (No API Key)",
            method="POST",
            endpoint="/invoke",
            payload=payload,
            headers={'x-api-key': ''},
            expect_status=403
        )

    def test_invalid_api_key(self):
        """Test request with invalid API key."""
        payload = {
            "prompt": "This should fail.",
            "max_tokens": 50
        }
        return self.run_test(
            name="Invalid API Key",
            method="POST",
            endpoint="/invoke",
            payload=payload,
            headers={'x-api-key': 'invalid-key'},
            expect_status=403
        )

    def test_malformed_request(self):
        """Test malformed JSON request."""
        return self.run_test(
            name="Malformed Request",
            method="POST",
            endpoint="/invoke",
            payload={"invalid": "request without required fields"},
            expect_status=400
        )

    def test_cors_preflight(self):
        """Test CORS preflight request."""
        return self.run_test(
            name="CORS Preflight",
            method="OPTIONS",
            endpoint="/invoke",
            headers={'Origin': 'https://example.com'},
            expect_status=200
        )

    def run_all_tests(self):
        """Run all test cases."""
        print("🚀 Starting Comprehensive API Testing")
        print(f"API Endpoint: {self.api_endpoint}")
        print(f"API Key: {self.api_key[:10]}...")
        print("=" * 80)

        # Core functionality tests
        self.test_health_check()
        self.test_basic_chat_completion()
        self.test_specific_model_request()
        self.test_anthropic_model_request()
        
        # Fallback strategy tests
        self.test_fallback_strategy_fast()
        self.test_fallback_strategy_balanced()
        self.test_fallback_strategy_quality()
        
        # Advanced feature tests
        self.test_streaming_request()
        self.test_temperature_control()
        self.test_system_message()
        
        # Edge case tests
        self.test_invalid_model()
        self.test_large_context()
        
        # Security tests
        self.test_unauthorized_request()
        self.test_invalid_api_key()
        
        # Error handling tests
        self.test_malformed_request()
        
        # CORS test
        self.test_cors_preflight()

    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        passed_tests = [r for r in self.results if r.passed]
        failed_tests = [r for r in self.results if not r.passed]
        
        print(f"Total Tests: {len(self.results)}")
        print(f"✅ Passed: {len(passed_tests)}")
        print(f"❌ Failed: {len(failed_tests)}")
        print(f"Success Rate: {len(passed_tests)/len(self.results)*100:.1f}%")
        
        if failed_tests:
            print("\n❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"   • {test.name}: {test.error_message}")
        
        avg_response_time = sum(r.response_time for r in self.results) / len(self.results)
        print(f"\n⏱️  Average Response Time: {avg_response_time:.2f}s")
        
        print("\n🎯 CRITICAL ENDPOINTS:")
        health_result = next((r for r in self.results if "Health" in r.name), None)
        basic_chat_result = next((r for r in self.results if "Basic Chat" in r.name), None)
        
        if health_result:
            status = "✅ UP" if health_result.passed else "❌ DOWN"
            print(f"   Health Check: {status}")
        
        if basic_chat_result:
            status = "✅ WORKING" if basic_chat_result.passed else "❌ BROKEN"
            print(f"   Basic Chat: {status}")
        
        print("\n" + "=" * 80)
        
        return len(failed_tests) == 0

def main():
    """Main function to run API tests."""
    if len(sys.argv) != 3:
        print("Usage: python test_api.py <API_ENDPOINT> <API_KEY>")
        print("Example: python test_api.py https://your-api-gateway-url.amazonaws.com/staging your-api-key")
        print("")
        print("Get your API endpoint and key from your deployment output:")
        print("./deployment/scripts/deploy-simple.sh staging")
        sys.exit(1)
    
    api_endpoint = sys.argv[1]
    api_key = sys.argv[2]
    
    tester = OmniLLMAPITester(api_endpoint, api_key)
    tester.run_all_tests()
    
    success = tester.print_summary()
    
    if success:
        print("🎉 ALL TESTS PASSED! Your API is working correctly.")
        sys.exit(0)
    else:
        print("💥 SOME TESTS FAILED! Please check the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()