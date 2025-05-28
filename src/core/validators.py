"""
Omni-LLM Request Validators - LangChain Based
============================================

Request validation and sanitization functions for LangChain provider.
"""

from typing import Dict, Any
from pydantic import ValidationError as PydanticValidationError

from .exceptions import ValidationError
from ..models.architecture import RequestSchema, LLMProvider


def validate_request(request_data: Dict[str, Any]) -> RequestSchema:
    """
    Validate and parse incoming request data for LangChain provider.
    
    Args:
        request_data: Raw request data dictionary
    
    Returns:
        Validated RequestSchema object
    
    Raises:
        ValidationError: If validation fails
    """
    try:
        # Parse with Pydantic model
        request = RequestSchema(**request_data)
        
        # Additional business logic validation
        _validate_model_availability(request)
        _validate_fallback_config(request)
        _validate_rag_config(request)
        _validate_mcp_config(request)
        _validate_structured_output(request)
        
        return request
        
    except PydanticValidationError as e:
        error_details = []
        for error in e.errors():
            field_path = " -> ".join(str(loc) for loc in error['loc'])
            error_details.append(f"{field_path}: {error['msg']}")
        
        raise ValidationError(
            f"Request validation failed: {'; '.join(error_details)}",
            details={"validation_errors": e.errors()}
        )
    except Exception as e:
        raise ValidationError(f"Request validation error: {str(e)}")


def _validate_model_availability(request: RequestSchema) -> None:
    """
    Validate that requested models/providers are available.
    
    Args:
        request: The request schema
    
    Raises:
        ValidationError: If model/provider combination is invalid
    """
    # Get available models from catalog
    from ..models.architecture import get_langchain_model_catalog
    
    catalog = get_langchain_model_catalog()
    available_models = {model.name: model for model in catalog}
    
    # Validate specific model if requested
    if request.model_name:
        if request.model_name not in available_models:
            available_model_names = list(available_models.keys())
            raise ValidationError(
                f"Model '{request.model_name}' is not available. "
                f"Available models: {', '.join(available_model_names[:10])}{'...' if len(available_model_names) > 10 else ''}"
            )
    
    # Validate provider preferences
    if request.provider_preference:
        available_providers = set(model.provider for model in catalog)
        
        for provider in request.provider_preference:
            if provider not in available_providers:
                raise ValidationError(
                    f"Provider '{provider.value}' is not available. "
                    f"Available providers: {', '.join(p.value for p in available_providers)}"
                )


def _validate_fallback_config(request: RequestSchema) -> None:
    """
    Validate fallback configuration.
    
    Args:
        request: The request schema
    
    Raises:
        ValidationError: If fallback config is invalid
    """
    if request.max_fallback_attempts < 1:
        raise ValidationError("max_fallback_attempts must be at least 1")
    
    if request.max_fallback_attempts > 10:
        raise ValidationError("max_fallback_attempts cannot exceed 10")
    
    # If fallback is disabled but specific model not provided, that could be problematic
    if not request.enable_fallback and not request.model_name and not request.provider_preference:
        raise ValidationError(
            "When fallback is disabled, you must specify either model_name or provider_preference"
        )


def _validate_rag_config(request: RequestSchema) -> None:
    """
    Validate RAG configuration if enabled.
    
    Args:
        request: The request schema
    
    Raises:
        ValidationError: If RAG config is invalid
    """
    if not request.rag_enabled:
        return
    
    if not request.s3_bucket:
        raise ValidationError("s3_bucket is required when RAG is enabled")
    
    if not request.vector_store_type:
        raise ValidationError("vector_store_type is required when RAG is enabled")
    
    # Validate vector store type
    supported_vector_stores = ["chroma", "pinecone", "opensearch", "faiss", "weaviate", "qdrant"]
    if request.vector_store_type not in supported_vector_stores:
        raise ValidationError(
            f"vector_store_type '{request.vector_store_type}' not supported. "
            f"Supported types: {', '.join(supported_vector_stores)}"
        )
    
    if request.retrieval_top_k < 1:
        raise ValidationError("retrieval_top_k must be at least 1")
    
    if request.retrieval_top_k > 50:
        raise ValidationError("retrieval_top_k cannot exceed 50")


def _validate_mcp_config(request: RequestSchema) -> None:
    """
    Validate MCP configuration if enabled.
    
    Args:
        request: The request schema
    
    Raises:
        ValidationError: If MCP config is invalid
    """
    if not request.mcp_enabled:
        return
    
    if not request.mcp_servers:
        raise ValidationError("mcp_servers list cannot be empty when MCP is enabled")
    
    # Validate server names (basic validation)
    for server in request.mcp_servers:
        if not server or not isinstance(server, str):
            raise ValidationError("All MCP server names must be non-empty strings")
        
        if len(server) > 100:
            raise ValidationError("MCP server names cannot exceed 100 characters")
    
    # Validate tool names if specified
    for tool in request.mcp_tools:
        if not tool or not isinstance(tool, str):
            raise ValidationError("All MCP tool names must be non-empty strings")
        
        if len(tool) > 100:
            raise ValidationError("MCP tool names cannot exceed 100 characters")


def _validate_structured_output(request: RequestSchema) -> None:
    """
    Validate structured output configuration.
    
    Args:
        request: The request schema
    
    Raises:
        ValidationError: If structured output config is invalid
    """
    if not request.structured_output_enabled:
        return
    
    if not request.structured_output_schema:
        raise ValidationError("structured_output_schema is required when structured_output_enabled is True")
    
    if not isinstance(request.structured_output_schema, dict):
        raise ValidationError("structured_output_schema must be a dictionary")
    
    # Basic schema validation
    if not request.structured_output_schema:
        raise ValidationError("structured_output_schema cannot be empty")
    
    # Check for reasonable schema size (prevent abuse)
    import json
    schema_str = json.dumps(request.structured_output_schema)
    if len(schema_str) > 10000:  # 10KB limit
        raise ValidationError("structured_output_schema is too large (max 10KB)")


def validate_api_key_format(api_key: str) -> bool:
    """
    Validate API key format.
    
    Args:
        api_key: The API key to validate
    
    Returns:
        True if format is valid, False otherwise
    """
    if not api_key:
        return False
    
    # Basic format validation
    if len(api_key) < 8:
        return False
    
    # Must contain alphanumeric characters and hyphens only
    allowed_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.')
    if not all(c in allowed_chars for c in api_key):
        return False
    
    return True


def validate_model_parameters(request: RequestSchema) -> None:
    """
    Validate model parameters are within acceptable ranges.
    
    Args:
        request: The request schema
    
    Raises:
        ValidationError: If parameters are invalid
    """
    # Temperature validation
    if not 0.0 <= request.temperature <= 2.0:
        raise ValidationError("temperature must be between 0.0 and 2.0")
    
    # Max tokens validation
    if request.max_tokens < 1:
        raise ValidationError("max_tokens must be at least 1")
    
    if request.max_tokens > 128000:  # Reasonable upper limit
        raise ValidationError("max_tokens cannot exceed 128,000")
    
    # Top-p validation
    if not 0.0 <= request.top_p <= 1.0:
        raise ValidationError("top_p must be between 0.0 and 1.0")
    
    # Top-k validation
    if request.top_k is not None:
        if request.top_k < 1:
            raise ValidationError("top_k must be at least 1")
        
        if request.top_k > 100:
            raise ValidationError("top_k cannot exceed 100")
    
    # Timeout validation
    if not 1 <= request.timeout <= 900:
        raise ValidationError("timeout must be between 1 and 900 seconds")


def get_supported_models() -> Dict[str, Any]:
    """
    Get list of supported models and their capabilities.
    
    Returns:
        Dictionary of supported models and metadata
    """
    from ..models.architecture import get_langchain_model_catalog
    
    catalog = get_langchain_model_catalog()
    
    models_by_provider = {}
    for model in catalog:
        provider_name = model.provider.value
        if provider_name not in models_by_provider:
            models_by_provider[provider_name] = []
        
        models_by_provider[provider_name].append({
            "name": model.name,
            "capabilities": [cap.value for cap in model.capabilities],
            "context_length": model.context_length,
            "cost_per_1m_input": model.cost_per_1m_input_tokens,
            "cost_per_1m_output": model.cost_per_1m_output_tokens,
            "latency_category": model.latency_category,
            "priority": model.priority,
            "use_cases": model.use_cases
        })
    
    return {
        "total_models": len(catalog),
        "providers": len(models_by_provider),
        "models_by_provider": models_by_provider,
        "supported_features": [
            "automatic_fallback",
            "cost_optimization", 
            "performance_optimization",
            "structured_output",
            "streaming",
            "function_calling",
            "vision",
            "rag_integration",
            "mcp_tools"
        ]
    }