"""
Request validation middleware and utilities.

This module provides middleware for request validation including
body size limiting and input sanitization.

Requirements:
- 21.6: Sanitize string inputs to prevent injection attacks
- 21.7: Limit request body size to 10MB
"""

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
import re


# Maximum request body size (10MB)
MAX_REQUEST_BODY_SIZE = 10 * 1024 * 1024  # 10MB in bytes


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for request validation.
    
    Requirements:
    - 21.7: Limit request body size to 10MB
    - 21.8: Return validation errors in consistent JSON format
    """
    
    async def dispatch(self, request: Request, call_next: Callable):
        """
        Process request and enforce validation rules.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain
        
        Returns:
            Response from next handler
        
        Raises:
            HTTPException: If request body exceeds size limit
        """
        # Check Content-Length header if present
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                content_length = int(content_length)
                if content_length > MAX_REQUEST_BODY_SIZE:
                    from fastapi.responses import JSONResponse
                    return JSONResponse(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        content={
                            "error": "Request body too large",
                            "message": f"Request body size exceeds maximum allowed size of {MAX_REQUEST_BODY_SIZE / (1024 * 1024):.1f}MB",
                            "max_size_mb": MAX_REQUEST_BODY_SIZE / (1024 * 1024),
                            "received_size_mb": round(content_length / (1024 * 1024), 2)
                        }
                    )
            except ValueError:
                # Invalid Content-Length header, let it pass and fail later
                pass
        
        # Process request
        response = await call_next(request)
        return response


def sanitize_path_parameter(value: str) -> str:
    """
    Sanitize path parameters to prevent injection attacks.
    
    Requirements:
    - 21.6: Sanitize string inputs to prevent injection attacks
    
    Args:
        value: Path parameter value
    
    Returns:
        Sanitized value
    """
    if not value:
        return value
    
    # Remove potential SQL injection patterns
    dangerous_patterns = [
        r"(\bDROP\b|\bDELETE\b|\bINSERT\b|\bUPDATE\b|\bEXEC\b|\bEXECUTE\b)",
        r"(--|;|\/\*|\*\/|xp_|sp_)",
        r"(\bUNION\b.*\bSELECT\b)",
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, value, re.IGNORECASE):
            # Replace dangerous patterns with empty string
            value = re.sub(pattern, "", value, flags=re.IGNORECASE)
    
    # Remove control characters except newlines and tabs
    value = "".join(char for char in value if ord(char) >= 32 or char in ['\n', '\t'])
    
    return value.strip()


def validate_date_format(date_str: str) -> bool:
    """
    Validate date string format (ISO 8601).
    
    Args:
        date_str: Date string to validate
    
    Returns:
        True if valid, False otherwise
    """
    # ISO 8601 date format: YYYY-MM-DD
    pattern = r'^\d{4}-\d{2}-\d{2}$'
    return bool(re.match(pattern, date_str))


def validate_metric_name(metric_name: str) -> bool:
    """
    Validate metric name format.
    
    Args:
        metric_name: Metric name to validate
    
    Returns:
        True if valid, False otherwise
    """
    # Allow alphanumeric, underscore, and hyphen
    pattern = r'^[a-zA-Z0-9_-]+$'
    return bool(re.match(pattern, metric_name))


def validate_employee_id(employee_id: str) -> bool:
    """
    Validate employee ID format.
    
    Args:
        employee_id: Employee ID to validate
    
    Returns:
        True if valid, False otherwise
    """
    # Allow alphanumeric, underscore, and hyphen
    pattern = r'^[a-zA-Z0-9_-]+$'
    return bool(re.match(pattern, employee_id))
