"""
Omni-LLM Configuration Management
================================

Configuration management using environment variables and AWS services.
"""

import os
import logging
from typing import Optional, Dict, Any
import boto3
import json
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class Config:
    """
    Configuration management class.
    
    Loads configuration from environment variables and AWS services.
    """
    
    def __init__(self):
        """Initialize configuration from environment variables."""
        # AWS Configuration
        self.aws_region = os.getenv('AWS_REGION', 'eu-west-2')
        self.aws_profile = os.getenv('AWS_PROFILE', 'yet')
        
        # API Key Management
        self.api_keys_secret_name = os.getenv('API_KEYS_SECRET_NAME', 'omni-llm/api-keys')
        
        # LLM Provider API Keys (loaded from environment or Secrets Manager)
        self.openai_api_key = self._get_secret('OPENAI_API_KEY')
        self.anthropic_api_key = self._get_secret('ANTHROPIC_API_KEY')
        self.mistral_api_key = self._get_secret('MISTRAL_API_KEY')
        self.cohere_api_key = self._get_secret('COHERE_API_KEY')
        self.groq_api_key = self._get_secret('GROQ_API_KEY')
        
        # Google Cloud Configuration
        self.google_project_id = self._get_secret('GOOGLE_PROJECT_ID')
        self.google_location = os.getenv('GOOGLE_LOCATION', 'us-central1')
        
        # Vector Store Configuration
        self.pinecone_api_key = self._get_secret('PINECONE_API_KEY')
        self.pinecone_environment = os.getenv('PINECONE_ENVIRONMENT', 'us-east1-gcp')
        
        # S3 Configuration for RAG
        self.s3_bucket_name = os.getenv('S3_BUCKET_NAME')
        self.s3_region = os.getenv('S3_REGION', self.aws_region)
        self.s3_prefix = os.getenv('S3_PREFIX', 'documents/')
        
        # Application Configuration
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
        self.cache_ttl = int(os.getenv('CACHE_TTL', '3600'))
        self.max_tokens_default = int(os.getenv('MAX_TOKENS_DEFAULT', '4096'))
        self.temperature_default = float(os.getenv('TEMPERATURE_DEFAULT', '0.7'))
        
        # Security Configuration
        self.rate_limit_per_minute = int(os.getenv('RATE_LIMIT_PER_MINUTE', '60'))
        self.rate_limit_per_hour = int(os.getenv('RATE_LIMIT_PER_HOUR', '1000'))
        self.max_request_size_mb = int(os.getenv('MAX_REQUEST_SIZE_MB', '10'))
        
        # Performance Configuration
        self.connection_pool_size = int(os.getenv('CONNECTION_POOL_SIZE', '20'))
        self.request_timeout = int(os.getenv('REQUEST_TIMEOUT', '300'))
        
        # Monitoring Configuration
        self.enable_xray_tracing = os.getenv('ENABLE_XRAY_TRACING', 'true').lower() == 'true'
        self.enable_metrics = os.getenv('ENABLE_METRICS', 'true').lower() == 'true'
        self.metrics_namespace = os.getenv('METRICS_NAMESPACE', 'OmniLLM')
        
    def _get_secret(self, env_var_name: str, secret_key: Optional[str] = None) -> Optional[str]:
        """
        Get secret value from environment variable or AWS Secrets Manager.
        
        Args:
            env_var_name: Environment variable name
            secret_key: Key within the secret (if different from env_var_name)
        
        Returns:
            Secret value or None if not found
        """
        # Try environment variable first
        value = os.getenv(env_var_name)
        if value:
            return value
        
        # Try AWS Secrets Manager if in AWS environment
        if self._is_aws_environment():
            try:
                return self._get_secret_from_aws(secret_key or env_var_name.lower().replace('_', '-'))
            except Exception as e:
                logger.debug(f"Could not retrieve {env_var_name} from Secrets Manager: {e}")
        
        return None
    
    def _is_aws_environment(self) -> bool:
        """Check if running in AWS environment."""
        return (
            os.getenv('AWS_LAMBDA_FUNCTION_NAME') is not None or
            os.getenv('AWS_EXECUTION_ENV') is not None
        )
    
    def _get_secret_from_aws(self, secret_name: str) -> Optional[str]:
        """
        Get secret from AWS Secrets Manager.
        
        Args:
            secret_name: Name of the secret
        
        Returns:
            Secret value or None if not found
        """
        try:
            secrets_client = boto3.client('secretsmanager', region_name=self.aws_region)
            response = secrets_client.get_secret_value(SecretId=f"omni-llm/{secret_name}")
            
            # Try to parse as JSON first
            try:
                secret_data = json.loads(response['SecretString'])
                return secret_data.get(secret_name)
            except json.JSONDecodeError:
                # Return as plain string
                return response['SecretString']
                
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'ResourceNotFoundException':
                logger.debug(f"Secret {secret_name} not found in Secrets Manager")
            else:
                logger.warning(f"Error retrieving secret {secret_name}: {e}")
            return None
    
    def get_provider_config(self, provider: str) -> Dict[str, Any]:
        """
        Get configuration for a specific provider.
        
        Args:
            provider: Provider name
        
        Returns:
            Provider configuration dictionary
        """
        configs = {
            'openai': {
                'api_key': self.openai_api_key,
                'timeout': self.request_timeout,
                'max_retries': 3
            },
            'anthropic': {
                'api_key': self.anthropic_api_key,
                'timeout': self.request_timeout,
                'max_retries': 3
            },
            'mistral': {
                'api_key': self.mistral_api_key,
                'timeout': self.request_timeout,
                'max_retries': 3
            },
            'cohere': {
                'api_key': self.cohere_api_key,
                'timeout': self.request_timeout,
                'max_retries': 3
            },
            'groq': {
                'api_key': self.groq_api_key,
                'timeout': self.request_timeout,
                'max_retries': 3
            },
            'bedrock': {
                'region': self.aws_region,
                'timeout': self.request_timeout
            },
            'vertexai': {
                'project_id': self.google_project_id,
                'location': self.google_location,
                'timeout': self.request_timeout
            }
        }
        
        return configs.get(provider, {})
    
    def validate_config(self) -> Dict[str, bool]:
        """
        Validate configuration completeness.
        
        Returns:
            Dictionary of validation results
        """
        validations = {
            'aws_region_set': bool(self.aws_region),
            'at_least_one_provider': any([
                self.openai_api_key,
                self.anthropic_api_key,
                self.mistral_api_key,
                self.cohere_api_key,
                self.groq_api_key,
                self._is_aws_environment()  # Bedrock available in AWS
            ]),
            'log_level_valid': self.log_level in ['DEBUG', 'INFO', 'WARNING', 'ERROR'],
            'cache_ttl_positive': self.cache_ttl > 0,
            'max_tokens_positive': self.max_tokens_default > 0,
            'temperature_valid': 0.0 <= self.temperature_default <= 2.0,
            'rate_limits_positive': self.rate_limit_per_minute > 0 and self.rate_limit_per_hour > 0
        }
        
        return validations