"""
Omni-LLM Request Validators
==========================

Request validation and sanitization functions.
"""

from typing import Dict, Any
from pydantic import ValidationError as PydanticValidationError

from .exceptions import ValidationError
from ..models.architecture import RequestSchema, LLMProvider


def validate_request(request_data: Dict[str, Any]) -> RequestSchema:
    """
    Validate and parse incoming request data.
    
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
        _validate_provider_model_compatibility(request.model_provider, request.model_name)
        _validate_rag_config(request)
        _validate_mcp_config(request)
        
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


def _validate_provider_model_compatibility(provider: LLMProvider, model_name: str) -> None:
    """
    Validate that the model is compatible with the provider.
    
    Args:
        provider: The LLM provider
        model_name: The model name
    
    Raises:
        ValidationError: If provider/model combination is invalid
    """
    # Define provider-specific model mappings
    provider_models = {
        LLMProvider.OPENAI: [
            "gpt-4", "gpt-4-turbo", "gpt-4o", "gpt-4o-mini",
            "gpt-3.5-turbo", "gpt-3.5-turbo-16k"
        ],
        LLMProvider.ANTHROPIC: [
            "claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022",
            "claude-3-opus-20240229", "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307"
        ],
        LLMProvider.AWS_BEDROCK: [
            "anthropic.claude-3-5-sonnet-20241022-v2:0",
            "anthropic.claude-3-5-haiku-20241022-v1:0",
            "anthropic.claude-3-opus-20240229-v1:0",
            "amazon.titan-text-premier-v1:0",
            "meta.llama3-70b-instruct-v1:0"
        ],
        LLMProvider.GOOGLE_VERTEX_AI: [
            "gemini-1.5-pro", "gemini-1.5-flash",
            "gemini-1.0-pro", "text-bison"
        ],
        LLMProvider.MISTRAL_AI: [
            "mistral-large-latest", "mistral-medium-latest",
            "mistral-small-latest", "open-mixtral-8x7b"
        ],
        LLMProvider.COHERE: [
            "command-r-plus", "command-r", "command",
            "command-light", "embed-english-v3.0"
        ],
        LLMProvider.GROQ: [
            "llama-3.1-70b-versatile", "llama-3.1-8b-instant",
            "llama-3.2-90b-text-preview", "mixtral-8x7b-32768",
            "gemma-7b-it"
        ]
    }
    
    if provider not in provider_models:
        return  # Allow custom providers
    
    valid_models = provider_models[provider]
    if model_name not in valid_models:
        raise ValidationError(
            f"Model '{model_name}' is not supported by provider '{provider.value}'. "
            f"Supported models: {', '.join(valid_models)}"
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
    
    if not request.embedding_provider:
        raise ValidationError("embedding_provider is required when RAG is enabled")


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
    allowed_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_')
    if not all(c in allowed_chars for c in api_key):
        return False
    
    return True