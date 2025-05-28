"""
Omni-LLM Request Router - LangChain Based
==========================================

Central router for processing requests using the universal LangChain provider
with automatic fallback support.
"""

import logging
from typing import Dict, Any
from datetime import datetime

from .exceptions import ProviderError, ConfigurationError
from ..models.architecture import RequestSchema
from ..providers.langchain_provider import LangChainProvider
from ..utils.config import Config

logger = logging.getLogger(__name__)


class RequestRouter:
    """
    Central router for processing LLM requests using LangChain provider.
    
    Routes all requests through the universal LangChain provider which handles
    multiple providers internally with automatic fallback.
    """
    
    def __init__(self, config: Config):
        """
        Initialize the request router.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.provider = None
        self._initialize_provider()
    
    def _initialize_provider(self) -> None:
        """Initialize the LangChain universal provider."""
        try:
            self.provider = LangChainProvider(self.config)
            logger.info("LangChain universal provider initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing LangChain provider: {e}")
            raise ConfigurationError(f"Provider initialization failed: {e}")
    
    def process_request(self, request: RequestSchema, request_id: str) -> Dict[str, Any]:
        """
        Process an incoming request through the LangChain provider.
        
        Args:
            request: Validated request schema
            request_id: Unique request identifier
        
        Returns:
            Response dictionary
        
        Raises:
            ProviderError: If request processing fails
        """
        start_time = datetime.utcnow()
        
        logger.info(f"Processing request {request_id} through LangChain provider")
        
        try:
            # Process request through LangChain provider
            response_data = self.provider.process_request(request, request_id)
            
            # Build final response
            response = {
                "success": True,
                "response": {
                    "content": response_data.get("content", ""),
                    "role": "assistant",
                    "finish_reason": "stop"
                },
                "metadata": {
                    "model_used": response_data.get("model_used", "unknown"),
                    "provider": response_data.get("provider_used", "unknown").value if hasattr(response_data.get("provider_used"), 'value') else str(response_data.get("provider_used", "unknown")),
                    "usage": {
                        "prompt_tokens": response_data.get("prompt_tokens", 0),
                        "completion_tokens": response_data.get("completion_tokens", 0),
                        "total_tokens": response_data.get("total_tokens", 0),
                        "cost_usd": response_data.get("total_cost", 0.0)
                    },
                    "execution_time": response_data.get("total_latency", 0.0),
                    "provider_latency": response_data.get("provider_latency", 0.0),
                    "request_id": request_id,
                    "fallback_attempts": len(response_data.get("fallback_attempts", [])),
                    "providers_tried": [
                        {
                            "provider": attempt.provider.value if hasattr(attempt.provider, 'value') else str(attempt.provider),
                            "model": attempt.model,
                            "success": attempt.success,
                            "latency": attempt.latency,
                            "cost": attempt.cost,
                            "error": attempt.error
                        }
                        for attempt in response_data.get("fallback_attempts", [])
                    ]
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
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            response["metadata"]["total_execution_time"] = execution_time
            
            logger.info(f"Request {request_id} processed successfully in {execution_time:.2f}s")
            logger.info(f"Used provider: {response_data.get('provider_used')}, model: {response_data.get('model_used')}")
            
            if response_data.get("fallback_attempts"):
                logger.info(f"Fallback attempts: {len(response_data['fallback_attempts'])}")
            
            return response
            
        except ProviderError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error processing request {request_id}: {e}")
            raise ProviderError(
                f"Request processing failed: {str(e)}",
                provider="langchain",
                details={"request_id": request_id}
            )
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on the LangChain provider.
        
        Returns:
            Health check results
        """
        try:
            if not self.provider:
                return {
                    "healthy": False,
                    "error": "LangChain provider not initialized",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            provider_health = self.provider.health_check()
            
            # Enhance with router-level information
            result = {
                "healthy": provider_health.get("healthy", False),
                "router": "langchain_universal",
                "provider_details": provider_health,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "healthy": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }