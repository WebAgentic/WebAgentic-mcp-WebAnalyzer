"""Caching utilities using Redis."""

import json
import pickle
from typing import Any, Optional, Union, Callable
from functools import wraps
import hashlib
import asyncio
import redis.asyncio as redis
from ..config import get_settings

settings = get_settings()


class CacheManager:
    """Redis-based cache manager."""
    
    def __init__(self):
        self._redis: Optional[redis.Redis] = None
    
    async def get_redis(self) -> redis.Redis:
        """Get Redis connection."""
        if self._redis is None:
            connection_kwargs = {
                "max_connections": settings.redis_max_connections,
                "decode_responses": False  # We'll handle encoding manually
            }
            
            if settings.redis_password:
                connection_kwargs["password"] = settings.redis_password
                
            self._redis = redis.from_url(
                settings.redis_url,
                **connection_kwargs
            )
        return self._redis
    
    async def close(self):
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
    
    def _make_key(self, prefix: str, key: str) -> str:
        """Create cache key with prefix."""
        return f"{settings.app_name}:{prefix}:{key}"
    
    async def get(self, key: str, prefix: str = "cache") -> Optional[Any]:
        """Get value from cache."""
        try:
            redis_client = await self.get_redis()
            cache_key = self._make_key(prefix, key)
            
            value = await redis_client.get(cache_key)
            if value is None:
                return None
            
            # Try to deserialize as JSON first, then pickle
            try:
                return json.loads(value.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                return pickle.loads(value)
                
        except Exception as e:
            print(f"Cache get error: {e}")
            return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None, 
        prefix: str = "cache"
    ) -> bool:
        """Set value in cache."""
        try:
            redis_client = await self.get_redis()
            cache_key = self._make_key(prefix, key)
            
            # Try to serialize as JSON first, then pickle
            try:
                serialized = json.dumps(value, default=str)
            except (TypeError, ValueError):
                serialized = pickle.dumps(value)
            
            ttl = ttl or settings.cache_ttl
            await redis_client.setex(cache_key, ttl, serialized)
            return True
            
        except Exception as e:
            print(f"Cache set error: {e}")
            return False
    
    async def delete(self, key: str, prefix: str = "cache") -> bool:
        """Delete value from cache."""
        try:
            redis_client = await self.get_redis()
            cache_key = self._make_key(prefix, key)
            result = await redis_client.delete(cache_key)
            return result > 0
        except Exception as e:
            print(f"Cache delete error: {e}")
            return False
    
    async def exists(self, key: str, prefix: str = "cache") -> bool:
        """Check if key exists in cache."""
        try:
            redis_client = await self.get_redis()
            cache_key = self._make_key(prefix, key)
            return await redis_client.exists(cache_key) > 0
        except Exception as e:
            print(f"Cache exists error: {e}")
            return False
    
    async def clear_prefix(self, prefix: str) -> int:
        """Clear all keys with given prefix."""
        try:
            redis_client = await self.get_redis()
            pattern = self._make_key(prefix, "*")
            keys = await redis_client.keys(pattern)
            if keys:
                return await redis_client.delete(*keys)
            return 0
        except Exception as e:
            print(f"Cache clear error: {e}")
            return 0


# Global cache manager instance
cache_manager = CacheManager()


def cache_key_from_args(*args, **kwargs) -> str:
    """Generate cache key from function arguments."""
    # Create a hash of the arguments
    key_data = str(args) + str(sorted(kwargs.items()))
    return hashlib.md5(key_data.encode()).hexdigest()


def cache_async(
    ttl: Optional[int] = None,
    prefix: str = "func_cache",
    key_func: Optional[Callable] = None
):
    """Decorator for caching async function results."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}:{cache_key_from_args(*args, **kwargs)}"
            
            # Try to get from cache
            cached_result = await cache_manager.get(cache_key, prefix)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache_manager.set(cache_key, result, ttl, prefix)
            
            return result
        return wrapper
    return decorator


def cache_sync(
    ttl: Optional[int] = None,
    prefix: str = "func_cache",
    key_func: Optional[Callable] = None
):
    """Decorator for caching sync function results."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}:{cache_key_from_args(*args, **kwargs)}"
            
            # Run async operations in sync context
            async def async_wrapper():
                # Try to get from cache
                cached_result = await cache_manager.get(cache_key, prefix)
                if cached_result is not None:
                    return cached_result
                
                # Execute function and cache result
                result = func(*args, **kwargs)
                await cache_manager.set(cache_key, result, ttl, prefix)
                
                return result
            
            # Run in event loop
            try:
                loop = asyncio.get_event_loop()
                return loop.run_until_complete(async_wrapper())
            except RuntimeError:
                # If no event loop is running, create one
                return asyncio.run(async_wrapper())
                
        return wrapper
    return decorator


async def get_cache_manager() -> CacheManager:
    """Dependency to get cache manager."""
    return cache_manager