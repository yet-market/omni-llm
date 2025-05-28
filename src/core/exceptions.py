"""
Omni-LLM Exception Classes
==========================

Custom exception classes for error handling throughout the system.
"""

from typing import Optional, Dict, Any


class OmniLLMError(Exception):
    """Base exception class for Omni-LLM errors."""
    
    def __init__(
        self,
        message: str,
        error_code: str = "OMNI_LLM_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}


class ValidationError(OmniLLMError):
    """Exception raised for request validation errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=400,
            details=details
        )


class ProviderError(OmniLLMError):
    """Exception raised for LLM provider errors."""
    
    def __init__(
        self,
        message: str,
        provider: str,
        model: Optional[str] = None,
        status_code: int = 502,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code="PROVIDER_ERROR",
            status_code=status_code,
            details=details or {}
        )
        self.provider = provider
        self.model = model


class AuthenticationError(OmniLLMError):
    """Exception raised for authentication errors."""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            status_code=401
        )


class RateLimitError(OmniLLMError):
    """Exception raised for rate limit errors."""
    
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_ERROR",
            status_code=429
        )


class TimeoutError(OmniLLMError):
    """Exception raised for timeout errors."""
    
    def __init__(self, message: str = "Request timeout"):
        super().__init__(
            message=message,
            error_code="TIMEOUT_ERROR",
            status_code=504
        )


class ConfigurationError(OmniLLMError):
    """Exception raised for configuration errors."""
    
    def __init__(self, message: str):
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            status_code=500
        )