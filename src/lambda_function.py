"""
Omni-LLM Lambda Function Handler
===============================

Main AWS Lambda function handler for the Universal AI Gateway.
Provides unified access to multiple LLM providers through a single API.
"""

import json
import logging
import os
import traceback
from typing import Dict, Any, Optional
from datetime import datetime

import boto3
from botocore.exceptions import ClientError

from .core.router import RequestRouter
from .core.validators import validate_request
from .core.exceptions import OmniLLMError, ValidationError
from .utils.logger import setup_logger
from .utils.config import Config
from .models.architecture import RequestSchema, ResponseSchema

# Setup logging
logger = setup_logger(__name__)

# Initialize configuration
config = Config()

# Initialize request router
router = RequestRouter(config)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda function handler for Omni-LLM requests.
    
    Args:
        event: Lambda event containing API Gateway request
        context: Lambda context object
    
    Returns:
        API Gateway response with CORS headers
    """
    request_id = context.aws_request_id if context else "local"
    start_time = datetime.utcnow()
    
    logger.info(f"Processing request {request_id}")
    
    try:
        # Extract request details
        http_method = event.get('httpMethod', 'POST')
        path = event.get('path', '/')
        headers = event.get('headers', {})
        body = event.get('body', '{}')
        
        # Log request details (without sensitive data)
        logger.info(f"Method: {http_method}, Path: {path}")
        
        # Handle CORS preflight
        if http_method == 'OPTIONS':
            return create_cors_response(200, {"message": "CORS preflight successful"})
        
        # Validate API key
        api_key = headers.get('x-api-key') or headers.get('X-API-Key')
        if not validate_api_key(api_key):
            logger.warning(f"Invalid API key for request {request_id}")
            return create_cors_response(401, {"error": "Invalid or missing API key"})
        
        # Parse request body
        try:
            if isinstance(body, str):
                request_data = json.loads(body) if body else {}
            else:
                request_data = body
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in request body: {e}")
            return create_cors_response(400, {"error": "Invalid JSON in request body"})
        
        # Validate request
        try:
            validated_request = validate_request(request_data)
        except ValidationError as e:
            logger.error(f"Request validation failed: {e}")
            return create_cors_response(400, {"error": str(e)})
        
        # Route and process request
        try:
            response = router.process_request(validated_request, request_id)
            
            # Calculate execution time
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            response['metadata']['execution_time'] = execution_time
            response['metadata']['request_id'] = request_id
            
            logger.info(f"Request {request_id} completed in {execution_time:.2f}s")
            
            return create_cors_response(200, response)
            
        except OmniLLMError as e:
            logger.error(f"OmniLLM error for request {request_id}: {e}")
            error_response = {
                "success": False,
                "error": {
                    "code": e.error_code,
                    "message": str(e),
                    "request_id": request_id
                }
            }
            return create_cors_response(e.status_code, error_response)
        
    except Exception as e:
        logger.error(f"Unexpected error for request {request_id}: {e}")
        logger.error(traceback.format_exc())
        
        error_response = {
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "Internal server error",
                "request_id": request_id
            }
        }
        return create_cors_response(500, error_response)


def validate_api_key(api_key: Optional[str]) -> bool:
    """
    Validate API key against configured keys or AWS Secrets Manager.
    
    Args:
        api_key: The API key to validate
    
    Returns:
        True if valid, False otherwise
    """
    if not api_key:
        return False
    
    # Get valid API keys from environment or Secrets Manager
    valid_keys = get_valid_api_keys()
    
    return api_key in valid_keys


def get_valid_api_keys() -> set:
    """
    Get valid API keys from environment or AWS Secrets Manager.
    
    Returns:
        Set of valid API keys
    """
    # Try environment variable first (for development)
    env_keys = os.getenv('OMNI_LLM_API_KEYS', '')
    if env_keys:
        return set(key.strip() for key in env_keys.split(',') if key.strip())
    
    # Try AWS Secrets Manager
    try:
        secrets_client = boto3.client('secretsmanager', region_name=config.aws_region)
        secret_name = config.api_keys_secret_name
        
        response = secrets_client.get_secret_value(SecretId=secret_name)
        secret_data = json.loads(response['SecretString'])
        
        # Expect format: {"api_keys": ["key1", "key2", ...]}
        return set(secret_data.get('api_keys', []))
        
    except ClientError as e:
        logger.warning(f"Could not retrieve API keys from Secrets Manager: {e}")
        return set()
    except Exception as e:
        logger.error(f"Error getting API keys: {e}")
        return set()


def create_cors_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create API Gateway response with CORS headers.
    
    Args:
        status_code: HTTP status code
        body: Response body
    
    Returns:
        API Gateway response
    """
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,x-api-key',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
            'Access-Control-Max-Age': '86400'
        },
        'body': json.dumps(body, default=str)
    }


# For local development/testing
if __name__ == "__main__":
    # Local development server using FastAPI
    import uvicorn
    from fastapi import FastAPI, Request, HTTPException, Security, APIRouter
    from fastapi.security import APIKeyHeader
    from fastapi.middleware.cors import CORSMiddleware
    
    app = FastAPI(
        title="Omni-LLM Local Development Server",
        description="Universal AI Lambda Gateway - Local Development",
        version="1.0.0"
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # API Key security
    api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)
    
    def get_api_key(api_key: str = Security(api_key_header)):
        if not validate_api_key(api_key):
            raise HTTPException(status_code=401, detail="Invalid API key")
        return api_key
    
    @app.post("/invoke")
    async def invoke_local(request: Request, api_key: str = Security(get_api_key)):
        """Local development endpoint for testing."""
        body = await request.body()
        
        # Create mock Lambda event
        event = {
            'httpMethod': 'POST',
            'path': '/invoke',
            'headers': dict(request.headers),
            'body': body.decode('utf-8') if body else '{}'
        }
        
        # Create mock Lambda context
        class MockContext:
            aws_request_id = "local-dev"
        
        # Process through Lambda handler
        response = lambda_handler(event, MockContext())
        
        # Extract status and body
        status_code = response['statusCode']
        response_body = json.loads(response['body'])
        
        if status_code != 200:
            raise HTTPException(status_code=status_code, detail=response_body)
        
        return response_body
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "service": "omni-llm",
            "version": "1.0.0",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    # Set development API key if not set
    if not os.getenv('OMNI_LLM_API_KEYS'):
        os.environ['OMNI_LLM_API_KEYS'] = 'dev-key-12345'
        logger.info("Using development API key: dev-key-12345")
    
    logger.info("Starting local development server on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)