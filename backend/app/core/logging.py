#!/usr/bin/env python3
"""
Structured logging configuration with sensitive data redaction
"""

import logging
import json
import re
from typing import Any, Dict, Optional
from datetime import datetime


class SensitiveDataFilter(logging.Filter):
    """
    Filter to redact sensitive data from log messages
    """
    
    # Patterns to match sensitive data
    # Format: (pattern, replacement, flags)
    SENSITIVE_PATTERNS = [
        (r'password["\']?\s*[:=]\s*["\']?([^"\',\s]+)', r'password": "[REDACTED]"', 0),
        (r'token["\']?\s*[:=]\s*["\']?([^"\',\s]+)', r'token": "[REDACTED]"', 0),
        (r'api[_-]?key["\']?\s*[:=]\s*["\']?([^"\',\s]+)', r'api_key": "[REDACTED]"', 0),
        (r'secret["\']?\s*[:=]\s*["\']?([^"\',\s]+)', r'secret": "[REDACTED]"', 0),
        (r'authorization["\']?\s*[:=]\s*["\']?bearer\s+([^"\',\s]+)', r'authorization": "Bearer [REDACTED]"', re.IGNORECASE),
        (r'access[_-]?token["\']?\s*[:=]\s*["\']?([^"\',\s]+)', r'access_token": "[REDACTED]"', 0),
        (r'refresh[_-]?token["\']?\s*[:=]\s*["\']?([^"\',\s]+)', r'refresh_token": "[REDACTED]"', 0),
    ]
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Redact sensitive data from log message"""
        if hasattr(record, 'msg') and record.msg:
            msg = str(record.msg)
            for pattern, replacement, flags in self.SENSITIVE_PATTERNS:
                msg = re.sub(pattern, replacement, msg, flags=flags)
            record.msg = msg
        
        if hasattr(record, 'args') and record.args:
            args = list(record.args)
            for i, arg in enumerate(args):
                if isinstance(arg, str):
                    for pattern, replacement, flags in self.SENSITIVE_PATTERNS:
                        args[i] = re.sub(pattern, replacement, arg, flags=flags)
                elif isinstance(arg, dict):
                    args[i] = self._redact_dict(arg)
            record.args = tuple(args)
        
        return True
    
    def _redact_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively redact sensitive keys from dictionaries"""
        sensitive_keys = {
            'password', 'token', 'api_key', 'api-key', 'secret', 
            'access_token', 'refresh_token', 'authorization',
            'openai_api_key', 'companies_house_api_key', 'google_maps_api_key',
            'hashed_password', 'super_admin_password', 'super_admin_email'
        }
        
        redacted = {}
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                redacted[key] = '[REDACTED]'
            elif isinstance(value, dict):
                redacted[key] = self._redact_dict(value)
            elif isinstance(value, list):
                redacted[key] = [
                    self._redact_dict(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                redacted[key] = value
        return redacted


class StructuredFormatter(logging.Formatter):
    """
    JSON formatter for structured logging
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)
        
        return json.dumps(log_data, default=str)


def setup_logging(level: str = "INFO", enable_json: bool = False) -> None:
    """
    Configure application logging
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        enable_json: If True, use JSON formatting for structured logs
    """
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    
    # Add sensitive data filter
    console_handler.addFilter(SensitiveDataFilter())
    
    # Set formatter
    if enable_json:
        formatter = StructuredFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Set levels for noisy libraries
    logging.getLogger('uvicorn').setLevel(logging.WARNING)
    logging.getLogger('uvicorn.access').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def log_safe(message: str, logger: Optional[logging.Logger] = None, level: int = logging.INFO, **kwargs) -> None:
    """
    Log a message with automatic sensitive data redaction
    
    Args:
        message: Log message
        logger: Logger instance (if None, uses root logger)
        level: Log level
        **kwargs: Additional fields to include in log
    """
    if logger is None:
        logger = logging.getLogger()
    
    # Redact sensitive data from kwargs
    safe_kwargs = {}
    sensitive_keys = {'password', 'token', 'api_key', 'secret', 'authorization'}
    
    for key, value in kwargs.items():
        if any(sensitive in key.lower() for sensitive in sensitive_keys):
            safe_kwargs[key] = '[REDACTED]'
        else:
            safe_kwargs[key] = value
    
    logger.log(level, message, extra={'extra_fields': safe_kwargs})

