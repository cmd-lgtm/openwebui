"""
Rate Limiting Middleware for FastAPI.

Requirements:
- 20.1: Enforce rate limit of 100 requests per minute per user
- 20.2: Enforce rate limit of 1000 requests per minute per IP address
- 20.3: Apply stricter limits to expensive endpoints (10 requests per minute)
- 20.4: Return HTTP 429 with Retry-After header when rate limit exceeded
- 20.7: Allow higher limits for premium user roles
- 20.8: Expose metrics for rate limit hits per endpoint
"""
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional
import time

from backend.core.rate_limiter import RateLimiter, RateLimitConfig


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce rate limiting on API requests.
    
    Applies per-user and per-IP limits with different limits for different endpoints
    and higher limits for premium roles.
    """
    
    def __init__(self, app, rate_limiter: RateLimiter, prometheus_metrics=None):
        """
        Initialize rate limiting middleware.
        
        Args:
            app: FastAPI application
            rate_limiter: RateLimiter instance
            prometheus_metrics: PrometheusMetrics instance for tracking rate limit hits
        """
        super().__init__(app)
        self.rate_limiter = rate_limiter
        self.prometheus_metrics = prometheus_metrics
        
        # Endpoints that should skip rate limiting
        self.skip_endpoints = {
            "/health/live",
            "/health/ready",
            "/metrics",
            "/docs",
            "/openapi.json",
            "/redoc",
        }
    
    async def dispatch(self, request: Request, call_next):
        """
        Process request with rate limiting.
        
        Requirements:
        - 20.1: Enforce rate limit per user
        - 20.2: Enforce rate limit per IP
        - 20.3: Apply stricter limits to expensive endpoints
        - 20.4: Return HTTP 429 with Retry-After header
        - 20.7: Allow higher limits for premium user roles
        - 20.8: Expose metrics for rate limit hits
        """
        # Skip rate limiting for certain endpoints
        if request.url.path in self.skip_endpoints:
            return await call_next(request)
        
        # Get client IP address
        client_ip = self._get_client_ip(request)
        
        # Get user ID and role from request (if authenticated)
        user_id = self._get_user_id(request)
        user_role = self._get_user_role(request)
        
        # Check IP-based rate limit first (broader protection)
        ip_allowed, ip_info = await self.rate_limiter.check_ip_rate_limit(
            ip_address=client_ip,
            limit=RateLimitConfig.DEFAULT_IP_LIMIT
        )
        
        if not ip_allowed:
            # Track rate limit hit in metrics
            if self.prometheus_metrics:
                self.prometheus_metrics.increment_rate_limit_hits(
                    endpoint=request.url.path,
                    limit_type="ip"
                )
            
            return self._create_rate_limit_response(ip_info)
        
        # Check user-based rate limit (if authenticated)
        if user_id:
            # Get user's rate limit based on role
            user_limit = RateLimitConfig.get_user_limit(user_role)
            
            # Check if endpoint is expensive and requires stricter limit
            endpoint_limit = RateLimitConfig.get_endpoint_limit(request.url.path)
            
            if endpoint_limit is not None:
                # Apply endpoint-specific limit
                endpoint_allowed, endpoint_info = await self.rate_limiter.check_endpoint_rate_limit(
                    user_id=user_id,
                    endpoint=request.url.path,
                    limit=endpoint_limit
                )
                
                if not endpoint_allowed:
                    # Track rate limit hit in metrics
                    if self.prometheus_metrics:
                        self.prometheus_metrics.increment_rate_limit_hits(
                            endpoint=request.url.path,
                            limit_type="endpoint"
                        )
                    
                    return self._create_rate_limit_response(endpoint_info)
            
            # Check general user rate limit
            user_allowed, user_info = await self.rate_limiter.check_user_rate_limit(
                user_id=user_id,
                limit=user_limit
            )
            
            if not user_allowed:
                # Track rate limit hit in metrics
                if self.prometheus_metrics:
                    self.prometheus_metrics.increment_rate_limit_hits(
                        endpoint=request.url.path,
                        limit_type="user"
                    )
                
                return self._create_rate_limit_response(user_info)
            
            # Add rate limit headers to response
            response = await call_next(request)
            self._add_rate_limit_headers(response, user_info)
            return response
        else:
            # Unauthenticated request - only IP limit applies
            response = await call_next(request)
            self._add_rate_limit_headers(response, ip_info)
            return response
    
    def _get_client_ip(self, request: Request) -> str:
        """
        Extract client IP address from request.
        
        Checks X-Forwarded-For header first (for proxied requests),
        then falls back to direct client IP.
        
        Args:
            request: FastAPI request
        
        Returns:
            Client IP address
        """
        # Check X-Forwarded-For header (for requests behind proxy/load balancer)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take first IP in the chain
            return forwarded_for.split(",")[0].strip()
        
        # Fall back to direct client IP
        if request.client:
            return request.client.host
        
        return "unknown"
    
    def _get_user_id(self, request: Request) -> Optional[str]:
        """
        Extract user ID from request state (set by auth middleware).
        
        Args:
            request: FastAPI request
        
        Returns:
            User ID if authenticated, None otherwise
        """
        # Check if user is authenticated (set by auth dependency)
        if hasattr(request.state, "user"):
            user = request.state.user
            if hasattr(user, "user_id"):
                return user.user_id
            elif isinstance(user, dict):
                return user.get("user_id")
        
        # Try to get from custom header (for testing)
        return request.headers.get("X-User-Id")
    
    def _get_user_role(self, request: Request) -> str:
        """
        Extract user role from request state (set by auth middleware).
        
        Args:
            request: FastAPI request
        
        Returns:
            User role (defaults to "standard")
        """
        # Check if user is authenticated
        if hasattr(request.state, "user"):
            user = request.state.user
            if hasattr(user, "role"):
                return user.role
            elif isinstance(user, dict):
                return user.get("role", "standard")
        
        # Try to get from custom header (for testing)
        role = request.headers.get("X-User-Role")
        return role if role else "standard"
    
    def _create_rate_limit_response(self, rate_limit_info: dict) -> JSONResponse:
        """
        Create HTTP 429 response with rate limit information.
        
        Requirements:
        - 20.4: Return HTTP 429 with Retry-After header
        
        Args:
            rate_limit_info: Rate limit information dictionary
        
        Returns:
            JSONResponse with 429 status code
        """
        headers = {
            "X-RateLimit-Limit": str(rate_limit_info["limit"]),
            "X-RateLimit-Remaining": str(rate_limit_info["remaining"]),
            "X-RateLimit-Reset": str(rate_limit_info["reset"]),
            "Retry-After": str(rate_limit_info["retry_after"])
        }
        
        return JSONResponse(
            status_code=429,
            content={
                "error": "Rate limit exceeded",
                "message": f"Too many requests. Please retry after {rate_limit_info['retry_after']} seconds.",
                "limit": rate_limit_info["limit"],
                "remaining": rate_limit_info["remaining"],
                "reset": rate_limit_info["reset"],
                "retry_after": rate_limit_info["retry_after"]
            },
            headers=headers
        )
    
    def _add_rate_limit_headers(self, response: Response, rate_limit_info: dict):
        """
        Add rate limit information to response headers.
        
        Requirements:
        - 20.4: Include rate limit info in headers
        
        Args:
            response: FastAPI response
            rate_limit_info: Rate limit information dictionary
        """
        response.headers["X-RateLimit-Limit"] = str(rate_limit_info["limit"])
        response.headers["X-RateLimit-Remaining"] = str(rate_limit_info["remaining"])
        response.headers["X-RateLimit-Reset"] = str(rate_limit_info["reset"])


def setup_rate_limiting(app, redis_url: str, prometheus_metrics=None) -> RateLimiter:
    """
    Setup rate limiting for FastAPI application.
    
    Args:
        app: FastAPI application
        redis_url: Redis connection URL
        prometheus_metrics: PrometheusMetrics instance
    
    Returns:
        RateLimiter instance
    """
    rate_limiter = RateLimiter(redis_url=redis_url)
    
    # Add middleware
    app.add_middleware(
        RateLimitMiddleware,
        rate_limiter=rate_limiter,
        prometheus_metrics=prometheus_metrics
    )
    
    return rate_limiter
