"""
OpenAI Provider Implementation
=============================

Provider implementation for OpenAI GPT models.
"""

import logging
from typing import Dict, Any, Optional
import openai
from openai import OpenAI

from .base_provider import BaseProvider
from ..core.exceptions import ProviderError, ConfigurationError
from ..models.architecture import RequestSchema

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseProvider):
    """OpenAI provider implementation."""
    
    def __init__(self, config):
        """
        Initialize OpenAI provider.
        
        Args:
            config: Configuration object
        """
        super().__init__(config)
        
        # Get provider configuration
        provider_config = config.get_provider_config('openai')
        api_key = provider_config.get('api_key')
        
        if not api_key:
            raise ConfigurationError("OpenAI API key not configured")
        
        # Initialize OpenAI client
        self.client = OpenAI(
            api_key=api_key,
            timeout=provider_config.get('timeout', 300),
            max_retries=provider_config.get('max_retries', 3)
        )
        
        logger.info("OpenAI provider initialized successfully")
    
    def process_request(self, request: RequestSchema, request_id: str) -> Dict[str, Any]:
        """
        Process request through OpenAI API.
        
        Args:
            request: Validated request schema
            request_id: Request identifier
        
        Returns:
            Response data dictionary
        """
        try:
            # Build OpenAI API request
            api_request = self._build_api_request(request)
            
            logger.info(f"Calling OpenAI API for request {request_id}")
            
            # Make API call
            if request.stream:
                return self._process_streaming_request(api_request, request_id)
            else:
                return self._process_standard_request(api_request, request_id)
                
        except openai.APIError as e:
            logger.error(f"OpenAI API error for request {request_id}: {e}")
            raise ProviderError(
                f"OpenAI API error: {str(e)}",
                provider="openai",
                model=request.model_name,
                status_code=getattr(e, 'status_code', 502)
            )
        except Exception as e:
            logger.error(f"Unexpected error in OpenAI provider for request {request_id}: {e}")
            raise ProviderError(
                f"OpenAI provider error: {str(e)}",
                provider="openai",
                model=request.model_name
            )
    
    def _build_api_request(self, request: RequestSchema) -> Dict[str, Any]:
        """
        Build OpenAI API request from our request schema.
        
        Args:
            request: Request schema
        
        Returns:
            OpenAI API request dictionary
        """
        # Build messages
        messages = []
        
        # Add system prompt if provided
        if request.system_prompt:
            messages.append({
                "role": "system",
                "content": request.system_prompt
            })
        
        # Add user prompt
        messages.append({
            "role": "user",
            "content": request.prompt
        })
        
        # Build API request
        api_request = {
            "model": request.model_name,
            "messages": messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "top_p": request.top_p,
            "stream": request.stream
        }
        
        # Add structured output if requested
        if request.structured_output_enabled and request.structured_output_schema:
            if hasattr(self.client.chat.completions, 'with_structured_output'):
                # Use OpenAI's structured output if available
                api_request["response_format"] = {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "response",
                        "schema": request.structured_output_schema
                    }
                }
            else:
                # Fallback to JSON mode
                api_request["response_format"] = {"type": "json_object"}
                # Add instruction to return JSON
                api_request["messages"][-1]["content"] += "\n\nPlease respond with valid JSON only."
        
        return api_request
    
    def _process_standard_request(self, api_request: Dict[str, Any], request_id: str) -> Dict[str, Any]:
        """
        Process standard (non-streaming) request.
        
        Args:
            api_request: OpenAI API request
            request_id: Request identifier
        
        Returns:
            Response data
        """
        # Make API call
        response = self.client.chat.completions.create(**api_request)
        
        # Extract response data
        choice = response.choices[0]
        message = choice.message
        
        # Build response
        response_data = {
            "content": message.content,
            "finish_reason": choice.finish_reason,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
                "cost_usd": self._calculate_cost(
                    response.usage.prompt_tokens,
                    response.usage.completion_tokens,
                    api_request["model"]
                )
            }
        }
        
        # Parse structured output if requested
        if api_request.get("response_format", {}).get("type") in ["json_object", "json_schema"]:
            try:
                import json
                response_data["structured_data"] = json.loads(message.content)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse JSON response for request {request_id}")
        
        return response_data
    
    def _process_streaming_request(self, api_request: Dict[str, Any], request_id: str) -> Dict[str, Any]:
        """
        Process streaming request.
        
        Args:
            api_request: OpenAI API request
            request_id: Request identifier
        
        Returns:
            Response data
        """
        # For now, convert streaming to non-streaming
        # TODO: Implement proper streaming support
        api_request["stream"] = False
        return self._process_standard_request(api_request, request_id)
    
    def _calculate_cost(self, prompt_tokens: int, completion_tokens: int, model: str) -> float:
        """
        Calculate estimated cost for the request.
        
        Args:
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
            model: Model name
        
        Returns:
            Estimated cost in USD
        """
        # OpenAI pricing (per 1M tokens) - updated as of 2024
        pricing = {
            "gpt-4": {"input": 30.0, "output": 60.0},
            "gpt-4-turbo": {"input": 10.0, "output": 30.0},
            "gpt-4o": {"input": 5.0, "output": 15.0},
            "gpt-4o-mini": {"input": 0.15, "output": 0.6},
            "gpt-3.5-turbo": {"input": 1.5, "output": 2.0},
            "gpt-3.5-turbo-16k": {"input": 3.0, "output": 4.0}
        }
        
        # Get pricing for model (default to gpt-4 if not found)
        model_pricing = pricing.get(model, pricing["gpt-4"])
        
        # Calculate cost
        input_cost = (prompt_tokens / 1_000_000) * model_pricing["input"]
        output_cost = (completion_tokens / 1_000_000) * model_pricing["output"]
        
        return round(input_cost + output_cost, 6)
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check for OpenAI provider.
        
        Returns:
            Health check results
        """
        try:
            # Make a simple API call to test connectivity
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1
            )
            
            return {
                "healthy": True,
                "provider": "openai",
                "models_available": ["gpt-4", "gpt-4-turbo", "gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"],
                "api_accessible": True
            }
            
        except Exception as e:
            logger.error(f"OpenAI health check failed: {e}")
            return {
                "healthy": False,
                "provider": "openai",
                "error": str(e),
                "api_accessible": False
            }