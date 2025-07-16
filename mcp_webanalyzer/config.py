"""Configuration settings for the Web Analyzer MCP Server."""

import os
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Server Configuration
    app_name: str = "Web Analyzer MCP Server"
    version: str = "2.0.0"
    debug: bool = Field(default=False, env="DEBUG")
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=3002, env="PORT")
    
    # Security
    secret_key: str = Field(default="your-secret-key-change-in-production", env="SECRET_KEY")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    api_key: Optional[str] = Field(default=None, env="API_KEY")
    
    # Redis Configuration
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    redis_max_connections: int = 20
    
    # Celery Configuration
    celery_broker_url: str = Field(default="redis://localhost:6379/1", env="CELERY_BROKER_URL")
    celery_result_backend: str = Field(default="redis://localhost:6379/2", env="CELERY_RESULT_BACKEND")
    
    # Caching
    cache_ttl: int = Field(default=3600, env="CACHE_TTL")  # 1 hour
    cache_max_size: int = Field(default=1000, env="CACHE_MAX_SIZE")
    
    # Rate Limiting
    rate_limit_per_minute: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")
    rate_limit_burst: int = Field(default=10, env="RATE_LIMIT_BURST")
    
    # Web Scraping
    request_timeout: int = Field(default=30, env="REQUEST_TIMEOUT")
    max_pages_per_request: int = Field(default=100, env="MAX_PAGES_PER_REQUEST")
    max_depth: int = Field(default=3, env="MAX_DEPTH")
    user_agent: str = "Web-Analyzer-MCP/2.0"
    
    # External APIs
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = "json"
    
    # Monitoring
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    metrics_port: int = Field(default=9090, env="METRICS_PORT")
    
    # CORS
    allowed_origins: List[str] = Field(default=["*"], env="ALLOWED_ORIGINS")
    allowed_methods: List[str] = ["GET", "POST", "PUT", "DELETE"]
    allowed_headers: List[str] = ["*"]
    
    # HTTP API Client Settings
    api_base_url: Optional[str] = Field(default=None, env="API_BASE_URL")
    
    # Database (for future expansion)
    database_url: Optional[str] = Field(default=None, env="DATABASE_URL")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the current settings instance."""
    return settings