"""Monitoring and logging utilities."""

import time
import structlog
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Callable
from functools import wraps
from contextlib import asynccontextmanager
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
import redis.asyncio as redis

from ..config import get_settings

settings = get_settings()

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer() if settings.log_format == "json" else structlog.dev.ConsoleRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Prometheus metrics
REQUEST_COUNT = Counter(
    'web_analyzer_requests_total',
    'Total number of requests',
    ['method', 'endpoint', 'status_code']
)

REQUEST_DURATION = Histogram(
    'web_analyzer_request_duration_seconds',
    'Request duration in seconds',
    ['method', 'endpoint']
)

ACTIVE_CONNECTIONS = Gauge(
    'web_analyzer_active_connections',
    'Number of active connections'
)

CACHE_HITS = Counter(
    'web_analyzer_cache_hits_total',
    'Total number of cache hits',
    ['cache_type']
)

CACHE_MISSES = Counter(
    'web_analyzer_cache_misses_total',
    'Total number of cache misses',
    ['cache_type']
)

TASK_COUNT = Counter(
    'web_analyzer_tasks_total',
    'Total number of tasks processed',
    ['task_type', 'status']
)

TASK_DURATION = Histogram(
    'web_analyzer_task_duration_seconds',
    'Task processing duration in seconds',
    ['task_type']
)

EXTERNAL_API_CALLS = Counter(
    'web_analyzer_external_api_calls_total',
    'Total number of external API calls',
    ['provider', 'status']
)

EXTERNAL_API_DURATION = Histogram(
    'web_analyzer_external_api_duration_seconds',
    'External API call duration in seconds',
    ['provider']
)


class MetricsCollector:
    """Collector for application metrics."""
    
    def __init__(self):
        self._redis: Optional[redis.Redis] = None
    
    async def get_redis(self) -> redis.Redis:
        """Get Redis connection for metrics storage."""
        if self._redis is None:
            connection_kwargs = {"decode_responses": True}
            if settings.redis_password:
                connection_kwargs["password"] = settings.redis_password
                
            self._redis = redis.from_url(
                settings.redis_url,
                **connection_kwargs
            )
        return self._redis
    
    async def record_request(
        self, 
        method: str, 
        endpoint: str, 
        status_code: int, 
        duration: float
    ):
        """Record HTTP request metrics."""
        REQUEST_COUNT.labels(
            method=method,
            endpoint=endpoint,
            status_code=status_code
        ).inc()
        
        REQUEST_DURATION.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
    
    async def record_cache_hit(self, cache_type: str):
        """Record cache hit."""
        CACHE_HITS.labels(cache_type=cache_type).inc()
    
    async def record_cache_miss(self, cache_type: str):
        """Record cache miss."""
        CACHE_MISSES.labels(cache_type=cache_type).inc()
    
    async def record_task(self, task_type: str, status: str, duration: Optional[float] = None):
        """Record task execution metrics."""
        TASK_COUNT.labels(task_type=task_type, status=status).inc()
        
        if duration is not None:
            TASK_DURATION.labels(task_type=task_type).observe(duration)
    
    async def record_external_api_call(
        self, 
        provider: str, 
        status: str, 
        duration: float
    ):
        """Record external API call metrics."""
        EXTERNAL_API_CALLS.labels(provider=provider, status=status).inc()
        EXTERNAL_API_DURATION.labels(provider=provider).observe(duration)
    
    async def increment_active_connections(self):
        """Increment active connections counter."""
        ACTIVE_CONNECTIONS.inc()
    
    async def decrement_active_connections(self):
        """Decrement active connections counter."""
        ACTIVE_CONNECTIONS.dec()
    
    async def get_metrics_data(self) -> str:
        """Get Prometheus metrics data."""
        return generate_latest()
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get application health status."""
        redis_client = await self.get_redis()
        
        try:
            # Test Redis connection
            await redis_client.ping()
            redis_status = "healthy"
        except Exception as e:
            redis_status = f"unhealthy: {str(e)}"
        
        return {
            "status": "healthy" if redis_status == "healthy" else "unhealthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "services": {
                "redis": redis_status,
                "metrics": "healthy"
            },
            "version": settings.version
        }
    
    async def close(self):
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()


# Global metrics collector
metrics_collector = MetricsCollector()


def monitor_performance(func_name: Optional[str] = None):
    """Decorator to monitor function performance."""
    def decorator(func):
        name = func_name or f"{func.__module__}.{func.__name__}"
        
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.time()
                status = "success"
                
                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception as e:
                    status = "error"
                    logger.error(
                        "Function execution failed",
                        function=name,
                        error=str(e),
                        args=args[:3],  # Log first 3 args only
                        kwargs=list(kwargs.keys())
                    )
                    raise
                finally:
                    duration = time.time() - start_time
                    await metrics_collector.record_task(name, status, duration)
                    
                    logger.info(
                        "Function execution completed",
                        function=name,
                        duration=duration,
                        status=status
                    )
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                start_time = time.time()
                status = "success"
                
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    status = "error"
                    logger.error(
                        "Function execution failed",
                        function=name,
                        error=str(e),
                        args=args[:3],
                        kwargs=list(kwargs.keys())
                    )
                    raise
                finally:
                    duration = time.time() - start_time
                    
                    # Run async metrics recording in background
                    try:
                        loop = asyncio.get_event_loop()
                        loop.create_task(
                            metrics_collector.record_task(name, status, duration)
                        )
                    except RuntimeError:
                        pass  # No event loop running
                    
                    logger.info(
                        "Function execution completed",
                        function=name,
                        duration=duration,
                        status=status
                    )
            return sync_wrapper
    return decorator


@asynccontextmanager
async def monitor_external_api(provider: str):
    """Context manager to monitor external API calls."""
    start_time = time.time()
    status = "success"
    
    try:
        yield
    except Exception as e:
        status = "error"
        logger.error(
            "External API call failed",
            provider=provider,
            error=str(e)
        )
        raise
    finally:
        duration = time.time() - start_time
        await metrics_collector.record_external_api_call(provider, status, duration)


class RequestMonitor:
    """Monitor for HTTP requests."""
    
    def __init__(self):
        self.start_time = None
    
    async def __aenter__(self):
        self.start_time = time.time()
        await metrics_collector.increment_active_connections()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await metrics_collector.decrement_active_connections()
        
        if self.start_time:
            duration = time.time() - self.start_time
            status_code = 500 if exc_type else 200
            
            # This would typically be called with actual request info
            logger.info(
                "Request completed",
                duration=duration,
                status_code=status_code,
                error=str(exc_val) if exc_val else None
            )


def get_logger(name: str = __name__) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


async def get_metrics_collector() -> MetricsCollector:
    """Dependency to get metrics collector."""
    return metrics_collector


# Logging utilities
def log_api_call(provider: str, endpoint: str, status: str, duration: float):
    """Log external API call."""
    logger.info(
        "External API call",
        provider=provider,
        endpoint=endpoint,
        status=status,
        duration=duration
    )


def log_cache_operation(operation: str, key: str, hit: bool, duration: Optional[float] = None):
    """Log cache operation."""
    logger.debug(
        "Cache operation",
        operation=operation,
        key=key,
        hit=hit,
        duration=duration
    )


def log_task_execution(task_name: str, status: str, duration: float, **kwargs):
    """Log task execution."""
    logger.info(
        "Task execution",
        task=task_name,
        status=status,
        duration=duration,
        **kwargs
    )