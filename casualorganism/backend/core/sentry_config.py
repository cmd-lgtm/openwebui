"""
Sentry Error Aggregation Configuration

This module provides Sentry integration for error tracking and aggregation.

Requirements:
- 17.1: Send all unhandled exceptions to error tracking service
- 17.2: Enable automatic error capture
- 17.4: Include request context, user context, and stack traces
"""

import os
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from typing import Optional, Dict, Any


def setup_sentry(
    dsn: Optional[str] = None,
    environment: Optional[str] = None,
    traces_sample_rate: float = 0.1,
    profiles_sample_rate: float = 0.1,
    enable_tracing: bool = True
) -> bool:
    """
    Initialize Sentry SDK with FastAPI and Celery integrations.
    
    Requirements:
    - 17.1: Configure DSN and environment
    - 17.2: Enable automatic error capture
    - 17.4: Include stack traces
    
    Args:
        dsn: Sentry DSN (Data Source Name). If None, reads from SENTRY_DSN env var
        environment: Environment name (dev, staging, prod). If None, reads from SENTRY_ENVIRONMENT
        traces_sample_rate: Percentage of transactions to trace (0.0 to 1.0)
        profiles_sample_rate: Percentage of transactions to profile (0.0 to 1.0)
        enable_tracing: Whether to enable performance tracing
    
    Returns:
        bool: True if Sentry was initialized, False if DSN not provided
    """
    # Get DSN from parameter or environment
    sentry_dsn = dsn or os.getenv("SENTRY_DSN")
    
    if not sentry_dsn:
        print("Warning: SENTRY_DSN not configured. Error tracking disabled.")
        return False
    
    # Get environment from parameter or environment variable
    sentry_env = environment or os.getenv("SENTRY_ENVIRONMENT", "development")
    
    # Initialize Sentry with integrations
    sentry_sdk.init(
        dsn=sentry_dsn,
        environment=sentry_env,
        
        # Integrations for automatic instrumentation
        integrations=[
            FastApiIntegration(
                transaction_style="endpoint",  # Group by endpoint path
                failed_request_status_codes={500, 501, 502, 503, 504, 505, 506, 507, 508, 509, 510, 511, 599}  # 5xx errors
            ),
            CeleryIntegration(
                monitor_beat_tasks=True,  # Monitor Celery Beat scheduled tasks
                exclude_beat_tasks=[]  # Don't exclude any tasks
            ),
            RedisIntegration()
        ],
        
        # Performance monitoring
        traces_sample_rate=traces_sample_rate if enable_tracing else 0.0,
        profiles_sample_rate=profiles_sample_rate if enable_tracing else 0.0,
        
        # Error sampling (capture all errors)
        sample_rate=1.0,
        
        # Send default PII (Personally Identifiable Information)
        # Set to False in production if needed for privacy compliance
        send_default_pii=False,
        
        # Attach stack traces to messages
        attach_stacktrace=True,
        
        # Maximum breadcrumbs to capture
        max_breadcrumbs=50,
        
        # Release tracking (optional - can be set via SENTRY_RELEASE env var)
        release=os.getenv("SENTRY_RELEASE"),
        
        # Additional options
        debug=os.getenv("SENTRY_DEBUG", "false").lower() == "true",
        
        # Before send hook for custom filtering/enrichment
        before_send=before_send_hook,
        
        # Before breadcrumb hook for filtering breadcrumbs
        before_breadcrumb=before_breadcrumb_hook
    )
    
    print(f"Sentry initialized for environment: {sentry_env}")
    return True


def before_send_hook(event: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Hook called before sending event to Sentry.
    Can be used to filter, modify, or enrich events.
    
    Requirements:
    - 17.3: Custom event processing for grouping and deduplication
    - 17.4: Enrich error context
    
    Args:
        event: Sentry event dictionary
        hint: Additional context about the event
    
    Returns:
        Modified event or None to drop the event
    """
    # Example: Filter out specific errors
    if 'exc_info' in hint:
        exc_type, exc_value, tb = hint['exc_info']
        
        # Don't send certain expected errors
        if isinstance(exc_value, (KeyboardInterrupt, SystemExit)):
            return None
    
    # Custom fingerprinting for better grouping
    # Requirement 17.3: Use Sentry's automatic grouping with custom fingerprinting
    
    # Get exception information
    exception_type = None
    exception_message = None
    if 'exception' in event and 'values' in event['exception']:
        if event['exception']['values']:
            exc = event['exception']['values'][0]
            exception_type = exc.get('type')
            exception_message = exc.get('value', '')
    
    # Custom fingerprinting based on endpoint and error type
    if 'request' in event:
        request = event['request']
        url = request.get('url', '')
        
        # Group export errors by type
        if '/api/exports/' in url:
            event['fingerprint'] = ['export-error', exception_type or 'unknown']
        
        # Group trend query errors by type
        elif '/api/trends/' in url:
            event['fingerprint'] = ['trends-error', exception_type or 'unknown']
        
        # Group intervention errors by type
        elif '/api/interventions/' in url:
            event['fingerprint'] = ['intervention-error', exception_type or 'unknown']
        
        # Group causal analysis errors by type
        elif '/api/causal/' in url:
            event['fingerprint'] = ['causal-analysis-error', exception_type or 'unknown']
        
        # Group database connection errors
        elif exception_type in ['ConnectionError', 'TimeoutError', 'OperationalError']:
            # Extract database type from error message
            db_type = 'unknown'
            if 'neo4j' in exception_message.lower():
                db_type = 'neo4j'
            elif 'redis' in exception_message.lower():
                db_type = 'redis'
            elif 'timescale' in exception_message.lower() or 'postgres' in exception_message.lower():
                db_type = 'timescale'
            
            event['fingerprint'] = ['database-connection-error', db_type, exception_type]
        
        # Group validation errors by endpoint
        elif exception_type == 'ValidationError':
            endpoint = request.get('url', '').split('?')[0]  # Remove query params
            event['fingerprint'] = ['validation-error', endpoint]
        
        # Default: use Sentry's automatic grouping
        else:
            event['fingerprint'] = ['{{ default }}']
    
    # Add custom tags for better filtering
    if exception_type:
        event.setdefault('tags', {})['exception_type'] = exception_type
    
    # Add environment-specific context
    event.setdefault('tags', {})['service'] = 'api-service'
    
    return event


def before_breadcrumb_hook(crumb: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Hook called before adding breadcrumb.
    Can be used to filter or modify breadcrumbs.
    
    Args:
        crumb: Breadcrumb dictionary
        hint: Additional context
    
    Returns:
        Modified breadcrumb or None to drop it
    """
    # Filter out noisy breadcrumbs
    if crumb.get('category') == 'httplib':
        # Don't log health check requests
        if crumb.get('data', {}).get('url', '').endswith('/health'):
            return None
    
    return crumb


def set_user_context(user_id: str, email: Optional[str] = None, username: Optional[str] = None):
    """
    Set user context for error tracking.
    
    Requirements:
    - 17.4: Include user context in errors
    
    Args:
        user_id: User identifier
        email: User email (optional)
        username: Username (optional)
    """
    sentry_sdk.set_user({
        "id": user_id,
        "email": email,
        "username": username
    })


def set_request_context(request_id: str, endpoint: str, method: str):
    """
    Set request context for error tracking.
    
    Requirements:
    - 17.4: Include request context in errors
    
    Args:
        request_id: Unique request identifier
        endpoint: API endpoint path
        method: HTTP method
    """
    sentry_sdk.set_context("request", {
        "request_id": request_id,
        "endpoint": endpoint,
        "method": method
    })


def add_breadcrumb(message: str, category: str, level: str = "info", data: Optional[Dict] = None):
    """
    Add a breadcrumb for debugging context.
    
    Args:
        message: Breadcrumb message
        category: Category (e.g., "database", "cache", "api")
        level: Severity level (debug, info, warning, error)
        data: Additional data dictionary
    """
    sentry_sdk.add_breadcrumb(
        message=message,
        category=category,
        level=level,
        data=data or {}
    )


def capture_exception(error: Exception, **kwargs):
    """
    Manually capture an exception.
    
    Requirements:
    - 17.1: Send exceptions to error tracking service
    
    Args:
        error: Exception to capture
        **kwargs: Additional context (tags, extras, etc.)
    """
    with sentry_sdk.push_scope() as scope:
        # Add any additional context
        for key, value in kwargs.items():
            if key == "tags":
                for tag_key, tag_value in value.items():
                    scope.set_tag(tag_key, tag_value)
            elif key == "extra":
                for extra_key, extra_value in value.items():
                    scope.set_extra(extra_key, extra_value)
            elif key == "level":
                scope.level = value
        
        sentry_sdk.capture_exception(error)


def capture_message(message: str, level: str = "info", **kwargs):
    """
    Capture a message (non-exception event).
    
    Args:
        message: Message to capture
        level: Severity level (debug, info, warning, error, fatal)
        **kwargs: Additional context
    """
    with sentry_sdk.push_scope() as scope:
        for key, value in kwargs.items():
            if key == "tags":
                for tag_key, tag_value in value.items():
                    scope.set_tag(tag_key, tag_value)
            elif key == "extra":
                for extra_key, extra_value in value.items():
                    scope.set_extra(extra_key, extra_value)
        
        sentry_sdk.capture_message(message, level=level)


def get_sentry_stats() -> Dict[str, Any]:
    """
    Get Sentry configuration status.
    
    Requirements:
    - 17.8: Expose API for querying error statistics
    
    Returns:
        Dictionary with Sentry configuration status
    """
    client = sentry_sdk.Hub.current.client
    
    if not client:
        return {
            "enabled": False,
            "dsn_configured": False
        }
    
    return {
        "enabled": True,
        "dsn_configured": True,
        "environment": client.options.get("environment"),
        "release": client.options.get("release"),
        "sample_rate": client.options.get("sample_rate"),
        "traces_sample_rate": client.options.get("traces_sample_rate")
    }
