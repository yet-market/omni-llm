"""
LangChain Universal Provider Implementation
==========================================

Single provider implementation using LangChain with built-in fallback support
for all major LLM providers.
"""

import logging
import time
from typing import Dict, Any, List, Optional, Type
from datetime import datetime

# LangChain imports
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.output_parsers import JsonOutputParser, PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.exceptions import LangChainException

# Provider-specific imports
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_mistralai import ChatMistralAI
from langchain_cohere import ChatCohere
from langchain_groq import ChatGroq

# AWS and Google imports (conditional)
try:
    from langchain_aws import ChatBedrock
except ImportError:
    ChatBedrock = None

try:
    from langchain_google_vertexai import ChatVertexAI
except ImportError:
    ChatVertexAI = None

from ..core.exceptions import ProviderError, ConfigurationError
from ..models.architecture import (
    RequestSchema, LLMProvider, FallbackStrategy, 
    ProviderAttempt, ModelConfiguration
)
from ..utils.config import Config

logger = logging.getLogger(__name__)


class LangChainProvider:
    """
    Universal LangChain provider with automatic fallback support.
    
    This provider uses LangChain's built-in capabilities to handle multiple
    LLM providers with intelligent fallback and cost optimization.
    """
    
    def __init__(self, config: Config):
        """
        Initialize LangChain provider with all available models.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.providers: Dict[LLMProvider, Dict[str, BaseChatModel]] = {}
        self.model_catalog: Dict[str, ModelConfiguration] = {}
        self._initialize_providers()
        self._load_model_catalog()
    
    def _initialize_providers(self) -> None:
        """Initialize all available LangChain providers."""
        try:
            # OpenAI
            if self.config.openai_api_key:
                self.providers[LLMProvider.OPENAI] = self._init_openai_models()
                logger.info("OpenAI provider initialized")
            
            # Anthropic
            if self.config.anthropic_api_key:
                self.providers[LLMProvider.ANTHROPIC] = self._init_anthropic_models()
                logger.info("Anthropic provider initialized")
            
            # Groq
            if self.config.groq_api_key:
                self.providers[LLMProvider.GROQ] = self._init_groq_models()
                logger.info("Groq provider initialized")
            
            # Mistral AI
            if self.config.mistral_api_key:
                self.providers[LLMProvider.MISTRAL_AI] = self._init_mistral_models()
                logger.info("Mistral AI provider initialized")
            
            # Cohere
            if self.config.cohere_api_key:
                self.providers[LLMProvider.COHERE] = self._init_cohere_models()
                logger.info("Cohere provider initialized")
            
            # AWS Bedrock (if in AWS environment)
            if ChatBedrock and self._is_aws_environment():
                self.providers[LLMProvider.AWS_BEDROCK] = self._init_bedrock_models()
                logger.info("AWS Bedrock provider initialized")
            
            # Google Vertex AI
            if ChatVertexAI and self.config.google_project_id:
                self.providers[LLMProvider.GOOGLE_VERTEX_AI] = self._init_vertexai_models()
                logger.info("Google Vertex AI provider initialized")
            
            if not self.providers:
                raise ConfigurationError("No LLM providers configured. Please check your API keys.")
                
        except Exception as e:
            logger.error(f"Error initializing providers: {e}")
            raise ConfigurationError(f"Provider initialization failed: {e}")
    
    def _init_openai_models(self) -> Dict[str, BaseChatModel]:
        """Initialize OpenAI models."""
        models = {}
        model_names = ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"]
        
        for model_name in model_names:
            try:
                models[model_name] = ChatOpenAI(
                    model=model_name,
                    api_key=self.config.openai_api_key,
                    timeout=self.config.request_timeout,
                    max_retries=3
                )
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI model {model_name}: {e}")
        
        return models
    
    def _init_anthropic_models(self) -> Dict[str, BaseChatModel]:
        """Initialize Anthropic models."""
        models = {}
        model_names = [
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307"
        ]
        
        for model_name in model_names:
            try:
                models[model_name] = ChatAnthropic(
                    model=model_name,
                    api_key=self.config.anthropic_api_key,
                    timeout=self.config.request_timeout,
                    max_retries=3
                )
            except Exception as e:
                logger.warning(f"Failed to initialize Anthropic model {model_name}: {e}")
        
        return models
    
    def _init_groq_models(self) -> Dict[str, BaseChatModel]:
        """Initialize Groq models."""
        models = {}
        model_names = [
            "llama-3.1-70b-versatile",
            "llama-3.1-8b-instant",
            "llama-3.2-90b-text-preview",
            "mixtral-8x7b-32768",
            "gemma-7b-it"
        ]
        
        for model_name in model_names:
            try:
                models[model_name] = ChatGroq(
                    model=model_name,
                    api_key=self.config.groq_api_key,
                    timeout=self.config.request_timeout,
                    max_retries=3
                )
            except Exception as e:
                logger.warning(f"Failed to initialize Groq model {model_name}: {e}")
        
        return models
    
    def _init_mistral_models(self) -> Dict[str, BaseChatModel]:
        """Initialize Mistral AI models."""
        models = {}
        model_names = [
            "mistral-large-latest",
            "mistral-medium-latest", 
            "mistral-small-latest",
            "open-mixtral-8x7b"
        ]
        
        for model_name in model_names:
            try:
                models[model_name] = ChatMistralAI(
                    model=model_name,
                    api_key=self.config.mistral_api_key,
                    timeout=self.config.request_timeout,
                    max_retries=3
                )
            except Exception as e:
                logger.warning(f"Failed to initialize Mistral model {model_name}: {e}")
        
        return models
    
    def _init_cohere_models(self) -> Dict[str, BaseChatModel]:
        """Initialize Cohere models."""
        models = {}
        model_names = ["command-r-plus", "command-r", "command", "command-light"]
        
        for model_name in model_names:
            try:
                models[model_name] = ChatCohere(
                    model=model_name,
                    cohere_api_key=self.config.cohere_api_key,
                    timeout=self.config.request_timeout,
                    max_retries=3
                )
            except Exception as e:
                logger.warning(f"Failed to initialize Cohere model {model_name}: {e}")
        
        return models
    
    def _init_bedrock_models(self) -> Dict[str, BaseChatModel]:
        """Initialize AWS Bedrock models."""
        models = {}
        model_names = [
            "anthropic.claude-3-5-sonnet-20241022-v2:0",
            "anthropic.claude-3-5-haiku-20241022-v1:0",
            "anthropic.claude-3-opus-20240229-v1:0",
            "amazon.titan-text-premier-v1:0",
            "meta.llama3-70b-instruct-v1:0"
        ]
        
        for model_name in model_names:
            try:
                models[model_name] = ChatBedrock(
                    model_id=model_name,
                    region_name=self.config.aws_region,
                    model_kwargs={
                        "max_tokens": 4096,
                        "temperature": 0.7
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to initialize Bedrock model {model_name}: {e}")
        
        return models
    
    def _init_vertexai_models(self) -> Dict[str, BaseChatModel]:
        """Initialize Google Vertex AI models."""
        models = {}
        model_names = ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-1.0-pro"]
        
        for model_name in model_names:
            try:
                models[model_name] = ChatVertexAI(
                    model=model_name,
                    project=self.config.google_project_id,
                    location=self.config.google_location,
                    timeout=self.config.request_timeout,
                    max_retries=3
                )
            except Exception as e:
                logger.warning(f"Failed to initialize Vertex AI model {model_name}: {e}")
        
        return models
    
    def _load_model_catalog(self) -> None:
        """Load model catalog for cost calculation and routing."""
        from ..models.architecture import get_langchain_model_catalog
        
        catalog = get_langchain_model_catalog()
        for model_config in catalog:
            self.model_catalog[model_config.name] = model_config
    
    def _is_aws_environment(self) -> bool:
        """Check if running in AWS environment."""
        import os
        return (
            os.getenv('AWS_LAMBDA_FUNCTION_NAME') is not None or
            os.getenv('AWS_EXECUTION_ENV') is not None
        )
    
    def process_request(self, request: RequestSchema, request_id: str) -> Dict[str, Any]:
        """
        Process request with automatic fallback support.
        
        Args:
            request: Validated request schema
            request_id: Request identifier
        
        Returns:
            Response data dictionary
        """
        start_time = time.time()
        attempts: List[ProviderAttempt] = []
        
        # Get provider order for fallback
        provider_order = self._get_provider_order(request)
        
        last_error = None
        
        for i, (provider, model_name) in enumerate(provider_order):
            if i >= request.max_fallback_attempts:
                break
                
            attempt_start = time.time()
            
            try:
                logger.info(f"Attempting request {request_id} with {provider.value}:{model_name}")
                
                # Get the model
                model = self._get_model(provider, model_name)
                
                # Process the request
                result = self._process_with_model(model, request, request_id)
                
                # Calculate metrics
                attempt_time = time.time() - attempt_start
                cost = self._calculate_cost(result, model_name)
                
                # Record successful attempt
                attempts.append(ProviderAttempt(
                    provider=provider,
                    model=model_name,
                    success=True,
                    error=None,
                    latency=attempt_time,
                    cost=cost
                ))
                
                # Build successful response
                response = {
                    "content": result["content"],
                    "provider_used": provider,
                    "model_used": model_name,
                    "fallback_attempts": attempts,
                    "total_tokens": result.get("total_tokens", 0),
                    "prompt_tokens": result.get("prompt_tokens", 0),
                    "completion_tokens": result.get("completion_tokens", 0),
                    "total_cost": cost,
                    "total_latency": time.time() - start_time,
                    "provider_latency": attempt_time
                }
                
                # Add structured data if present
                if "structured_data" in result:
                    response["structured_data"] = result["structured_data"]
                
                logger.info(f"Request {request_id} succeeded with {provider.value}:{model_name}")
                return response
                
            except Exception as e:
                attempt_time = time.time() - attempt_start
                error_msg = str(e)
                last_error = e
                
                logger.warning(f"Request {request_id} failed with {provider.value}:{model_name}: {error_msg}")
                
                # Record failed attempt
                attempts.append(ProviderAttempt(
                    provider=provider,
                    model=model_name,
                    success=False,
                    error=error_msg,
                    latency=attempt_time,
                    cost=0.0
                ))
                
                # Continue to next provider if fallback is enabled
                if not request.enable_fallback:
                    break
        
        # All attempts failed
        total_time = time.time() - start_time
        logger.error(f"Request {request_id} failed after {len(attempts)} attempts in {total_time:.2f}s")
        
        raise ProviderError(
            f"All provider attempts failed. Last error: {str(last_error)}",
            provider="fallback",
            details={
                "attempts": len(attempts),
                "total_time": total_time,
                "fallback_attempts": [attempt.dict() for attempt in attempts]
            }
        )
    
    def _get_provider_order(self, request: RequestSchema) -> List[tuple]:
        """
        Get ordered list of (provider, model) pairs for fallback.
        
        Args:
            request: Request schema
        
        Returns:
            List of (provider, model) tuples in priority order
        """
        # If specific model requested, try that first
        if request.model_name:
            provider = self._find_provider_for_model(request.model_name)
            if provider:
                provider_order = [(provider, request.model_name)]
            else:
                raise ProviderError(f"Model '{request.model_name}' not available in any configured provider")
        else:
            provider_order = []
        
        # Add fallback providers based on strategy
        if request.enable_fallback:
            fallback_providers = self._get_fallback_providers(request)
            provider_order.extend(fallback_providers)
        
        return provider_order[:request.max_fallback_attempts]
    
    def _find_provider_for_model(self, model_name: str) -> Optional[LLMProvider]:
        """Find which provider has the specified model."""
        for provider, models in self.providers.items():
            if model_name in models:
                return provider
        return None
    
    def _get_fallback_providers(self, request: RequestSchema) -> List[tuple]:
        """Get fallback provider list based on strategy."""
        fallback_list = []
        
        # Use provider preference if specified
        if request.provider_preference:
            providers_to_try = request.provider_preference
        else:
            # Default order based on strategy
            if request.fallback_strategy == FallbackStrategy.COST_OPTIMIZED:
                providers_to_try = [LLMProvider.GROQ, LLMProvider.OPENAI, LLMProvider.ANTHROPIC]
            elif request.fallback_strategy == FallbackStrategy.PERFORMANCE_OPTIMIZED:
                providers_to_try = [LLMProvider.GROQ, LLMProvider.OPENAI, LLMProvider.ANTHROPIC]
            else:  # PRIORITY_ORDER
                providers_to_try = [LLMProvider.OPENAI, LLMProvider.ANTHROPIC, LLMProvider.GROQ, LLMProvider.MISTRAL_AI, LLMProvider.COHERE]
        
        # Build fallback list with available models
        for provider in providers_to_try:
            if provider in self.providers:
                models = list(self.providers[provider].keys())
                if models:
                    # Get best model for this provider
                    best_model = self._get_best_model_for_provider(provider, request.fallback_strategy)
                    if best_model:
                        fallback_list.append((provider, best_model))
        
        return fallback_list
    
    def _get_best_model_for_provider(self, provider: LLMProvider, strategy: FallbackStrategy) -> Optional[str]:
        """Get the best model for a provider based on strategy."""
        available_models = list(self.providers[provider].keys())
        
        if not available_models:
            return None
        
        # Filter models by strategy
        if strategy == FallbackStrategy.COST_OPTIMIZED:
            # Find cheapest model
            cheapest_model = None
            min_cost = float('inf')
            
            for model_name in available_models:
                model_config = self.model_catalog.get(model_name)
                if model_config:
                    total_cost = model_config.cost_per_1m_input_tokens + model_config.cost_per_1m_output_tokens
                    if total_cost < min_cost:
                        min_cost = total_cost
                        cheapest_model = model_name
            
            return cheapest_model or available_models[0]
        
        elif strategy == FallbackStrategy.PERFORMANCE_OPTIMIZED:
            # Find fastest model
            for model_name in available_models:
                model_config = self.model_catalog.get(model_name)
                if model_config and model_config.latency_category == "ultra_fast":
                    return model_name
            
            # Fallback to first available
            return available_models[0]
        
        else:  # PRIORITY_ORDER
            # Return highest priority model
            best_model = None
            highest_priority = 0
            
            for model_name in available_models:
                model_config = self.model_catalog.get(model_name)
                if model_config and model_config.priority >= highest_priority:
                    highest_priority = model_config.priority
                    best_model = model_name
            
            return best_model or available_models[0]
    
    def _get_model(self, provider: LLMProvider, model_name: str) -> BaseChatModel:
        """Get model instance for provider and model name."""
        if provider not in self.providers:
            raise ProviderError(f"Provider {provider.value} not configured")
        
        if model_name not in self.providers[provider]:
            raise ProviderError(f"Model {model_name} not available in provider {provider.value}")
        
        return self.providers[provider][model_name]
    
    def _process_with_model(self, model: BaseChatModel, request: RequestSchema, request_id: str) -> Dict[str, Any]:
        """Process request with a specific model."""
        # Build messages
        messages = []
        
        if request.system_prompt:
            messages.append(SystemMessage(content=request.system_prompt))
        
        messages.append(HumanMessage(content=request.prompt))
        
        # Configure model parameters
        model_kwargs = {
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "top_p": request.top_p
        }
        
        if request.top_k:
            model_kwargs["top_k"] = request.top_k
        
        # Create runnable with parameters
        configured_model = model.bind(**model_kwargs)
        
        # Process request
        if request.structured_output_enabled and request.structured_output_schema:
            # Use structured output
            parser = JsonOutputParser()
            chain = configured_model | parser
            
            # Add instruction for JSON output
            json_instruction = f"\n\nPlease respond with valid JSON matching this schema: {request.structured_output_schema}"
            messages[-1].content += json_instruction
            
            response = chain.invoke(messages)
            
            return {
                "content": str(response),
                "structured_data": response,
                "total_tokens": getattr(response, 'usage', {}).get('total_tokens', 0),
                "prompt_tokens": getattr(response, 'usage', {}).get('prompt_tokens', 0),
                "completion_tokens": getattr(response, 'usage', {}).get('completion_tokens', 0)
            }
        else:
            # Standard text response
            response = configured_model.invoke(messages)
            
            return {
                "content": response.content,
                "total_tokens": getattr(response, 'usage', {}).get('total_tokens', 0),
                "prompt_tokens": getattr(response, 'usage', {}).get('prompt_tokens', 0),
                "completion_tokens": getattr(response, 'usage', {}).get('completion_tokens', 0)
            }
    
    def _calculate_cost(self, result: Dict[str, Any], model_name: str) -> float:
        """Calculate cost for the request."""
        model_config = self.model_catalog.get(model_name)
        if not model_config:
            return 0.0
        
        prompt_tokens = result.get("prompt_tokens", 0)
        completion_tokens = result.get("completion_tokens", 0)
        
        input_cost = (prompt_tokens / 1_000_000) * model_config.cost_per_1m_input_tokens
        output_cost = (completion_tokens / 1_000_000) * model_config.cost_per_1m_output_tokens
        
        return round(input_cost + output_cost, 6)
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on all providers."""
        results = {
            "healthy": True,
            "providers": {},
            "total_models": 0,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        for provider, models in self.providers.items():
            try:
                provider_health = {
                    "healthy": True,
                    "models_available": list(models.keys()),
                    "model_count": len(models)
                }
                
                results["providers"][provider.value] = provider_health
                results["total_models"] += len(models)
                
            except Exception as e:
                logger.error(f"Health check failed for {provider.value}: {e}")
                results["providers"][provider.value] = {
                    "healthy": False,
                    "error": str(e),
                    "models_available": [],
                    "model_count": 0
                }
                results["healthy"] = False
        
        return results