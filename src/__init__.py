"""
Omni-LLM: Universal AI Lambda Gateway
====================================

A serverless AWS Lambda function that provides a unified gateway for all LLM
interactions, supporting multiple AI providers, RAG capabilities, and dynamic
tool integration through a single API endpoint.

Author: Temkit Sid-Ali <contact@yet.lu>
Organization: yet.lu
License: MIT
"""

__version__ = "1.0.0"
__author__ = "Temkit Sid-Ali"
__email__ = "contact@yet.lu"
__license__ = "MIT"

from .models.architecture import OMNI_LLM_ARCHITECTURE, OmniLLMArchitecture

__all__ = [
    "OMNI_LLM_ARCHITECTURE",
    "OmniLLMArchitecture",
    "__version__",
    "__author__",
    "__email__",
    "__license__"
]