"""
Base Provider Class
==================

Abstract base class for all LLM providers.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from ..models.architecture import RequestSchema


class BaseProvider(ABC):
    """Abstract base class for LLM providers."""
    
    def __init__(self, config):
        """
        Initialize the provider.
        
        Args:
            config: Configuration object
        """
        self.config = config
    
    @abstractmethod
    def process_request(self, request: RequestSchema, request_id: str) -> Dict[str, Any]:
        """
        Process a request through the provider.
        
        Args:
            request: Validated request schema
            request_id: Request identifier
        
        Returns:
            Response data dictionary
        """
        pass
    
    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check for the provider.
        
        Returns:
            Health check results
        """
        pass