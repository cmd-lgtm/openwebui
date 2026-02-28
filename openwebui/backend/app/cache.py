"""
Redis caching service for improved performance
"""
import json
import logging
from typing import Any, Optional
from functools import wraps
import hashlib

import redis.asyncio as redis
from redis.asyncio import Redis

from app.core.config import settings

logger = logging.getLogger(__name__)


class CacheService:
    """Redis-based caching service"""

    def __init__(self):
        self._redis: Optional[Redis] = None
        self._enabled = False

    async def connect(self):
        """Connect to Redis"""
        if not settings.REDIS_ENABLED:
            logger.info("Redis caching disabled")
            return

        try:
            self._redis = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            # Test connection
            await self._redis.ping()
            self._enabled = True
            logger.info(f"Redis connected: {settings.REDIS_URL}")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Caching disabled.")
            self._enabled = False
            self._redis = None

    async def disconnect(self):
        """Disconnect from Redis"""
        if self._redis:
            await self._redis.close()
            self._redis = None
            self._enabled = False

    @property
    def is_enabled(self) -> bool:
        """Check if caching is enabled"""
        return self._enabled and self._redis is not None

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.is_enabled:
            return None

        try:
            value = await self._redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.warning(f"Cache get error for key {key}: {e}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """Set value in cache with optional TTL (in seconds)"""
        if not self.is_enabled:
            return False

        try:
            serialized = json.dumps(value, default=str)
            if ttl:
                await self._redis.setex(key, ttl, serialized)
            else:
                await self._redis.set(key, serialized)
            return True
        except Exception as e:
            logger.warning(f"Cache set error for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete value from cache"""
        if not self.is_enabled:
            return False

        try:
            await self._redis.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Cache delete error for key {key}: {e}")
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern"""
        if not self.is_enabled:
            return 0

        try:
            keys = []
            async for key in self._redis.scan_iter(match=pattern):
                keys.append(key)

            if keys:
                return await self._redis.delete(*keys)
            return 0
        except Exception as e:
            logger.warning(f"Cache delete pattern error for {pattern}: {e}")
            return 0

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        if not self.is_enabled:
            return False

        try:
            return await self._redis.exists(key) > 0
        except Exception:
            return False

    async def get_or_set(
        self,
        key: str,
        fetcher: callable,
        ttl: Optional[int] = None
    ) -> Any:
        """
        Get from cache or fetch and cache.

        Args:
            key: Cache key
            fetcher: Async function to fetch data if not cached
            ttl: Time to live in seconds

        Returns:
            Cached or freshly fetched data
        """
        # Try to get from cache
        cached = await self.get(key)
        if cached is not None:
            logger.debug(f"Cache hit: {key}")
            return cached

        # Fetch fresh data
        logger.debug(f"Cache miss: {key}")
        data = await fetcher()

        # Cache the result
        if data is not None:
            await self.set(key, data, ttl)

        return data


def cache_key(*args, **kwargs) -> str:
    """Generate cache key from function arguments"""
    key_parts = [str(arg) for arg in args]
    key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
    key_hash = hashlib.md5("".join(key_parts).encode()).hexdigest()[:8]
    return key_hash


def cached(ttl: int = 300, key_prefix: str = "cache"):
    """
    Decorator for caching async function results.

    Args:
        ttl: Time to live in seconds (default: 5 minutes)
        key_prefix: Prefix for cache keys
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            key_parts = [key_prefix, func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
            cache_key_str = ":".join(key_parts)

            # Try cache first
            cache = cache_service
            cached_value = await cache.get(cache_key_str)
            if cached_value is not None:
                return cached_value

            # Call function
            result = await func(*args, **kwargs)

            # Cache result
            if result is not None:
                await cache.set(cache_key_str, result, ttl)

            return result
        return wrapper
    return decorator


# Global cache service instance
cache_service = CacheService()


async def init_cache():
    """Initialize cache service"""
    await cache_service.connect()


async def close_cache():
    """Close cache service"""
    await cache_service.disconnect()
