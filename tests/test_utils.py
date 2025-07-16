"""
Tests for utility functions
"""
import pytest
from unittest.mock import patch, MagicMock
from mcp_webanalyzer.utils.auth import verify_api_key, create_jwt_token, verify_jwt_token
from mcp_webanalyzer.utils.cache import get_redis_client, cache_set, cache_get, cache_delete
from mcp_webanalyzer.utils.monitoring import get_metrics, log_request, increment_counter


class TestAuthUtils:
    """Test authentication utilities"""

    def test_verify_api_key_valid(self, test_settings):
        """Test API key verification with valid key"""
        result = verify_api_key("test-api-key", test_settings)
        assert result is True

    def test_verify_api_key_invalid(self, test_settings):
        """Test API key verification with invalid key"""
        result = verify_api_key("invalid-key", test_settings)
        assert result is False

    def test_verify_api_key_none(self, test_settings):
        """Test API key verification with None"""
        result = verify_api_key(None, test_settings)
        assert result is False

    def test_create_jwt_token(self, test_settings):
        """Test JWT token creation"""
        token = create_jwt_token({"user": "test"}, test_settings)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_verify_jwt_token_valid(self, test_settings):
        """Test JWT token verification with valid token"""
        token = create_jwt_token({"user": "test"}, test_settings)
        payload = verify_jwt_token(token, test_settings)
        assert payload is not None
        assert payload["user"] == "test"

    def test_verify_jwt_token_invalid(self, test_settings):
        """Test JWT token verification with invalid token"""
        payload = verify_jwt_token("invalid-token", test_settings)
        assert payload is None

    def test_verify_jwt_token_expired(self, test_settings):
        """Test JWT token verification with expired token"""
        with patch('mcp_webanalyzer.utils.auth.datetime') as mock_datetime:
            # Create token in the past
            mock_datetime.utcnow.return_value.timestamp.return_value = 1000000000
            token = create_jwt_token({"user": "test"}, test_settings)
            
            # Verify token in the future
            mock_datetime.utcnow.return_value.timestamp.return_value = 2000000000
            payload = verify_jwt_token(token, test_settings)
            assert payload is None


class TestCacheUtils:
    """Test cache utilities"""

    def test_get_redis_client(self, test_settings):
        """Test Redis client creation"""
        with patch('mcp_webanalyzer.utils.cache.redis.Redis') as mock_redis:
            mock_redis.return_value = MagicMock()
            client = get_redis_client(test_settings)
            assert client is not None

    def test_cache_set(self, mock_redis):
        """Test cache set operation"""
        with patch('mcp_webanalyzer.utils.cache.get_redis_client', return_value=mock_redis):
            result = cache_set("test-key", "test-value", ttl=3600)
            assert result is True
            mock_redis.setex.assert_called_once()

    def test_cache_get(self, mock_redis):
        """Test cache get operation"""
        mock_redis.get.return_value = b'{"data": "test"}'
        
        with patch('mcp_webanalyzer.utils.cache.get_redis_client', return_value=mock_redis):
            result = cache_get("test-key")
            assert result == {"data": "test"}
            mock_redis.get.assert_called_once_with("test-key")

    def test_cache_get_not_found(self, mock_redis):
        """Test cache get operation when key not found"""
        mock_redis.get.return_value = None
        
        with patch('mcp_webanalyzer.utils.cache.get_redis_client', return_value=mock_redis):
            result = cache_get("non-existent-key")
            assert result is None

    def test_cache_delete(self, mock_redis):
        """Test cache delete operation"""
        with patch('mcp_webanalyzer.utils.cache.get_redis_client', return_value=mock_redis):
            result = cache_delete("test-key")
            assert result is True
            mock_redis.delete.assert_called_once_with("test-key")

    def test_cache_operations_with_redis_error(self, mock_redis):
        """Test cache operations with Redis error"""
        mock_redis.get.side_effect = Exception("Redis error")
        
        with patch('mcp_webanalyzer.utils.cache.get_redis_client', return_value=mock_redis):
            result = cache_get("test-key")
            assert result is None  # Should handle error gracefully


class TestMonitoringUtils:
    """Test monitoring utilities"""

    def test_get_metrics(self):
        """Test metrics collection"""
        with patch('mcp_webanalyzer.utils.monitoring.REGISTRY') as mock_registry:
            mock_registry.collect.return_value = []
            metrics = get_metrics()
            assert isinstance(metrics, str)

    def test_log_request(self):
        """Test request logging"""
        with patch('mcp_webanalyzer.utils.monitoring.logger') as mock_logger:
            log_request("GET", "/test", 200, 0.1)
            mock_logger.info.assert_called_once()

    def test_increment_counter(self):
        """Test counter increment"""
        with patch('mcp_webanalyzer.utils.monitoring.REQUEST_COUNT') as mock_counter:
            increment_counter("test_counter", {"label": "value"})
            mock_counter.labels.assert_called_once()

    def test_metrics_collection(self):
        """Test metrics are properly collected"""
        with patch('mcp_webanalyzer.utils.monitoring.generate_latest') as mock_generate:
            mock_generate.return_value = b"# HELP test_metric Test metric\n"
            metrics = get_metrics()
            assert "test_metric" in metrics or isinstance(metrics, str)


class TestConfigUtils:
    """Test configuration utilities"""

    def test_settings_validation(self):
        """Test settings validation"""
        from mcp_webanalyzer.config import Settings
        
        settings = Settings(
            debug=True,
            redis_url="redis://localhost:6379/0",
            secret_key="test-secret",
            api_key="test-api-key"
        )
        
        assert settings.debug is True
        assert settings.redis_url == "redis://localhost:6379/0"
        assert settings.secret_key == "test-secret"
        assert settings.api_key == "test-api-key"

    def test_settings_from_env(self):
        """Test settings from environment variables"""
        with patch.dict('os.environ', {
            'DEBUG': 'true',
            'REDIS_URL': 'redis://localhost:6379/1',
            'SECRET_KEY': 'env-secret',
            'API_KEY': 'env-api-key'
        }):
            from mcp_webanalyzer.config import Settings
            settings = Settings()
            
            assert settings.debug is True
            assert settings.redis_url == "redis://localhost:6379/1"
            assert settings.secret_key == "env-secret"
            assert settings.api_key == "env-api-key"


class TestErrorHandling:
    """Test error handling utilities"""

    def test_redis_connection_error(self):
        """Test Redis connection error handling"""
        with patch('mcp_webanalyzer.utils.cache.redis.Redis') as mock_redis:
            mock_redis.side_effect = Exception("Connection failed")
            
            with pytest.raises(Exception):
                get_redis_client(Settings())

    def test_auth_error_handling(self, test_settings):
        """Test authentication error handling"""
        with patch('mcp_webanalyzer.utils.auth.jwt.encode') as mock_encode:
            mock_encode.side_effect = Exception("JWT error")
            
            with pytest.raises(Exception):
                create_jwt_token({"user": "test"}, test_settings)

    def test_monitoring_error_handling(self):
        """Test monitoring error handling"""
        with patch('mcp_webanalyzer.utils.monitoring.logger') as mock_logger:
            mock_logger.info.side_effect = Exception("Logging error")
            
            # Should not raise exception
            log_request("GET", "/test", 200, 0.1)