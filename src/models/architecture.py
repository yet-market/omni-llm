"""
Omni-LLM Architecture Schema - LangChain Based
==============================================

This module defines the complete architecture schema for the Omni-LLM universal
AI Lambda gateway using LangChain as the single provider with built-in fallback support.
"""

from typing import Dict, List, Optional, Union, Any, Literal
from enum import Enum
from pydantic import BaseModel, Field


# Core Architecture Components
class ArchitectureLayer(str, Enum):
    """Architecture layers in the Omni-LLM system."""
    API_GATEWAY = "api_gateway"
    LAMBDA_FUNCTION = "lambda_function"
    LANGCHAIN_PROVIDER = "langchain_provider"
    RAG_ENGINE = "rag_engine"
    MCP_CLIENT = "mcp_client"
    SECURITY_LAYER = "security_layer"
    MONITORING = "monitoring"


# LangChain Provider Configuration
class LLMProvider(str, Enum):
    """Supported LLM providers through LangChain."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AWS_BEDROCK = "bedrock"
    GOOGLE_VERTEX_AI = "vertexai"
    MISTRAL_AI = "mistral"
    COHERE = "cohere"
    GROQ = "groq"
    HUGGING_FACE = "huggingface"
    OLLAMA = "ollama"


class ModelCapability(str, Enum):
    """Model capabilities through LangChain."""
    CHAT = "chat"
    EMBEDDINGS = "embeddings"
    FUNCTION_CALLING = "function_calling"
    VISION = "vision"
    STREAMING = "streaming"
    RAG_COMPATIBLE = "rag_compatible"
    MCP_SUPPORT = "mcp_support"


class FallbackStrategy(str, Enum):
    """LangChain native fallback strategies."""
    PRIORITY_ORDER = "priority_order"
    COST_OPTIMIZED = "cost_optimized"
    PERFORMANCE_OPTIMIZED = "performance_optimized"
    QUALITY_OPTIMIZED = "quality_optimized"
    BALANCED = "balanced"


class ModelConfiguration(BaseModel):
    """LangChain model configuration schema."""
    name: str = Field(description="Model name as used in LangChain")
    provider: LLMProvider = Field(description="Provider name")
    capabilities: List[ModelCapability] = Field(description="Model capabilities")
    context_length: int = Field(description="Maximum context length")
    cost_per_1m_input_tokens: float = Field(description="Cost per 1M input tokens USD")
    cost_per_1m_output_tokens: float = Field(description="Cost per 1M output tokens USD")
    latency_category: Literal["ultra_fast", "fast", "medium", "slow"] = Field(description="Latency category")
    priority: int = Field(default=1, description="Priority for fallback (1=highest)")
    use_cases: List[str] = Field(description="Recommended use cases")


# Request/Response Schema
class RequestSchema(BaseModel):
    """Complete request schema for LangChain provider."""
    prompt: str = Field(description="User prompt")
    
    # Model Selection
    model_name: Optional[str] = Field(default=None, description="Specific model name")
    provider_preference: Optional[List[LLMProvider]] = Field(default=None, description="Preferred providers in order")
    
    # LangChain Parameters
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Temperature")
    max_tokens: int = Field(default=4096, ge=1, description="Maximum tokens")
    top_p: float = Field(default=1.0, ge=0.0, le=1.0, description="Top-p sampling")
    top_k: Optional[int] = Field(default=None, ge=1, description="Top-k sampling")
    stream: bool = Field(default=False, description="Enable streaming")
    
    # System Configuration
    system_prompt: Optional[str] = Field(default=None, description="System prompt")
    
    # Fallback Configuration
    enable_fallback: bool = Field(default=True, description="Enable provider fallback")
    fallback_strategy: FallbackStrategy = Field(default=FallbackStrategy.PRIORITY_ORDER, description="Fallback strategy")
    max_fallback_attempts: int = Field(default=3, ge=1, le=10, description="Maximum fallback attempts")
    
    # RAG Configuration
    rag_enabled: bool = Field(default=False, description="Enable RAG")
    s3_bucket: Optional[str] = Field(default=None, description="S3 bucket for documents")
    vector_store_type: Optional[str] = Field(default="chroma", description="Vector store type")
    embedding_model: Optional[str] = Field(default="text-embedding-3-small", description="Embedding model")
    retrieval_top_k: int = Field(default=5, description="Top-k retrieval")
    
    # MCP Configuration
    mcp_enabled: bool = Field(default=False, description="Enable MCP")
    mcp_servers: List[str] = Field(default=[], description="MCP servers to use")
    mcp_tools: List[str] = Field(default=[], description="Specific tools to use")
    
    # Structured Output
    structured_output_enabled: bool = Field(default=False, description="Enable structured output")
    structured_output_schema: Optional[Dict[str, Any]] = Field(default=None, description="Output schema")
    
    # Advanced Options
    timeout: int = Field(default=300, ge=1, le=900, description="Request timeout in seconds")
    cache_enabled: bool = Field(default=True, description="Enable response caching")


class ProviderAttempt(BaseModel):
    """Details of a provider attempt."""
    provider: LLMProvider = Field(description="Provider attempted")
    model: str = Field(description="Model attempted")
    success: bool = Field(description="Whether attempt succeeded")
    error: Optional[str] = Field(description="Error message if failed")
    latency: float = Field(description="Response time in seconds")
    cost: float = Field(description="Cost in USD")


class ResponseSchema(BaseModel):
    """Complete response schema."""
    success: bool = Field(description="Request success status")
    content: Optional[str] = Field(description="Generated content")
    structured_data: Optional[Dict[str, Any]] = Field(description="Structured output data")
    
    # Provider Information
    provider_used: LLMProvider = Field(description="Final provider used")
    model_used: str = Field(description="Final model used")
    fallback_attempts: List[ProviderAttempt] = Field(description="All provider attempts")
    
    # Usage Statistics
    total_tokens: int = Field(description="Total tokens used")
    prompt_tokens: int = Field(description="Prompt tokens")
    completion_tokens: int = Field(description="Completion tokens")
    total_cost: float = Field(description="Total cost in USD")
    
    # Performance Metrics
    total_latency: float = Field(description="Total request time in seconds")
    provider_latency: float = Field(description="Provider response time in seconds")
    
    # RAG Context
    rag_context: Optional[List[Dict[str, Any]]] = Field(description="RAG retrieved documents")
    
    # MCP Tool Calls
    tool_calls: Optional[List[Dict[str, Any]]] = Field(description="MCP tool executions")
    
    # Error Information
    error: Optional[Dict[str, Any]] = Field(description="Error details if failed")
    
    # Metadata
    request_id: str = Field(description="Request identifier")
    timestamp: str = Field(description="Response timestamp")


class LangChainConfiguration(BaseModel):
    """LangChain provider configuration."""
    
    # Provider Configurations
    openai_config: Dict[str, Any] = Field(default_factory=dict, description="OpenAI configuration")
    anthropic_config: Dict[str, Any] = Field(default_factory=dict, description="Anthropic configuration")
    bedrock_config: Dict[str, Any] = Field(default_factory=dict, description="AWS Bedrock configuration")
    vertexai_config: Dict[str, Any] = Field(default_factory=dict, description="Google Vertex AI configuration")
    mistral_config: Dict[str, Any] = Field(default_factory=dict, description="Mistral AI configuration")
    cohere_config: Dict[str, Any] = Field(default_factory=dict, description="Cohere configuration")
    groq_config: Dict[str, Any] = Field(default_factory=dict, description="Groq configuration")
    
    # LangChain Fallback Configuration
    default_fallback_strategy: FallbackStrategy = Field(default=FallbackStrategy.BALANCED)
    
    # Performance Configuration
    provider_timeout: int = Field(default=60, description="Individual provider timeout")
    cache_ttl: int = Field(default=3600, description="Cache TTL in seconds")
    
    # Cost Management
    cost_per_request_limit: float = Field(default=1.0, description="Max cost per request USD")
    enable_cost_optimization: bool = Field(default=True, description="Enable cost-based routing")


# Complete System Architecture
class OmniLLMArchitecture(BaseModel):
    """Complete Omni-LLM system architecture definition using LangChain."""
    
    # System metadata
    version: str = Field(default="2.0.0", description="Architecture version")
    description: str = Field(
        default="Universal AI Lambda Gateway with LangChain Provider",
        description="System description"
    )
    
    # Core configuration
    langchain_config: LangChainConfiguration = Field(description="LangChain configuration")
    
    # Available models through LangChain
    model_catalog: List[ModelConfiguration] = Field(description="Available models")
    
    # Request/Response schemas
    request_schema: RequestSchema = Field(description="Request format")
    response_schema: ResponseSchema = Field(description="Response format")
    
    # Performance targets
    performance_targets: Dict[str, Union[int, float, str]] = Field(
        default={
            "cold_start_max_seconds": 5,
            "warm_response_max_seconds": 1,
            "fallback_max_seconds": 30,
            "max_concurrent_requests": 1000,
            "target_uptime_percentage": 99.9,
            "cost_per_request_target": 0.01
        },
        description="Performance targets"
    )


# Predefined Model Catalog for LangChain
def get_langchain_model_catalog() -> List[ModelConfiguration]:
    """Get the default model catalog for LangChain providers."""
    
    return [
        # OpenAI Models
        ModelConfiguration(
            name="gpt-4o",
            provider=LLMProvider.OPENAI,
            capabilities=[ModelCapability.CHAT, ModelCapability.FUNCTION_CALLING, ModelCapability.VISION, ModelCapability.STREAMING],
            context_length=128000,
            cost_per_1m_input_tokens=5.0,
            cost_per_1m_output_tokens=15.0,
            latency_category="fast",
            priority=1,
            use_cases=["general purpose", "vision", "function calling"]
        ),
        ModelConfiguration(
            name="gpt-4o-mini",
            provider=LLMProvider.OPENAI,
            capabilities=[ModelCapability.CHAT, ModelCapability.FUNCTION_CALLING, ModelCapability.STREAMING],
            context_length=128000,
            cost_per_1m_input_tokens=0.15,
            cost_per_1m_output_tokens=0.6,
            latency_category="fast",
            priority=2,
            use_cases=["cost-effective", "high volume", "simple tasks"]
        ),
        ModelConfiguration(
            name="gpt-3.5-turbo",
            provider=LLMProvider.OPENAI,
            capabilities=[ModelCapability.CHAT, ModelCapability.FUNCTION_CALLING, ModelCapability.STREAMING],
            context_length=16384,
            cost_per_1m_input_tokens=1.5,
            cost_per_1m_output_tokens=2.0,
            latency_category="fast",
            priority=3,
            use_cases=["budget-friendly", "simple conversations"]
        ),
        
        # Anthropic Models
        ModelConfiguration(
            name="claude-3-5-sonnet-20241022",
            provider=LLMProvider.ANTHROPIC,
            capabilities=[ModelCapability.CHAT, ModelCapability.FUNCTION_CALLING, ModelCapability.VISION, ModelCapability.STREAMING],
            context_length=200000,
            cost_per_1m_input_tokens=15.0,
            cost_per_1m_output_tokens=75.0,
            latency_category="medium",
            priority=1,
            use_cases=["reasoning", "analysis", "long context"]
        ),
        ModelConfiguration(
            name="claude-3-5-haiku-20241022",
            provider=LLMProvider.ANTHROPIC,
            capabilities=[ModelCapability.CHAT, ModelCapability.FUNCTION_CALLING, ModelCapability.STREAMING],
            context_length=200000,
            cost_per_1m_input_tokens=1.0,
            cost_per_1m_output_tokens=5.0,
            latency_category="fast",
            priority=2,
            use_cases=["fast responses", "cost-effective"]
        ),
        
        # Groq Models (Ultra-fast)
        ModelConfiguration(
            name="llama-3.1-70b-versatile",
            provider=LLMProvider.GROQ,
            capabilities=[ModelCapability.CHAT, ModelCapability.FUNCTION_CALLING, ModelCapability.STREAMING],
            context_length=32768,
            cost_per_1m_input_tokens=0.59,
            cost_per_1m_output_tokens=0.79,
            latency_category="ultra_fast",
            priority=1,
            use_cases=["real-time", "low latency", "cost-effective"]
        ),
        ModelConfiguration(
            name="llama-3.1-8b-instant",
            provider=LLMProvider.GROQ,
            capabilities=[ModelCapability.CHAT, ModelCapability.STREAMING],
            context_length=32768,
            cost_per_1m_input_tokens=0.05,
            cost_per_1m_output_tokens=0.08,
            latency_category="ultra_fast",
            priority=2,
            use_cases=["ultra-fast", "ultra-cheap", "simple tasks"]
        ),
        
        # Mistral Models
        ModelConfiguration(
            name="mistral-large-latest",
            provider=LLMProvider.MISTRAL_AI,
            capabilities=[ModelCapability.CHAT, ModelCapability.FUNCTION_CALLING, ModelCapability.STREAMING],
            context_length=32768,
            cost_per_1m_input_tokens=4.0,
            cost_per_1m_output_tokens=12.0,
            latency_category="medium",
            priority=1,
            use_cases=["multilingual", "reasoning"]
        ),
        
        # Cohere Models
        ModelConfiguration(
            name="command-r-plus",
            provider=LLMProvider.COHERE,
            capabilities=[ModelCapability.CHAT, ModelCapability.FUNCTION_CALLING, ModelCapability.RAG_COMPATIBLE],
            context_length=128000,
            cost_per_1m_input_tokens=3.0,
            cost_per_1m_output_tokens=15.0,
            latency_category="medium",
            priority=1,
            use_cases=["RAG", "enterprise", "search"]
        )
    ]


def get_default_architecture() -> OmniLLMArchitecture:
    """Get the default Omni-LLM architecture configuration."""
    
    return OmniLLMArchitecture(
        langchain_config=LangChainConfiguration(),
        model_catalog=get_langchain_model_catalog(),
        request_schema=RequestSchema(
            prompt="Example prompt",
            model_name="gpt-4o-mini"
        ),
        response_schema=ResponseSchema(
            success=True,
            content="Example response",
            structured_data=None,
            provider_used=LLMProvider.OPENAI,
            model_used="gpt-4o-mini",
            fallback_attempts=[],
            total_tokens=100,
            prompt_tokens=50,
            completion_tokens=50,
            total_cost=0.01,
            total_latency=1.5,
            provider_latency=1.2,
            rag_context=None,
            tool_calls=None,
            error=None,
            request_id="example-123",
            timestamp="2024-01-01T00:00:00Z"
        )
    )


# Export the complete architecture
OMNI_LLM_ARCHITECTURE = get_default_architecture()