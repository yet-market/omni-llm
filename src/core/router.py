"""
Omni-LLM Request Router
======================

Central router for processing requests and coordinating between providers.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from .exceptions import ProviderError, ConfigurationError
from ..models.architecture import RequestSchema, ResponseSchema, LLMProvider
from ..providers.openai_provider import OpenAIProvider
from ..utils.config import Config

logger = logging.getLogger(__name__)


class RequestRouter:
    """
    Central router for processing LLM requests.
    
    Routes requests to appropriate providers and handles response coordination.
    """
    
    def __init__(self, config: Config):
        """
        Initialize the request router.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self._providers = {}
        self._initialize_providers()
    
    def _initialize_providers(self) -> None:
        """Initialize available LLM providers."""
        try:
            # Initialize OpenAI provider
            if self.config.openai_api_key:
                self._providers[LLMProvider.OPENAI] = OpenAIProvider(self.config)
                logger.info("OpenAI provider initialized")
            
            # TODO: Initialize other providers as they are implemented
            # self._providers[LLMProvider.ANTHROPIC] = AnthropicProvider(self.config)
            # self._providers[LLMProvider.AWS_BEDROCK] = BedrockProvider(self.config)
            # etc.
            
        except Exception as e:
            logger.error(f"Error initializing providers: {e}")
            raise ConfigurationError(f"Provider initialization failed: {e}")
    
    def process_request(self, request: RequestSchema, request_id: str) -> Dict[str, Any]:
        """
        Process an incoming request and route to appropriate provider.
        
        Args:
            request: Validated request schema
            request_id: Unique request identifier
        
        Returns:
            Response dictionary
        
        Raises:
            ProviderError: If provider processing fails
        """
        start_time = datetime.utcnow()
        
        logger.info(f"Processing request {request_id} with provider {request.model_provider}")
        
        try:
            # Get provider
            provider = self._get_provider(request.model_provider)
            
            # Process request through provider
            response_data = provider.process_request(request, request_id)
            
            # Calculate execution time
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Build response
            response = {
                "success": True,
                "response": {
                    "content": response_data.get("content", ""),
                    "role": "assistant",
                    "finish_reason": response_data.get("finish_reason", "stop")
                },
                "metadata": {
                    "model_used": request.model_name,
                    "provider": request.model_provider.value,
                    "usage": response_data.get("usage", {}),
                    "execution_time": execution_time,
                    "request_id": request_id
                },
                "error": None
            }
            
            # Add structured data if present
            if "structured_data" in response_data:
                response["structured_data"] = response_data["structured_data"]
            
            # Add RAG context if present
            if "rag_context" in response_data:
                response["rag_context"] = response_data["rag_context"]
            
            # Add tool calls if present
            if "tool_calls" in response_data:
                response["tool_calls"] = response_data["tool_calls"]
            
            logger.info(f"Request {request_id} processed successfully in {execution_time:.2f}s")
            
            return response
            
        except ProviderError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error processing request {request_id}: {e}")
            raise ProviderError(
                f"Request processing failed: {str(e)}",
                provider=request.model_provider.value,
                model=request.model_name
            )
    
    def _get_provider(self, provider_type: LLMProvider):
        """
        Get provider instance for the specified type.
        
        Args:
            provider_type: The provider type
        
        Returns:
            Provider instance
        
        Raises:
            ProviderError: If provider is not available
        """
        if provider_type not in self._providers:
            available_providers = list(self._providers.keys())
            raise ProviderError(
                f"Provider '{provider_type.value}' is not available. "
                f"Available providers: {[p.value for p in available_providers]}",
                provider=provider_type.value
            )
        
        return self._providers[provider_type]
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on all providers.
        
        Returns:
            Health check results
        """
        results = {
            "healthy": True,
            "providers": {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        for provider_type, provider in self._providers.items():
            try:
                provider_health = provider.health_check()
                results["providers"][provider_type.value] = provider_health
                
                if not provider_health.get("healthy", False):
                    results["healthy"] = False
                    
            except Exception as e:
                logger.error(f"Health check failed for {provider_type.value}: {e}")
                results["providers"][provider_type.value] = {
                    "healthy": False,
                    "error": str(e)
                }
                results["healthy"] = False
        
        return results