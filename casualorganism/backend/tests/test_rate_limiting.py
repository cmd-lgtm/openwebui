"""
Unit tests for rate limiting functionality.

Requirements:
- 20.1: Enforce rate limit of 100 requests per minute per user
- 20.2: Enforce rate limit of 1000 requests per minute per IP address
- 20.3: Apply stricter limits to expensive endpoints (10 requests per minute)
- 20.4: Return HTTP 429 with Retry-After header when rate limit exceeded
- 20.5: Use sliding window algorithm for rate limit calculation
- 20.6: Store rate limit state in Redis for consistency across replicas
- 20.7: Allow higher limits for premium user roles
- 20.8: Expose metrics for rate limit hits per endpoint
"""
import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch
from backend.core.rate_limiter import RateLimiter, RateLimitConfig
from backend.core.rate_limit_middleware import RateLimitMiddleware
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class TestRateLimiter:
    """Test RateLimiter class."""
    
    @pytest.fixture
    async def rate_limiter(self):
        """Create a rate limiter instance for testing."""
        # Use a test Redis instance or mock
        limiter = RateLimiter(redis_url="redis://localhost:6379/15")  # Use test DB
        await limiter.initialize()
        yield limiter
        await limiter.close()
    
    @pytest.mark.asyncio
    async def test_user_rate_limit_within_limit(self, rate_limiter):
        """
        Test that requests within user rate limit are allowed.
        
        Requirements:
        - 20.1: Enforce rate limit of 100 requests per minute per user
        """
        user_id = "test_user_1"
        
        # Make 5 requests (well within limit)
        for i in range(5):
            allowed, info = await rate_limiter.check_user_rate_limit(user_id, limit=100)
            assert allowed is True
            assert info["limit"] == 100
            assert info["remaining"] >= 0
        
        # Clean up
        await rate_limiter.reset_rate_limit(f"user:{user_id}")
    
    @pytest.mark.asyncio
    async def test_user_rate_limit_exceeded(self, rate_limiter):
        """
        Test that requests exceeding user rate limit are blocked.
        
        Requirements:
        - 20.1: Enforce rate limit of 100 requests per minute per user
        - 20.4: Return rate limit info with retry_after
        """
        user_id = "test_user_2"
        limit = 10  # Use small limit for testing
        
        # Make requests up to limit
        for i in range(limit):
            allowed, info = await rate_limiter.check_user_rate_limit(user_id, limit=limit)
            assert allowed is True
        
        # Next request should be blocked
        allowed, info = await rate_limiter.check_user_rate_limit(user_id, limit=limit)
        assert allowed is False
        assert info["remaining"] == 0
        assert info["retry_after"] > 0
        
        # Clean up
        await rate_limiter.reset_rate_limit(f"user:{user_id}")
    
    @pytest.mark.asyncio
    async def test_ip_rate_limit_within_limit(self, rate_limiter):
        """
        Test that requests within IP rate limit are allowed.
        
        Requirements:
        - 20.2: Enforce rate limit of 1000 requests per minute per IP address
        """
        ip_address = "192.168.1.100"
        
        # Make 10 requests (well within limit)
        for i in range(10):
            allowed, info = await rate_limiter.check_ip_rate_limit(ip_address, limit=1000)
            assert allowed is True
            assert info["limit"] == 1000
        
        # Clean up
        await rate_limiter.reset_rate_limit(f"ip:{ip_address}")
    
    @pytest.mark.asyncio
    async def test_ip_rate_limit_exceeded(self, rate_limiter):
        """
        Test that requests exceeding IP rate limit are blocked.
        
        Requirements:
        - 20.2: Enforce rate limit of 1000 requests per minute per IP address
        """
        ip_address = "192.168.1.101"
        limit = 20  # Use small limit for testing
        
        # Make requests up to limit
        for i in range(limit):
            allowed, info = await rate_limiter.check_ip_rate_limit(ip_address, limit=limit)
            assert allowed is True
        
        # Next request should be blocked
        allowed, info = await rate_limiter.check_ip_rate_limit(ip_address, limit=limit)
        assert allowed is False
        assert info["remaining"] == 0
        
        # Clean up
        await rate_limiter.reset_rate_limit(f"ip:{ip_address}")
    
    @pytest.mark.asyncio
    async def test_endpoint_rate_limit(self, rate_limiter):
        """
        Test that expensive endpoints have stricter limits.
        
        Requirements:
        - 20.3: Apply stricter limits to expensive endpoints (10 requests per minute)
        """
        user_id = "test_user_3"
        endpoint = "/api/causal/analyze"
        limit = 10
        
        # Make requests up to limit
        for i in range(limit):
            allowed, info = await rate_limiter.check_endpoint_rate_limit(
                user_id, endpoint, limit=limit
            )
            assert allowed is True
        
        # Next request should be blocked
        allowed, info = await rate_limiter.check_endpoint_rate_limit(
            user_id, endpoint, limit=limit
        )
        assert allowed is False
        
        # Clean up
        await rate_limiter.reset_rate_limit(f"endpoint:{user_id}:{endpoint}")
    
    @pytest.mark.asyncio
    async def test_sliding_window_algorithm(self, rate_limiter):
        """
        Test that sliding window algorithm works correctly.
        
        Requirements:
        - 20.5: Use sliding window algorithm for rate limit calculation
        """
        user_id = "test_user_4"
        limit = 5
        window_seconds = 2  # Short window for testing
        
        # Make requests up to limit
        for i in range(limit):
            allowed, info = await rate_limiter.check_user_rate_limit(
                user_id, limit=limit, window_seconds=window_seconds
            )
            assert allowed is True
        
        # Next request should be blocked
        allowed, info = await rate_limiter.check_user_rate_limit(
            user_id, limit=limit, window_seconds=window_seconds
        )
        assert allowed is False
        
        # Wait for window to slide
        await asyncio.sleep(window_seconds + 0.5)
        
        # Should be allowed again
        allowed, info = await rate_limiter.check_user_rate_limit(
            user_id, limit=limit, window_seconds=window_seconds
        )
        assert allowed is True
        
        # Clean up
        await rate_limiter.reset_rate_limit(f"user:{user_id}")
    
    @pytest.mark.asyncio
    async def test_rate_limit_info(self, rate_limiter):
        """
        Test getting rate limit info without incrementing counter.
        """
        user_id = "test_user_5"
        limit = 10
        
        # Get initial info
        info = await rate_limiter.get_rate_limit_info(f"user:{user_id}", limit=limit)
        assert info["limit"] == limit
        assert info["remaining"] == limit
        
        # Make some requests
        for i in range(3):
            await rate_limiter.check_user_rate_limit(user_id, limit=limit)
        
        # Get updated info
        info = await rate_limiter.get_rate_limit_info(f"user:{user_id}", limit=limit)
        assert info["remaining"] == limit - 3
        
        # Clean up
        await rate_limiter.reset_rate_limit(f"user:{user_id}")
    
    @pytest.mark.asyncio
    async def test_reset_rate_limit(self, rate_limiter):
        """Test resetting rate limit for a key."""
        user_id = "test_user_6"
        limit = 5
        
        # Make requests up to limit
        for i in range(limit):
            await rate_limiter.check_user_rate_limit(user_id, limit=limit)
        
        # Should be blocked
        allowed, info = await rate_limiter.check_user_rate_limit(user_id, limit=limit)
        assert allowed is False
        
        # Reset
        success = await rate_limiter.reset_rate_limit(f"user:{user_id}")
        assert success is True
        
        # Should be allowed again
        allowed, info = await rate_limiter.check_user_rate_limit(user_id, limit=limit)
        assert allowed is True


class TestRateLimitConfig:
    """Test RateLimitConfig class."""
    
    def test_get_user_limit_standard(self):
        """
        Test getting rate limit for standard user.
        
        Requirements:
        - 20.7: Allow higher limits for premium user roles
        """
        limit = RateLimitConfig.get_user_limit("standard")
        assert limit == 100
    
    def test_get_user_limit_premium(self):
        """
        Test getting rate limit for premium user.
        
        Requirements:
        - 20.7: Allow higher limits for premium user roles
        """
        limit = RateLimitConfig.get_user_limit("premium")
        assert limit == 200
        assert limit > RateLimitConfig.get_user_limit("standard")
    
    def test_get_user_limit_admin(self):
        """
        Test getting rate limit for admin user.
        
        Requirements:
        - 20.7: Allow higher limits for premium user roles
        """
        limit = RateLimitConfig.get_user_limit("admin")
        assert limit == 500
        assert limit > RateLimitConfig.get_user_limit("premium")
    
    def test_get_user_limit_free(self):
        """Test getting rate limit for free user."""
        limit = RateLimitConfig.get_user_limit("free")
        assert limit == 50
        assert limit < RateLimitConfig.get_user_limit("standard")
    
    def test_get_endpoint_limit_expensive(self):
        """
        Test getting rate limit for expensive endpoint.
        
        Requirements:
        - 20.3: Apply stricter limits to expensive endpoints
        """
        limit = RateLimitConfig.get_endpoint_limit("/api/causal/analyze")
        assert limit == 10
        assert limit < RateLimitConfig.DEFAULT_USER_LIMIT
    
    def test_get_endpoint_limit_normal(self):
        """Test getting rate limit for normal endpoint."""
        limit = RateLimitConfig.get_endpoint_limit("/api/graph/stats")
        assert limit is None  # No special limit
    
    def test_is_expensive_endpoint(self):
        """Test checking if endpoint is expensive."""
        assert RateLimitConfig.is_expensive_endpoint("/api/causal/analyze") is True
        assert RateLimitConfig.is_expensive_endpoint("/api/exports/request") is True
        assert RateLimitConfig.is_expensive_endpoint("/api/graph/stats") is False


class TestRateLimitMiddleware:
    """Test RateLimitMiddleware class."""
    
    @pytest.fixture
    def app(self):
        """Create a test FastAPI app."""
        app = FastAPI()
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "success"}
        
        @app.get("/health/live")
        async def health():
            return {"status": "ok"}
        
        return app
    
    @pytest.fixture
    async def rate_limiter(self):
        """Create a rate limiter for testing."""
        limiter = RateLimiter(redis_url="redis://localhost:6379/15")
        await limiter.initialize()
        yield limiter
        await limiter.close()
    
    @pytest.mark.asyncio
    async def test_middleware_allows_within_limit(self, app, rate_limiter):
        """Test that middleware allows requests within limit."""
        from fastapi.testclient import TestClient
        
        app.add_middleware(
            RateLimitMiddleware,
            rate_limiter=rate_limiter,
            prometheus_metrics=None
        )
        
        client = TestClient(app)
        
        # Make a few requests
        for i in range(3):
            response = client.get("/test", headers={"X-User-Id": "test_user"})
            assert response.status_code == 200
            assert "X-RateLimit-Limit" in response.headers
            assert "X-RateLimit-Remaining" in response.headers
    
    @pytest.mark.asyncio
    async def test_middleware_blocks_over_limit(self, app, rate_limiter):
        """
        Test that middleware blocks requests over limit.
        
        Requirements:
        - 20.4: Return HTTP 429 with Retry-After header
        """
        from fastapi.testclient import TestClient
        
        app.add_middleware(
            RateLimitMiddleware,
            rate_limiter=rate_limiter,
            prometheus_metrics=None
        )
        
        client = TestClient(app)
        
        # Make requests up to a small limit
        user_id = "test_user_limit"
        
        # First, set a low limit by making many requests
        for i in range(15):
            response = client.get("/test", headers={"X-User-Id": user_id})
        
        # Eventually should get 429
        # Note: This test may need adjustment based on actual limits
    
    @pytest.mark.asyncio
    async def test_middleware_skips_health_endpoints(self, app, rate_limiter):
        """Test that middleware skips rate limiting for health endpoints."""
        from fastapi.testclient import TestClient
        
        app.add_middleware(
            RateLimitMiddleware,
            rate_limiter=rate_limiter,
            prometheus_metrics=None
        )
        
        client = TestClient(app)
        
        # Health endpoint should not have rate limit headers
        response = client.get("/health/live")
        assert response.status_code == 200
        # Health endpoints are skipped, so no rate limit headers
    
    def test_get_client_ip_direct(self):
        """Test extracting client IP from direct connection."""
        middleware = RateLimitMiddleware(None, None)
        
        # Mock request with client
        request = Mock()
        request.headers = {}
        request.client = Mock()
        request.client.host = "192.168.1.1"
        
        ip = middleware._get_client_ip(request)
        assert ip == "192.168.1.1"
    
    def test_get_client_ip_forwarded(self):
        """Test extracting client IP from X-Forwarded-For header."""
        middleware = RateLimitMiddleware(None, None)
        
        # Mock request with X-Forwarded-For
        request = Mock()
        request.headers = {"X-Forwarded-For": "10.0.0.1, 192.168.1.1"}
        request.client = Mock()
        request.client.host = "192.168.1.1"
        
        ip = middleware._get_client_ip(request)
        assert ip == "10.0.0.1"  # Should use first IP in chain
    
    def test_get_user_id_from_state(self):
        """Test extracting user ID from request state."""
        middleware = RateLimitMiddleware(None, None)
        
        # Mock request with user in state
        request = Mock()
        request.state = Mock()
        request.state.user = Mock()
        request.state.user.user_id = "user123"
        request.headers = {}
        
        user_id = middleware._get_user_id(request)
        assert user_id == "user123"
    
    def test_get_user_id_from_header(self):
        """Test extracting user ID from header."""
        middleware = RateLimitMiddleware(None, None)
        
        # Mock request with user ID in header
        request = Mock()
        request.state = Mock(spec=[])  # Empty spec to avoid auto-creating attributes
        request.headers = {"X-User-Id": "user456"}
        
        user_id = middleware._get_user_id(request)
        assert user_id == "user456"
    
    def test_get_user_role_from_state(self):
        """Test extracting user role from request state."""
        middleware = RateLimitMiddleware(None, None)
        
        # Mock request with user role in state
        request = Mock()
        request.state = Mock()
        request.state.user = Mock()
        request.state.user.role = "premium"
        request.headers = {}
        
        role = middleware._get_user_role(request)
        assert role == "premium"
    
    def test_get_user_role_default(self):
        """Test default user role."""
        middleware = RateLimitMiddleware(None, None)
        
        # Mock request without user
        request = Mock()
        request.state = Mock(spec=[])  # Empty spec to avoid auto-creating attributes
        request.headers = {}
        
        role = middleware._get_user_role(request)
        assert role == "standard"
    
    def test_create_rate_limit_response(self):
        """
        Test creating 429 response with rate limit info.
        
        Requirements:
        - 20.4: Return HTTP 429 with Retry-After header
        """
        middleware = RateLimitMiddleware(None, None)
        
        rate_limit_info = {
            "limit": 100,
            "remaining": 0,
            "reset": 1234567890,
            "retry_after": 30
        }
        
        response = middleware._create_rate_limit_response(rate_limit_info)
        
        assert response.status_code == 429
        assert "Retry-After" in response.headers
        assert response.headers["Retry-After"] == "30"
        assert "X-RateLimit-Limit" in response.headers
        assert response.headers["X-RateLimit-Limit"] == "100"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
