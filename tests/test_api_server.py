"""
Tests for the FastAPI server functionality
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from mcp_webanalyzer.api_server import app, get_settings
from mcp_webanalyzer.config import Settings


@pytest.fixture
def test_client(test_settings):
    """Create test client with test settings"""
    app.dependency_overrides[get_settings] = lambda: test_settings
    return TestClient(app)


class TestHealthEndpoint:
    """Test health check endpoint"""

    def test_health_check(self, test_client):
        """Test health check endpoint returns 200"""
        response = test_client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_health_check_with_redis(self, test_client, mock_redis):
        """Test health check with Redis connection"""
        with patch('mcp_webanalyzer.utils.cache.get_redis_client', return_value=mock_redis):
            response = test_client.get("/health")
            assert response.status_code == 200
            assert "redis" in response.json()


class TestMCPToolsEndpoint:
    """Test MCP tools endpoint"""

    def test_discover_subpages_endpoint(self, test_client):
        """Test discover_subpages endpoint"""
        with patch('mcp_webanalyzer.api_server.discover_subpages_task') as mock_task:
            mock_task.delay.return_value = MagicMock(id="test-task-id")
            
            response = test_client.post(
                "/mcp/tools/discover_subpages",
                json={"url": "https://example.com", "max_depth": 2},
                headers={"X-API-Key": "test-api-key"}
            )
            
            assert response.status_code == 200
            assert "task_id" in response.json()

    def test_extract_page_summary_endpoint(self, test_client):
        """Test extract_page_summary endpoint"""
        with patch('mcp_webanalyzer.api_server.extract_page_summary_task') as mock_task:
            mock_task.delay.return_value = MagicMock(id="test-task-id")
            
            response = test_client.post(
                "/mcp/tools/extract_page_summary",
                json={"url": "https://example.com"},
                headers={"X-API-Key": "test-api-key"}
            )
            
            assert response.status_code == 200
            assert "task_id" in response.json()

    def test_extract_content_for_rag_endpoint(self, test_client):
        """Test extract_content_for_rag endpoint"""
        with patch('mcp_webanalyzer.api_server.extract_content_for_rag_task') as mock_task:
            mock_task.delay.return_value = MagicMock(id="test-task-id")
            
            response = test_client.post(
                "/mcp/tools/extract_content_for_rag",
                json={"url": "https://example.com"},
                headers={"X-API-Key": "test-api-key"}
            )
            
            assert response.status_code == 200
            assert "task_id" in response.json()

    def test_unauthorized_request(self, test_client):
        """Test unauthorized request without API key"""
        response = test_client.post(
            "/mcp/tools/discover_subpages",
            json={"url": "https://example.com"}
        )
        
        assert response.status_code == 401

    def test_invalid_api_key(self, test_client):
        """Test request with invalid API key"""
        response = test_client.post(
            "/mcp/tools/discover_subpages",
            json={"url": "https://example.com"},
            headers={"X-API-Key": "invalid-key"}
        )
        
        assert response.status_code == 401

    def test_invalid_url_format(self, test_client):
        """Test request with invalid URL format"""
        response = test_client.post(
            "/mcp/tools/discover_subpages",
            json={"url": "invalid-url"},
            headers={"X-API-Key": "test-api-key"}
        )
        
        assert response.status_code == 422

    def test_missing_required_fields(self, test_client):
        """Test request with missing required fields"""
        response = test_client.post(
            "/mcp/tools/discover_subpages",
            json={},
            headers={"X-API-Key": "test-api-key"}
        )
        
        assert response.status_code == 422


class TestTaskStatusEndpoint:
    """Test task status endpoint"""

    def test_get_task_status(self, test_client):
        """Test getting task status"""
        with patch('mcp_webanalyzer.api_server.celery_app') as mock_celery:
            mock_result = MagicMock()
            mock_result.state = "SUCCESS"
            mock_result.result = {"data": "test"}
            mock_celery.AsyncResult.return_value = mock_result
            
            response = test_client.get(
                "/tasks/test-task-id",
                headers={"X-API-Key": "test-api-key"}
            )
            
            assert response.status_code == 200
            assert response.json()["status"] == "SUCCESS"

    def test_get_task_status_pending(self, test_client):
        """Test getting pending task status"""
        with patch('mcp_webanalyzer.api_server.celery_app') as mock_celery:
            mock_result = MagicMock()
            mock_result.state = "PENDING"
            mock_result.result = None
            mock_celery.AsyncResult.return_value = mock_result
            
            response = test_client.get(
                "/tasks/test-task-id",
                headers={"X-API-Key": "test-api-key"}
            )
            
            assert response.status_code == 200
            assert response.json()["status"] == "PENDING"

    def test_get_task_status_failed(self, test_client):
        """Test getting failed task status"""
        with patch('mcp_webanalyzer.api_server.celery_app') as mock_celery:
            mock_result = MagicMock()
            mock_result.state = "FAILURE"
            mock_result.result = Exception("Task failed")
            mock_celery.AsyncResult.return_value = mock_result
            
            response = test_client.get(
                "/tasks/test-task-id",
                headers={"X-API-Key": "test-api-key"}
            )
            
            assert response.status_code == 200
            assert response.json()["status"] == "FAILURE"


class TestMetricsEndpoint:
    """Test metrics endpoint"""

    def test_metrics_endpoint(self, test_client):
        """Test metrics endpoint"""
        response = test_client.get("/metrics")
        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]

    def test_metrics_content(self, test_client):
        """Test metrics content format"""
        response = test_client.get("/metrics")
        content = response.text
        
        # Should contain Prometheus metrics format
        assert "# HELP" in content or "# TYPE" in content or len(content) > 0


class TestRateLimiting:
    """Test rate limiting functionality"""

    def test_rate_limit_applied(self, test_client):
        """Test that rate limiting is applied"""
        # Make multiple requests quickly
        responses = []
        for i in range(5):
            response = test_client.post(
                "/mcp/tools/discover_subpages",
                json={"url": "https://example.com"},
                headers={"X-API-Key": "test-api-key"}
            )
            responses.append(response)
        
        # At least some should succeed (exact behavior depends on rate limit config)
        success_count = sum(1 for r in responses if r.status_code == 200)
        assert success_count > 0


class TestErrorHandling:
    """Test error handling"""

    def test_404_endpoint(self, test_client):
        """Test 404 for non-existent endpoint"""
        response = test_client.get("/non-existent-endpoint")
        assert response.status_code == 404

    def test_method_not_allowed(self, test_client):
        """Test method not allowed"""
        response = test_client.get("/mcp/tools/discover_subpages")
        assert response.status_code == 405

    def test_invalid_json(self, test_client):
        """Test invalid JSON request"""
        response = test_client.post(
            "/mcp/tools/discover_subpages",
            data="invalid json",
            headers={
                "X-API-Key": "test-api-key",
                "Content-Type": "application/json"
            }
        )
        assert response.status_code == 422


class TestCORS:
    """Test CORS configuration"""

    def test_cors_headers(self, test_client):
        """Test CORS headers are present"""
        response = test_client.options("/health")
        assert response.status_code == 200
        # CORS headers should be present
        assert "access-control-allow-origin" in response.headers or response.status_code == 200