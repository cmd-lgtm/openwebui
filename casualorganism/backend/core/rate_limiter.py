"""
Rate Limiter using Redis with sliding window algorithm.

Requirements:
- 20.1: Enforce rate limit of 100 requests per minute per user
- 20.2: Enforce rate limit of 1000 requests per minute per IP address
- 20.5: Use sliding window algorithm for rate limit calculation
- 20.6: Store rate limit state in Cache_Layer for consistency across replicas
"""
from typing import Optional, Tuple
import time
import redis.asyncio as redis
from redis.asyncio import ConnectionPool


class RateLimiter:
    """
    Rate limiter using Redis with sliding window algorithm.
    
    The sliding window algorithm provides more accurate rate limiting than
    fixed windows by considering the timestamp of each request.
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        """
        Initialize rate limiter with Redis connection.
        
        Args:
            redis_url: Redis connection URL
        """
        self.redis_url = redis_url
        self.pool: Optional[ConnectionPool] = None
        self.client: Optional[redis.Redis] = None
    
    async def initialize(self) -> bool:
        """Initialize Redis connection pool."""
        try:
            self.pool = ConnectionPool.from_url(
                self.redis_url,
                max_connections=50,
                socket_timeout=2.0,
                decode_responses=True
            )
            self.client = redis.Redis(connection_pool=self.pool)
            # Test connection
            await self.client.ping()
            return True
        except Exception as e:
            print(f"Rate limiter Redis initialization failed: {e}")
            return False
    
    async def check_rate_limit(
        self,
        key: str,
        limit: int,
        window_seconds: int = 60
    ) -> Tuple[bool, dict]:
        """
        Check if request is within rate limit using sliding window algorithm.
        
        Requirements:
        - 20.5: Use sliding window algorithm for rate limit calculation
        - 20.6: Store rate limit state in Redis for consistency across replicas
        
        Args:
            key: Unique identifier for rate limit (e.g., "user:123" or "ip:192.168.1.1")
            limit: Maximum number of requests allowed in window
            window_seconds: Time window in seconds (default: 60 for per-minute limits)
        
        Returns:
            Tuple of (allowed: bool, info: dict)
            - allowed: True if request is within limit, False otherwise
            - info: Dictionary with rate limit information:
                - limit: Maximum requests allowed
                - remaining: Requests remaining in current window
                - reset: Unix timestamp when limit resets
                - retry_after: Seconds to wait before retrying (if limit exceeded)
        """
        if not self.client:
            raise RuntimeError("Rate limiter not initialized")
        
        current_time = time.time()
        window_start = current_time - window_seconds
        
        # Redis key for this rate limit
        redis_key = f"ratelimit:{key}"
        
        # Use Redis pipeline for atomic operations
        pipe = self.client.pipeline()
        
        try:
            # Remove old entries outside the sliding window
            pipe.zremrangebyscore(redis_key, 0, window_start)
            
            # Count requests in current window
            pipe.zcard(redis_key)
            
            # Execute pipeline
            results = await pipe.execute()
            current_count = results[1]
            
            # Check if limit exceeded
            if current_count >= limit:
                # Get oldest request timestamp to calculate retry_after
                oldest_requests = await self.client.zrange(
                    redis_key, 0, 0, withscores=True
                )
                
                if oldest_requests:
                    oldest_timestamp = oldest_requests[0][1]
                    retry_after = int(oldest_timestamp + window_seconds - current_time) + 1
                else:
                    retry_after = window_seconds
                
                return False, {
                    "limit": limit,
                    "remaining": 0,
                    "reset": int(current_time + window_seconds),
                    "retry_after": retry_after
                }
            
            # Add current request to sorted set
            await self.client.zadd(redis_key, {str(current_time): current_time})
            
            # Set expiry on key (cleanup)
            await self.client.expire(redis_key, window_seconds + 10)
            
            # Calculate remaining requests
            remaining = limit - current_count - 1
            
            return True, {
                "limit": limit,
                "remaining": remaining,
                "reset": int(current_time + window_seconds),
                "retry_after": 0
            }
        
        except Exception as e:
            print(f"Rate limit check failed: {e}")
            # Fail open - allow request if Redis is unavailable
            return True, {
                "limit": limit,
                "remaining": limit,
                "reset": int(current_time + window_seconds),
                "retry_after": 0
            }
    
    async def check_user_rate_limit(
        self,
        user_id: str,
        limit: int = 100,
        window_seconds: int = 60
    ) -> Tuple[bool, dict]:
        """
        Check rate limit for a specific user.
        
        Requirements:
        - 20.1: Enforce rate limit of 100 requests per minute per user
        
        Args:
            user_id: User identifier
            limit: Maximum requests per window (default: 100)
            window_seconds: Time window in seconds (default: 60)
        
        Returns:
            Tuple of (allowed: bool, info: dict)
        """
        return await self.check_rate_limit(
            key=f"user:{user_id}",
            limit=limit,
            window_seconds=window_seconds
        )
    
    async def check_ip_rate_limit(
        self,
        ip_address: str,
        limit: int = 1000,
        window_seconds: int = 60
    ) -> Tuple[bool, dict]:
        """
        Check rate limit for a specific IP address.
        
        Requirements:
        - 20.2: Enforce rate limit of 1000 requests per minute per IP address
        
        Args:
            ip_address: IP address
            limit: Maximum requests per window (default: 1000)
            window_seconds: Time window in seconds (default: 60)
        
        Returns:
            Tuple of (allowed: bool, info: dict)
        """
        return await self.check_rate_limit(
            key=f"ip:{ip_address}",
            limit=limit,
            window_seconds=window_seconds
        )
    
    async def check_endpoint_rate_limit(
        self,
        user_id: str,
        endpoint: str,
        limit: int = 10,
        window_seconds: int = 60
    ) -> Tuple[bool, dict]:
        """
        Check rate limit for a specific endpoint per user.
        
        Requirements:
        - 20.3: Apply stricter limits to expensive endpoints (10 requests per minute)
        
        Args:
            user_id: User identifier
            endpoint: Endpoint path
            limit: Maximum requests per window (default: 10 for expensive endpoints)
            window_seconds: Time window in seconds (default: 60)
        
        Returns:
            Tuple of (allowed: bool, info: dict)
        """
        return await self.check_rate_limit(
            key=f"endpoint:{user_id}:{endpoint}",
            limit=limit,
            window_seconds=window_seconds
        )
    
    async def get_rate_limit_info(
        self,
        key: str,
        limit: int,
        window_seconds: int = 60
    ) -> dict:
        """
        Get current rate limit information without incrementing counter.
        
        Args:
            key: Unique identifier for rate limit
            limit: Maximum number of requests allowed in window
            window_seconds: Time window in seconds
        
        Returns:
            Dictionary with rate limit information
        """
        if not self.client:
            raise RuntimeError("Rate limiter not initialized")
        
        current_time = time.time()
        window_start = current_time - window_seconds
        
        redis_key = f"ratelimit:{key}"
        
        try:
            # Remove old entries
            await self.client.zremrangebyscore(redis_key, 0, window_start)
            
            # Count current requests
            current_count = await self.client.zcard(redis_key)
            
            remaining = max(0, limit - current_count)
            
            return {
                "limit": limit,
                "remaining": remaining,
                "reset": int(current_time + window_seconds),
                "retry_after": 0
            }
        except Exception as e:
            print(f"Failed to get rate limit info: {e}")
            return {
                "limit": limit,
                "remaining": limit,
                "reset": int(current_time + window_seconds),
                "retry_after": 0
            }
    
    async def reset_rate_limit(self, key: str) -> bool:
        """
        Reset rate limit for a specific key (admin function).
        
        Args:
            key: Unique identifier for rate limit
        
        Returns:
            True if reset successful, False otherwise
        """
        if not self.client:
            raise RuntimeError("Rate limiter not initialized")
        
        try:
            redis_key = f"ratelimit:{key}"
            await self.client.delete(redis_key)
            return True
        except Exception as e:
            print(f"Failed to reset rate limit: {e}")
            return False
    
    async def close(self):
        """Close Redis connection."""
        if self.client:
            await self.client.close()
        if self.pool:
            await self.pool.disconnect()


class RateLimitConfig:
    """
    Configuration for rate limits by endpoint and role.
    
    Requirements:
    - 20.3: Apply stricter limits to expensive endpoints
    - 20.7: Allow higher limits for premium user roles
    """
    
    # Default limits
    DEFAULT_USER_LIMIT = 100  # requests per minute
    DEFAULT_IP_LIMIT = 1000   # requests per minute
    
    # Expensive endpoints with stricter limits
    EXPENSIVE_ENDPOINTS = {
        "/api/causal/analyze": 10,
        "/api/exports/request": 5,
        "/api/graph/employee_metrics": 20,
    }
    
    # Role-based limits (higher limits for premium roles)
    ROLE_LIMITS = {
        "admin": 500,      # 5x normal limit
        "premium": 200,    # 2x normal limit
        "standard": 100,   # normal limit
        "free": 50,        # 0.5x normal limit
    }
    
    @classmethod
    def get_user_limit(cls, role: str = "standard") -> int:
        """
        Get rate limit for user based on role.
        
        Requirements:
        - 20.7: Allow higher limits for premium user roles
        
        Args:
            role: User role (admin, premium, standard, free)
        
        Returns:
            Rate limit for the role
        """
        return cls.ROLE_LIMITS.get(role, cls.DEFAULT_USER_LIMIT)
    
    @classmethod
    def get_endpoint_limit(cls, endpoint: str) -> Optional[int]:
        """
        Get rate limit for specific endpoint if it's expensive.
        
        Requirements:
        - 20.3: Apply stricter limits to expensive endpoints
        
        Args:
            endpoint: Endpoint path
        
        Returns:
            Rate limit for endpoint, or None if not expensive
        """
        return cls.EXPENSIVE_ENDPOINTS.get(endpoint)
    
    @classmethod
    def is_expensive_endpoint(cls, endpoint: str) -> bool:
        """
        Check if endpoint is classified as expensive.
        
        Args:
            endpoint: Endpoint path
        
        Returns:
            True if endpoint is expensive, False otherwise
        """
        return endpoint in cls.EXPENSIVE_ENDPOINTS
