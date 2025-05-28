"""
LangChain Universal Provider with Native Fallback Runnable
==========================================================

Implementation using LangChain's built-in with_fallbacks() runnable for
automatic provider fallback support.
"""

import logging
import time
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

# LangChain core imports
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnableWithFallbacks
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
from ..models.architecture import RequestSchema, LLMProvider, FallbackStrategy
from ..utils.config import Config

logger = logging.getLogger(__name__)


class LangChainProvider:
    """
    Universal LangChain provider using native fallback runnables.
    
    This provider leverages LangChain's built-in with_fallbacks() method
    to create robust runnable chains with automatic provider fallback.
    """
    
    def __init__(self, config: Config):
        """
        Initialize LangChain provider with fallback runnables.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.models: Dict[str, BaseChatModel] = {}
        self.fallback_chains: Dict[str, RunnableWithFallbacks] = {}
        self._initialize_models()
        self._create_fallback_chains()
    
    def _initialize_models(self) -> None:
        """Initialize all available LangChain models."""
        try:
            # OpenAI models (Latest 2025)
            if self.config.openai_api_key:
                self.models.update({
                    "gpt-4o": ChatOpenAI(
                        model="gpt-4o-2024-11-20",  # Latest stable with 16K output
                        api_key=self.config.openai_api_key,
                        max_retries=0,  # Let fallback handle retries
                        timeout=60
                    ),
                    "gpt-4o-mini": ChatOpenAI(
                        model="gpt-4o-mini-2024-12-17",  # Real-time audio capabilities
                        api_key=self.config.openai_api_key,
                        max_retries=0,
                        timeout=60
                    ),
                    "o3-mini": ChatOpenAI(
                        model="o3-mini-2025-01-31",  # New reasoning model
                        api_key=self.config.openai_api_key,
                        max_retries=0,
                        timeout=90  # Reasoning models may need more time
                    ),
                    "gpt-4o-realtime": ChatOpenAI(
                        model="gpt-4o-realtime-preview-2024-12-17",  # Real-time audio
                        api_key=self.config.openai_api_key,
                        max_retries=0,
                        timeout=60
                    )
                })
                logger.info("OpenAI models initialized")
            
            # Anthropic models (Latest 2025)
            if self.config.anthropic_api_key:
                self.models.update({
                    "claude-sonnet-4": ChatAnthropic(
                        model="claude-sonnet-4-20250514",  # Latest Sonnet 4
                        api_key=self.config.anthropic_api_key,
                        max_retries=0,
                        timeout=90  # More time for advanced reasoning
                    ),
                    "claude-opus-4": ChatAnthropic(
                        model="claude-opus-4-20250514",  # Latest Opus 4
                        api_key=self.config.anthropic_api_key,
                        max_retries=0,
                        timeout=120  # Most advanced model needs more time
                    ),
                    "claude-3-5-sonnet": ChatAnthropic(
                        model="claude-3-5-sonnet-20241022",  # Latest 3.5 Sonnet
                        api_key=self.config.anthropic_api_key,
                        max_retries=0,
                        timeout=60
                    ),
                    "claude-3-5-haiku": ChatAnthropic(
                        model="claude-3-5-haiku-20241022",  # Latest 3.5 Haiku
                        api_key=self.config.anthropic_api_key,
                        max_retries=0,
                        timeout=60
                    )
                })
                logger.info("Anthropic models initialized")
            
            # Groq models (Latest 2025 - ultra-fast)
            if self.config.groq_api_key:
                self.models.update({
                    "llama-3.3-70b-versatile": ChatGroq(
                        model="llama-3.3-70b-versatile",  # Latest Llama 3.3 70B
                        api_key=self.config.groq_api_key,
                        max_retries=0,
                        timeout=30
                    ),
                    "llama-3.3-70b-specdec": ChatGroq(
                        model="llama-3.3-70b-specdec",  # Speculative decoding version
                        api_key=self.config.groq_api_key,
                        max_retries=0,
                        timeout=20  # Even faster with speculative decoding
                    ),
                    "llama-3.1-8b-instant": ChatGroq(
                        model="llama-3.1-8b-instant",  # Fast fallback
                        api_key=self.config.groq_api_key,
                        max_retries=0,
                        timeout=15
                    ),
                    "mixtral-8x7b-32768": ChatGroq(
                        model="mixtral-8x7b-32768",  # Reliable fallback
                        api_key=self.config.groq_api_key,
                        max_retries=0,
                        timeout=30
                    )
                })
                logger.info("Groq models initialized")
            
            # Mistral AI models (Latest 2025)
            if self.config.mistral_api_key:
                self.models.update({
                    "codestral-25.01": ChatMistralAI(
                        model="codestral-25.01",  # Latest coding model
                        api_key=self.config.mistral_api_key,
                        max_retries=0,
                        timeout=60
                    ),
                    "devstral": ChatMistralAI(
                        model="devstral",  # Development-optimized model
                        api_key=self.config.mistral_api_key,
                        max_retries=0,
                        timeout=60
                    ),
                    "mistral-large-latest": ChatMistralAI(
                        model="mistral-large-latest",  # Latest large model
                        api_key=self.config.mistral_api_key,
                        max_retries=0,
                        timeout=60
                    ),
                    "mistral-small-latest": ChatMistralAI(
                        model="mistral-small-latest",  # Efficient fallback
                        api_key=self.config.mistral_api_key,
                        max_retries=0,
                        timeout=60
                    )
                })
                logger.info("Mistral AI models initialized")
            
            # Cohere models
            if self.config.cohere_api_key:
                self.models.update({
                    "command-r-plus": ChatCohere(
                        model="command-r-plus",
                        cohere_api_key=self.config.cohere_api_key,
                        max_retries=0,
                        timeout=60
                    ),
                    "command-r": ChatCohere(
                        model="command-r",
                        cohere_api_key=self.config.cohere_api_key,
                        max_retries=0,
                        timeout=60
                    )
                })
                logger.info("Cohere models initialized")
            
            # AWS Bedrock (if in AWS environment)
            if ChatBedrock and self._is_aws_environment():
                self.models.update({
                    "anthropic.claude-3-5-sonnet-20241022-v2:0": ChatBedrock(
                        model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
                        region_name=self.config.aws_region
                    ),
                    "anthropic.claude-3-5-haiku-20241022-v1:0": ChatBedrock(
                        model_id="anthropic.claude-3-5-haiku-20241022-v1:0",
                        region_name=self.config.aws_region
                    )
                })
                logger.info("AWS Bedrock models initialized")
            
            # Google Vertex AI (Latest 2025)
            if ChatVertexAI and self.config.google_project_id:
                self.models.update({
                    "gemini-2.5-flash": ChatVertexAI(
                        model="gemini-2.5-flash",  # Latest Gemini 2.5 Flash
                        project=self.config.google_project_id,
                        location=self.config.google_location,
                        max_retries=0,
                        timeout=60
                    ),
                    "gemini-2.0-flash": ChatVertexAI(
                        model="gemini-2.0-flash",  # Gemini 2.0 Flash
                        project=self.config.google_project_id,
                        location=self.config.google_location,
                        max_retries=0,
                        timeout=60
                    ),
                    "gemini-2.0-flash-lite": ChatVertexAI(
                        model="gemini-2.0-flash-lite",  # Lightweight version
                        project=self.config.google_project_id,
                        location=self.config.google_location,
                        max_retries=0,
                        timeout=45
                    ),
                    "gemini-1.5-pro": ChatVertexAI(
                        model="gemini-1.5-pro",  # Reliable fallback
                        project=self.config.google_project_id,
                        location=self.config.google_location,
                        max_retries=0,
                        timeout=60
                    )
                })
                logger.info("Google Vertex AI models initialized")
            
            if not self.models:
                raise ConfigurationError("No LLM models configured. Please check your API keys.")
            
            logger.info(f"Total models initialized: {len(self.models)}")
                
        except Exception as e:
            logger.error(f"Error initializing models: {e}")
            raise ConfigurationError(f"Model initialization failed: {e}")
    
    def _create_fallback_chains(self) -> None:
        """Create pre-configured fallback chains using LangChain's with_fallbacks()."""
        
        # Cost-optimized chain (cheapest first)
        cost_optimized_models = self._get_models_by_cost()
        if cost_optimized_models:
            primary = cost_optimized_models[0]
            fallbacks = cost_optimized_models[1:3]  # Top 3 cheapest
            if fallbacks:
                self.fallback_chains["cost_optimized"] = primary.with_fallbacks(fallbacks)
            else:
                self.fallback_chains["cost_optimized"] = primary
        
        # Performance-optimized chain (fastest first)
        performance_models = self._get_models_by_performance()
        if performance_models:
            primary = performance_models[0]
            fallbacks = performance_models[1:3]  # Top 3 fastest
            if fallbacks:
                self.fallback_chains["performance_optimized"] = primary.with_fallbacks(fallbacks)
            else:
                self.fallback_chains["performance_optimized"] = primary
        
        # Quality-optimized chain (best models first)
        quality_models = self._get_models_by_quality()
        if quality_models:
            primary = quality_models[0]
            fallbacks = quality_models[1:3]  # Top 3 quality
            if fallbacks:
                self.fallback_chains["quality_optimized"] = primary.with_fallbacks(fallbacks)
            else:
                self.fallback_chains["quality_optimized"] = primary
        
        # Balanced chain (good balance of cost/performance/quality)
        balanced_models = self._get_balanced_models()
        if balanced_models:
            primary = balanced_models[0]
            fallbacks = balanced_models[1:4]  # Top 4 balanced
            if fallbacks:
                self.fallback_chains["balanced"] = primary.with_fallbacks(fallbacks)
            else:
                self.fallback_chains["balanced"] = primary
        
        # Default chain (priority order)
        default_models = self._get_default_priority_models()
        if default_models:
            primary = default_models[0]
            fallbacks = default_models[1:5]  # Top 5 overall
            if fallbacks:
                self.fallback_chains["priority_order"] = primary.with_fallbacks(fallbacks)
            else:
                self.fallback_chains["priority_order"] = primary
        
        logger.info(f"Created {len(self.fallback_chains)} fallback chains")
    
    def _get_models_by_cost(self) -> List[BaseChatModel]:
        """Get models ordered by cost (cheapest first)."""
        cost_priorities = [
            "llama-3.1-8b-instant",      # Groq - Ultra cheap
            "llama-3.3-70b-specdec",     # Groq - Fast & cheap (2025)
            "llama-3.3-70b-versatile",   # Groq - Cheap (2025)
            "gpt-4o-mini",               # OpenAI - Cost effective
            "claude-3-5-haiku",          # Anthropic - Fast & cheap
            "gemini-2.0-flash-lite",     # Google - Lightweight (2025)
            "mistral-small-latest",      # Mistral - Small
            "gemini-2.0-flash",          # Google - Flash (2025)
        ]
        
        return [self.models[name] for name in cost_priorities if name in self.models]
    
    def _get_models_by_performance(self) -> List[BaseChatModel]:
        """Get models ordered by performance (fastest first)."""
        performance_priorities = [
            "llama-3.3-70b-specdec",     # Groq - Ultra fast with speculative decoding (2025)
            "llama-3.1-8b-instant",      # Groq - Ultra fast
            "llama-3.3-70b-versatile",   # Groq - Very fast (2025)
            "gpt-4o-mini",               # OpenAI - Fast
            "claude-3-5-haiku",          # Anthropic - Fast
            "gemini-2.0-flash-lite",     # Google - Lightning fast (2025)
            "gemini-2.0-flash",          # Google - Fast (2025)
            "mixtral-8x7b-32768",        # Groq - Fast
        ]
        
        return [self.models[name] for name in performance_priorities if name in self.models]
    
    def _get_models_by_quality(self) -> List[BaseChatModel]:
        """Get models ordered by quality (best first)."""
        quality_priorities = [
            "claude-opus-4",             # Anthropic - Highest quality (2025)
            "claude-sonnet-4",           # Anthropic - Excellent quality (2025)
            "o3-mini",                   # OpenAI - Advanced reasoning (2025)
            "gpt-4o",                    # OpenAI - Top quality
            "claude-3-5-sonnet",         # Anthropic - Excellent
            "gemini-2.5-flash",          # Google - Latest Pro (2025)
            "codestral-25.01",           # Mistral - Latest coding (2025)
            "gpt-4o-mini",               # OpenAI - Very good
            "mistral-large-latest",      # Mistral - Large
            "llama-3.3-70b-versatile",   # Groq - Large (2025)
        ]
        
        return [self.models[name] for name in quality_priorities if name in self.models]
    
    def _get_balanced_models(self) -> List[BaseChatModel]:
        """Get models with good balance of cost/performance/quality."""
        balanced_priorities = [
            "gpt-4o-mini",               # OpenAI - Great balance
            "claude-3-5-haiku",          # Anthropic - Fast & good
            "llama-3.3-70b-versatile",   # Groq - Fast & capable (2025)
            "gemini-2.0-flash",          # Google - Balanced (2025)
            "claude-3-5-sonnet",         # Anthropic - Quality & speed
            "devstral",                  # Mistral - Development optimized (2025)
            "mistral-small-latest",      # Mistral - Efficient
        ]
        
        return [self.models[name] for name in balanced_priorities if name in self.models]
    
    def _get_default_priority_models(self) -> List[BaseChatModel]:
        """Get models in default priority order."""
        default_priorities = [
            "gpt-4o-mini",               # OpenAI - Best default
            "claude-3-5-haiku",          # Anthropic - Fast backup
            "llama-3.3-70b-versatile",   # Groq - Fast & capable (2025)
            "gemini-2.0-flash",          # Google - Fast alternative (2025)
            "claude-3-5-sonnet",         # Anthropic - Quality fallback
            "devstral",                  # Mistral - Development optimized (2025)
            "mistral-small-latest",      # Mistral - Backup
        ]
        
        return [self.models[name] for name in default_priorities if name in self.models]
    
    def _is_aws_environment(self) -> bool:
        """Check if running in AWS environment."""
        import os
        return (
            os.getenv('AWS_LAMBDA_FUNCTION_NAME') is not None or
            os.getenv('AWS_EXECUTION_ENV') is not None
        )
    
    def process_request(self, request: RequestSchema, request_id: str) -> Dict[str, Any]:
        """
        Process request using LangChain's native fallback runnable.
        
        Args:
            request: Validated request schema
            request_id: Request identifier
        
        Returns:
            Response data dictionary
        """
        start_time = time.time()
        
        try:
            # Get the appropriate fallback chain
            chain = self._get_fallback_chain(request)
            
            # Build messages
            messages = self._build_messages(request)
            
            # Configure model parameters
            model_kwargs = {
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
                "top_p": request.top_p
            }
            
            if request.top_k:
                model_kwargs["top_k"] = request.top_k
            
            # Configure the chain with parameters
            configured_chain = chain.bind(**model_kwargs)
            
            # Handle structured output
            if request.structured_output_enabled and request.structured_output_schema:
                parser = JsonOutputParser()
                final_chain = configured_chain | parser
                
                # Add JSON instruction to the last message
                json_instruction = f"\n\nPlease respond with valid JSON matching this schema: {request.structured_output_schema}"
                messages[-1].content += json_instruction
            else:
                final_chain = configured_chain
            
            logger.info(f"Processing request {request_id} with LangChain fallback chain")
            
            # Execute the chain - LangChain handles all fallback logic
            response = final_chain.invoke(messages)
            
            # Calculate metrics
            total_time = time.time() - start_time
            
            # Build response
            if request.structured_output_enabled:
                result = {
                    "content": str(response) if response else "",
                    "structured_data": response,
                    "total_latency": total_time,
                    "provider_latency": total_time,
                    "total_tokens": getattr(response, 'usage', {}).get('total_tokens', 0),
                    "prompt_tokens": getattr(response, 'usage', {}).get('prompt_tokens', 0),
                    "completion_tokens": getattr(response, 'usage', {}).get('completion_tokens', 0),
                    "total_cost": self._estimate_cost(request, 0)  # Will be calculated properly
                }
            else:
                result = {
                    "content": response.content if hasattr(response, 'content') else str(response),
                    "total_latency": total_time,
                    "provider_latency": total_time,
                    "total_tokens": getattr(response, 'usage', {}).get('total_tokens', 0),
                    "prompt_tokens": getattr(response, 'usage', {}).get('prompt_tokens', 0),
                    "completion_tokens": getattr(response, 'usage', {}).get('completion_tokens', 0),
                    "total_cost": self._estimate_cost(request, 0)  # Will be calculated properly
                }
            
            # Add metadata about the chain used
            result["chain_type"] = self._get_chain_type_used(request)
            result["fallback_strategy"] = request.fallback_strategy.value
            
            logger.info(f"Request {request_id} completed successfully in {total_time:.2f}s")
            
            return result
            
        except Exception as e:
            total_time = time.time() - start_time
            logger.error(f"Request {request_id} failed after {total_time:.2f}s: {e}")
            
            raise ProviderError(
                f"LangChain fallback chain failed: {str(e)}",
                provider="langchain",
                details={
                    "request_id": request_id,
                    "total_time": total_time,
                    "chain_type": self._get_chain_type_used(request),
                    "available_chains": list(self.fallback_chains.keys())
                }
            )
    
    def _get_fallback_chain(self, request: RequestSchema) -> Union[RunnableWithFallbacks, BaseChatModel]:
        """Get the appropriate fallback chain based on request."""
        
        # If specific model requested, try to get it directly
        if request.model_name and request.model_name in self.models:
            primary_model = self.models[request.model_name]
            
            if request.enable_fallback:
                # Create a custom fallback chain for this specific model
                fallback_models = self._get_fallback_models_for_specific(request.model_name, request.fallback_strategy)
                if fallback_models:
                    return primary_model.with_fallbacks(fallback_models)
            
            return primary_model
        
        # Use pre-configured fallback chains based on strategy
        if not request.enable_fallback:
            # No fallback - use first available model
            if self.models:
                return list(self.models.values())[0]
            else:
                raise ProviderError("No models available")
        
        # Get chain based on fallback strategy
        strategy_name = request.fallback_strategy.value
        
        if strategy_name in self.fallback_chains:
            return self.fallback_chains[strategy_name]
        
        # Fallback to default chain
        if "balanced" in self.fallback_chains:
            return self.fallback_chains["balanced"]
        elif "priority_order" in self.fallback_chains:
            return self.fallback_chains["priority_order"]
        else:
            # Last resort - use first available model
            return list(self.models.values())[0]
    
    def _get_fallback_models_for_specific(self, model_name: str, strategy: FallbackStrategy) -> List[BaseChatModel]:
        """Get fallback models for a specific primary model."""
        # Get all models except the primary one
        available_models = {name: model for name, model in self.models.items() if name != model_name}
        
        if strategy == FallbackStrategy.COST_OPTIMIZED:
            fallback_order = self._get_models_by_cost()
        elif strategy == FallbackStrategy.PERFORMANCE_OPTIMIZED:
            fallback_order = self._get_models_by_performance()
        else:  # PRIORITY_ORDER or others
            fallback_order = self._get_default_priority_models()
        
        # Return models that are available and not the primary
        return [model for model in fallback_order if model in available_models.values()][:3]
    
    def _build_messages(self, request: RequestSchema) -> List:
        """Build LangChain messages from request."""
        messages = []
        
        if request.system_prompt:
            messages.append(SystemMessage(content=request.system_prompt))
        
        messages.append(HumanMessage(content=request.prompt))
        
        return messages
    
    def _get_chain_type_used(self, request: RequestSchema) -> str:
        """Get the type of chain that would be used for this request."""
        if request.model_name and request.model_name in self.models:
            return f"specific_model_{request.model_name}"
        
        if not request.enable_fallback:
            return "no_fallback"
        
        return request.fallback_strategy.value
    
    def _estimate_cost(self, request: RequestSchema, tokens: int) -> float:
        """Estimate cost for the request (simplified)."""
        # This would need proper implementation based on actual usage
        # For now, return a minimal estimate
        return 0.001  # $0.001 baseline
    
    def get_available_models(self) -> Dict[str, Any]:
        """Get information about available models and chains."""
        return {
            "total_models": len(self.models),
            "available_models": list(self.models.keys()),
            "fallback_chains": list(self.fallback_chains.keys()),
            "models_by_provider": self._group_models_by_provider()
        }
    
    def _group_models_by_provider(self) -> Dict[str, List[str]]:
        """Group models by their provider."""
        groups = {}
        for model_name in self.models.keys():
            if model_name.startswith("gpt-") or model_name.startswith("o3-"):
                provider = "openai"
            elif model_name.startswith("claude-") or model_name == "claude-sonnet-4" or model_name == "claude-opus-4":
                provider = "anthropic"
            elif model_name.startswith("llama-") or model_name.startswith("mixtral-"):
                provider = "groq"
            elif model_name.startswith("mistral-") or model_name.startswith("codestral-") or model_name == "devstral":
                provider = "mistral"
            elif model_name.startswith("command-"):
                provider = "cohere"
            elif model_name.startswith("gemini-"):
                provider = "google"
            elif "anthropic." in model_name:
                provider = "bedrock"
            else:
                provider = "unknown"
            
            if provider not in groups:
                groups[provider] = []
            groups[provider].append(model_name)
        
        return groups
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on the provider."""
        try:
            return {
                "healthy": True,
                "total_models": len(self.models),
                "available_models": list(self.models.keys()),
                "fallback_chains": list(self.fallback_chains.keys()),
                "timestamp": datetime.utcnow().isoformat(),
                "langchain_fallback_enabled": True
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "healthy": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }