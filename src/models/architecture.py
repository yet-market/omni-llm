"""
Omni-LLM Architecture Schema
============================

This module defines the complete architecture schema for the Omni-LLM universal
AI Lambda gateway, including all providers, configurations, and data models.
"""

from typing import Dict, List, Optional, Union, Any, Literal
from enum import Enum
from pydantic import BaseModel, Field


# Core Architecture Components
class ArchitectureLayer(str, Enum):
    """Architecture layers in the Omni-LLM system."""
    API_GATEWAY = "api_gateway"
    LAMBDA_FUNCTION = "lambda_function"
    PROVIDER_ROUTER = "provider_router"
    RAG_ENGINE = "rag_engine"
    MCP_CLIENT = "mcp_client"
    SECURITY_LAYER = "security_layer"
    MONITORING = "monitoring"


class ComponentType(str, Enum):
    """Types of components in the system."""
    HANDLER = "handler"
    PROVIDER = "provider"
    PROCESSOR = "processor"
    STORE = "store"
    CLIENT = "client"
    UTILITY = "utility"


# Provider Architecture
class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AWS_BEDROCK = "bedrock"
    GOOGLE_VERTEX_AI = "vertexai"
    MISTRAL_AI = "mistral"
    COHERE = "cohere"
    GROQ = "groq"
    CUSTOM = "custom"


class ModelCapability(str, Enum):
    """Model capabilities."""
    CHAT = "chat"
    EMBEDDINGS = "embeddings"
    FUNCTION_CALLING = "function_calling"
    VISION = "vision"
    STREAMING = "streaming"
    RAG_COMPATIBLE = "rag_compatible"
    MCP_SUPPORT = "mcp_support"


class ModelConfiguration(BaseModel):
    """Model configuration schema."""
    name: str = Field(description="Model name")
    provider: LLMProvider = Field(description="Provider name")
    capabilities: List[ModelCapability] = Field(description="Model capabilities")
    context_length: int = Field(description="Maximum context length")
    cost_per_1m_input_tokens: float = Field(description="Cost per 1M input tokens USD")
    cost_per_1m_output_tokens: float = Field(description="Cost per 1M output tokens USD")
    latency_category: Literal["ultra_fast", "fast", "medium", "slow"] = Field(description="Latency category")
    use_cases: List[str] = Field(description="Recommended use cases")


# Vector Store Architecture
class VectorStoreType(str, Enum):
    """Supported vector store types."""
    PINECONE = "pinecone"
    OPENSEARCH = "opensearch"
    CHROMA = "chroma"
    FAISS = "faiss"
    WEAVIATE = "weaviate"
    QDRANT = "qdrant"


class VectorStoreConfiguration(BaseModel):
    """Vector store configuration schema."""
    type: VectorStoreType = Field(description="Vector store type")
    serverless_compatible: bool = Field(description="Lambda compatible")
    managed_service: bool = Field(description="Managed service")
    storage_cost_per_gb_month: Optional[float] = Field(description="Storage cost per GB/month")
    query_cost_per_1m: Optional[float] = Field(description="Query cost per 1M operations")
    max_dimensions: int = Field(description="Maximum vector dimensions")
    use_cases: List[str] = Field(description="Optimal use cases")


# RAG Architecture
class ChunkingStrategy(str, Enum):
    """Document chunking strategies."""
    FIXED_SIZE = "fixed_size"
    SEMANTIC = "semantic"
    RECURSIVE = "recursive"
    CHARACTER = "character"
    TOKEN = "token"


class EmbeddingProvider(str, Enum):
    """Embedding providers."""
    OPENAI = "openai"
    COHERE = "cohere"
    AWS_BEDROCK = "bedrock"
    GOOGLE = "google"
    SENTENCE_TRANSFORMERS = "sentence_transformers"


class EmbeddingConfiguration(BaseModel):
    """Embedding configuration schema."""
    provider: EmbeddingProvider = Field(description="Embedding provider")
    model: str = Field(description="Embedding model name")
    dimensions: int = Field(description="Vector dimensions")
    cost_per_1m_tokens: float = Field(description="Cost per 1M tokens USD")
    local_deployment: bool = Field(description="Can be deployed locally")


# MCP Architecture
class MCPTransportType(str, Enum):
    """MCP transport types."""
    HTTP = "http"
    STDIO = "stdio"
    WEBSOCKET = "websocket"


class MCPServerConfiguration(BaseModel):
    """MCP server configuration schema."""
    name: str = Field(description="Server name")
    transport: MCPTransportType = Field(description="Transport type")
    url: Optional[str] = Field(description="Server URL for HTTP/WebSocket")
    command: Optional[str] = Field(description="Command for stdio")
    tools: List[str] = Field(description="Available tools")
    timeout: int = Field(default=30, description="Timeout in seconds")


# Security Architecture
class AuthenticationType(str, Enum):
    """Authentication types."""
    API_KEY = "api_key"
    IAM_ROLE = "iam_role"
    COGNITO = "cognito"
    BEARER_TOKEN = "bearer_token"


class SecurityConfiguration(BaseModel):
    """Security configuration schema."""
    authentication: List[AuthenticationType] = Field(description="Supported auth methods")
    rate_limit_per_minute: int = Field(default=60, description="Rate limit per minute")
    rate_limit_per_hour: int = Field(default=1000, description="Rate limit per hour")
    encryption_at_rest: bool = Field(default=True, description="Encryption at rest")
    encryption_in_transit: bool = Field(default=True, description="Encryption in transit")
    audit_logging: bool = Field(default=True, description="Audit logging enabled")


# Lambda Architecture
class LambdaConfiguration(BaseModel):
    """Lambda configuration schema."""
    runtime: Literal["python3.11"] = Field(default="python3.11", description="Runtime version")
    architecture: Literal["arm64", "x86_64"] = Field(default="arm64", description="Architecture")
    memory_mb: int = Field(default=1024, description="Memory allocation in MB")
    timeout_seconds: int = Field(default=900, description="Timeout in seconds")
    ephemeral_storage_mb: int = Field(default=512, description="Ephemeral storage in MB")
    package_type: Literal["Image", "Zip"] = Field(default="Image", description="Package type")
    max_image_size_gb: int = Field(default=10, description="Maximum image size in GB")


# Request/Response Architecture
class StructuredOutputMethod(str, Enum):
    """Structured output methods."""
    PYDANTIC = "pydantic"
    JSON_SCHEMA = "json_schema"
    TYPED_DICT = "typed_dict"
    JSON_MODE = "json_mode"


class RequestSchema(BaseModel):
    """Complete request schema."""
    prompt: str = Field(description="User prompt")
    model_provider: LLMProvider = Field(description="LLM provider")
    model_name: str = Field(description="Model name")
    system_prompt: Optional[str] = Field(description="System prompt")
    
    # Model configuration
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Temperature")
    max_tokens: int = Field(default=4096, ge=1, description="Maximum tokens")
    top_p: float = Field(default=1.0, ge=0.0, le=1.0, description="Top-p sampling")
    stream: bool = Field(default=False, description="Enable streaming")
    
    # RAG configuration
    rag_enabled: bool = Field(default=False, description="Enable RAG")
    s3_bucket: Optional[str] = Field(description="S3 bucket for documents")
    vector_store_type: Optional[VectorStoreType] = Field(description="Vector store type")
    embedding_provider: Optional[EmbeddingProvider] = Field(description="Embedding provider")
    retrieval_top_k: int = Field(default=5, description="Top-k retrieval")
    
    # MCP configuration
    mcp_enabled: bool = Field(default=False, description="Enable MCP")
    mcp_servers: List[str] = Field(default=[], description="MCP servers to use")
    mcp_tools: List[str] = Field(default=[], description="Specific tools to use")
    
    # Structured output
    structured_output_enabled: bool = Field(default=False, description="Enable structured output")
    structured_output_method: Optional[StructuredOutputMethod] = Field(description="Output method")
    structured_output_schema: Optional[Dict[str, Any]] = Field(description="Output schema")


class ResponseSchema(BaseModel):
    """Complete response schema."""
    success: bool = Field(description="Request success status")
    content: Optional[str] = Field(description="Generated content")
    structured_data: Optional[Dict[str, Any]] = Field(description="Structured output data")
    
    # Metadata
    model_used: str = Field(description="Model that generated response")
    provider: LLMProvider = Field(description="Provider used")
    execution_time: float = Field(description="Execution time in seconds")
    
    # Usage statistics
    prompt_tokens: int = Field(description="Prompt tokens used")
    completion_tokens: int = Field(description="Completion tokens generated")
    total_tokens: int = Field(description="Total tokens")
    cost_usd: float = Field(description="Estimated cost in USD")
    
    # RAG context
    rag_context: Optional[List[Dict[str, Any]]] = Field(description="RAG retrieved documents")
    
    # MCP tool calls
    tool_calls: Optional[List[Dict[str, Any]]] = Field(description="MCP tool executions")
    
    # Error information
    error: Optional[Dict[str, Any]] = Field(description="Error details if failed")


# Complete System Architecture
class OmniLLMArchitecture(BaseModel):
    """Complete Omni-LLM system architecture definition."""
    
    # System metadata
    version: str = Field(default="1.0.0", description="Architecture version")
    description: str = Field(
        default="Universal AI Lambda Gateway Architecture",
        description="System description"
    )
    
    # Core components
    lambda_config: LambdaConfiguration = Field(description="Lambda configuration")
    security_config: SecurityConfiguration = Field(description="Security configuration")
    
    # Supported providers and models
    supported_providers: List[LLMProvider] = Field(description="Supported LLM providers")
    model_catalog: List[ModelConfiguration] = Field(description="Available models")
    
    # Vector stores and embeddings
    vector_stores: List[VectorStoreConfiguration] = Field(description="Vector store options")
    embedding_providers: List[EmbeddingConfiguration] = Field(description="Embedding options")
    
    # MCP configuration
    mcp_servers: List[MCPServerConfiguration] = Field(description="Available MCP servers")
    
    # API schemas
    request_schema: RequestSchema = Field(description="Request format")
    response_schema: ResponseSchema = Field(description="Response format")
    
    # Performance targets
    performance_targets: Dict[str, Union[int, float, str]] = Field(
        default={
            "cold_start_max_seconds": 5,
            "warm_response_max_seconds": 1,
            "max_concurrent_executions": 1000,
            "target_throughput_req_per_sec": 100,
            "max_memory_usage_mb": 2048,
            "target_uptime_percentage": 99.9
        },
        description="Performance targets"
    )
    
    # Cost optimization
    cost_optimization: Dict[str, Any] = Field(
        default={
            "preferred_providers": ["groq", "anthropic", "openai"],
            "cost_per_request_target": 0.01,
            "auto_routing_enabled": True,
            "caching_enabled": True
        },
        description="Cost optimization settings"
    )


# Predefined Architecture Configurations
def get_default_architecture() -> OmniLLMArchitecture:
    """Get the default Omni-LLM architecture configuration."""
    
    # Define model catalog
    model_catalog = [
        ModelConfiguration(
            name="gpt-4",
            provider=LLMProvider.OPENAI,
            capabilities=[
                ModelCapability.CHAT,
                ModelCapability.FUNCTION_CALLING,
                ModelCapability.VISION,
                ModelCapability.STREAMING,
                ModelCapability.RAG_COMPATIBLE,
                ModelCapability.MCP_SUPPORT
            ],
            context_length=8192,
            cost_per_1m_input_tokens=30.0,
            cost_per_1m_output_tokens=60.0,
            latency_category="medium",
            use_cases=["complex reasoning", "function calling", "RAG", "vision tasks"]
        ),
        ModelConfiguration(
            name="claude-3-5-sonnet",
            provider=LLMProvider.ANTHROPIC,
            capabilities=[
                ModelCapability.CHAT,
                ModelCapability.FUNCTION_CALLING,
                ModelCapability.VISION,
                ModelCapability.STREAMING,
                ModelCapability.RAG_COMPATIBLE,
                ModelCapability.MCP_SUPPORT
            ],
            context_length=200000,
            cost_per_1m_input_tokens=15.0,
            cost_per_1m_output_tokens=75.0,
            latency_category="medium",
            use_cases=["long context", "reasoning", "tool use", "code generation"]
        ),
        ModelConfiguration(
            name="llama-3.1-70b",
            provider=LLMProvider.GROQ,
            capabilities=[
                ModelCapability.CHAT,
                ModelCapability.FUNCTION_CALLING,
                ModelCapability.STREAMING,
                ModelCapability.RAG_COMPATIBLE,
                ModelCapability.MCP_SUPPORT
            ],
            context_length=8192,
            cost_per_1m_input_tokens=0.05,
            cost_per_1m_output_tokens=0.08,
            latency_category="ultra_fast",
            use_cases=["real-time chat", "fast inference", "cost optimization"]
        )
    ]
    
    # Define vector stores
    vector_stores = [
        VectorStoreConfiguration(
            type=VectorStoreType.PINECONE,
            serverless_compatible=True,
            managed_service=True,
            storage_cost_per_gb_month=0.096,
            query_cost_per_1m=0.40,
            max_dimensions=40960,
            use_cases=["production", "high scale", "managed service"]
        ),
        VectorStoreConfiguration(
            type=VectorStoreType.OPENSEARCH,
            serverless_compatible=True,
            managed_service=True,
            storage_cost_per_gb_month=0.10,
            query_cost_per_1m=0.20,
            max_dimensions=16000,
            use_cases=["AWS native", "enterprise", "cost control"]
        ),
        VectorStoreConfiguration(
            type=VectorStoreType.CHROMA,
            serverless_compatible=True,
            managed_service=False,
            storage_cost_per_gb_month=None,
            query_cost_per_1m=None,
            max_dimensions=2048,
            use_cases=["development", "prototyping", "self-hosted"]
        )
    ]
    
    # Define embedding providers
    embedding_providers = [
        EmbeddingConfiguration(
            provider=EmbeddingProvider.OPENAI,
            model="text-embedding-3-large",
            dimensions=3072,
            cost_per_1m_tokens=0.02,
            local_deployment=False
        ),
        EmbeddingConfiguration(
            provider=EmbeddingProvider.COHERE,
            model="embed-english-v3.0",
            dimensions=1024,
            cost_per_1m_tokens=0.10,
            local_deployment=False
        ),
        EmbeddingConfiguration(
            provider=EmbeddingProvider.AWS_BEDROCK,
            model="amazon.titan-embed-text-v1",
            dimensions=1536,
            cost_per_1m_tokens=0.02,
            local_deployment=False
        )
    ]
    
    # Define MCP servers
    mcp_servers = [
        MCPServerConfiguration(
            name="filesystem",
            transport=MCPTransportType.HTTP,
            url="https://filesystem-mcp.example.com",
            tools=["read_file", "write_file", "list_directory"],
            timeout=30
        ),
        MCPServerConfiguration(
            name="web_search",
            transport=MCPTransportType.HTTP,
            url="https://web-search-mcp.example.com",
            tools=["search_web", "fetch_url", "extract_content"],
            timeout=60
        )
    ]
    
    return OmniLLMArchitecture(
        supported_providers=[
            LLMProvider.OPENAI,
            LLMProvider.ANTHROPIC,
            LLMProvider.AWS_BEDROCK,
            LLMProvider.GOOGLE_VERTEX_AI,
            LLMProvider.MISTRAL_AI,
            LLMProvider.COHERE,
            LLMProvider.GROQ
        ],
        model_catalog=model_catalog,
        vector_stores=vector_stores,
        embedding_providers=embedding_providers,
        mcp_servers=mcp_servers,
        lambda_config=LambdaConfiguration(),
        security_config=SecurityConfiguration(
            authentication=[
                AuthenticationType.API_KEY,
                AuthenticationType.IAM_ROLE
            ]
        ),
        request_schema=RequestSchema(
            prompt="Example prompt",
            model_provider=LLMProvider.OPENAI,
            model_name="gpt-4"
        ),
        response_schema=ResponseSchema(
            success=True,
            content="Example response",
            model_used="gpt-4",
            provider=LLMProvider.OPENAI,
            execution_time=1.5,
            prompt_tokens=100,
            completion_tokens=200,
            total_tokens=300,
            cost_usd=0.01
        )
    )


# Export the complete architecture
OMNI_LLM_ARCHITECTURE = get_default_architecture()