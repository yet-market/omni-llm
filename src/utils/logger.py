"""
Omni-LLM Logging Setup
=====================

Centralized logging configuration for the application.
"""

import logging
import sys
import os
import json
from typing import Any, Dict
from datetime import datetime


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_obj = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ('name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                          'filename', 'module', 'lineno', 'funcName', 'created',
                          'msecs', 'relativeCreated', 'thread', 'threadName',
                          'processName', 'process', 'getMessage', 'exc_info',
                          'exc_text', 'stack_info'):
                log_obj[key] = value
        
        return json.dumps(log_obj, default=str)


def setup_logger(name: str = None) -> logging.Logger:
    """
    Setup logger with appropriate configuration.
    
    Args:
        name: Logger name (defaults to calling module)
    
    Returns:
        Configured logger instance
    """
    # Get log level from environment
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    
    # Create logger
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    logger.setLevel(getattr(logging, log_level, logging.INFO))
    
    # Create handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logger.level)
    
    # Choose formatter based on environment
    if _is_aws_environment():
        # Use JSON formatter for AWS CloudWatch
        formatter = JSONFormatter()
    else:
        # Use simple formatter for local development
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger


def _is_aws_environment() -> bool:
    """Check if running in AWS environment."""
    return (
        os.getenv('AWS_LAMBDA_FUNCTION_NAME') is not None or
        os.getenv('AWS_EXECUTION_ENV') is not None
    )


def log_request_response(logger: logging.Logger, request_id: str, 
                        request_data: Dict[str, Any], 
                        response_data: Dict[str, Any] = None,
                        error: Exception = None) -> None:
    """
    Log request and response data with sanitization.
    
    Args:
        logger: Logger instance
        request_id: Request identifier
        request_data: Request data (will be sanitized)
        response_data: Response data (optional)
        error: Error information (optional)
    """
    # Sanitize request data
    sanitized_request = _sanitize_log_data(request_data)
    
    log_entry = {
        "request_id": request_id,
        "request": sanitized_request
    }
    
    if response_data:
        sanitized_response = _sanitize_log_data(response_data)
        log_entry["response"] = sanitized_response
    
    if error:
        log_entry["error"] = {
            "type": type(error).__name__,
            "message": str(error)
        }
        logger.error("Request processing failed", extra=log_entry)
    else:
        logger.info("Request processed", extra=log_entry)


def _sanitize_log_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize log data to remove sensitive information.
    
    Args:
        data: Data to sanitize
    
    Returns:
        Sanitized data
    """
    if not isinstance(data, dict):
        return data
    
    sensitive_keys = {
        'api_key', 'token', 'password', 'secret', 'credential',
        'authorization', 'auth', 'key', 'private'
    }
    
    sanitized = {}
    
    for key, value in data.items():
        key_lower = key.lower()
        
        # Check if key contains sensitive information
        if any(sensitive in key_lower for sensitive in sensitive_keys):
            sanitized[key] = "[REDACTED]"
        elif isinstance(value, dict):
            sanitized[key] = _sanitize_log_data(value)
        elif isinstance(value, list):
            sanitized[key] = [_sanitize_log_data(item) if isinstance(item, dict) else item 
                             for item in value]
        else:
            sanitized[key] = value
    
    return sanitized