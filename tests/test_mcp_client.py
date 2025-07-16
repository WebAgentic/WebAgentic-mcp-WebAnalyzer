"""
Tests for MCP client functionality
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from mcp_webanalyzer.mcp_client import (
    discover_subpages_remote,
    extract_page_summary_remote,
    extract_content_for_rag_remote,
    MCPClient,
)


class TestMCPClientBasic:
    """Test basic MCP client functionality"""

    @pytest.fixture
    def mcp_client(self):
        """Create MCP client instance"""
        return MCPClient(
            api_base_url="http://localhost:8080",
            api_key="test-api-key"
        )

    @pytest.mark.asyncio
    async def test_discover_subpages_remote(self, mcp_client):
        """Test remote subpages discovery"""
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "task_id": "test-task-id",
            "status": "SUCCESS",
            "result": [
                {"url": "https://example.com/page1", "title": "Page 1"},
                {"url": "https://example.com/page2", "title": "Page 2"}
            ]
        }
        mock_response.status_code = 200
        
        with patch('mcp_webanalyzer.mcp_client.httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            result = await discover_subpages_remote(
                url="https://example.com",
                max_depth=2
            )
            
            assert isinstance(result, list)
            assert len(result) == 2
            assert result[0]["url"] == "https://example.com/page1"

    @pytest.mark.asyncio
    async def test_extract_page_summary_remote(self, mcp_client):
        """Test remote page summary extraction"""
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "task_id": "test-task-id",
            "status": "SUCCESS",
            "result": {
                "summary": "This is a test summary",
                "title": "Test Page",
                "url": "https://example.com"
            }
        }
        mock_response.status_code = 200
        
        with patch('mcp_webanalyzer.mcp_client.httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            result = await extract_page_summary_remote(
                url="https://example.com"
            )
            
            assert isinstance(result, dict)
            assert result["summary"] == "This is a test summary"
            assert result["url"] == "https://example.com"

    @pytest.mark.asyncio
    async def test_extract_content_for_rag_remote(self, mcp_client):
        """Test remote content extraction for RAG"""
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "task_id": "test-task-id",
            "status": "SUCCESS",
            "result": {
                "content": "This is the extracted content",
                "metadata": {"title": "Test Page", "description": "Test description"},
                "url": "https://example.com"
            }
        }
        mock_response.status_code = 200
        
        with patch('mcp_webanalyzer.mcp_client.httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            result = await extract_content_for_rag_remote(
                url="https://example.com"
            )
            
            assert isinstance(result, dict)
            assert "content" in result
            assert "metadata" in result
            assert result["url"] == "https://example.com"


class TestMCPClientAuthentication:
    """Test MCP client authentication"""

    @pytest.mark.asyncio
    async def test_api_key_authentication(self):
        """Test API key authentication"""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"task_id": "test-task-id"}
        
        with patch('mcp_webanalyzer.mcp_client.httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            result = await discover_subpages_remote(
                url="https://example.com",
                max_depth=1
            )
            
            # Check that API key was included in headers
            call_args = mock_client.return_value.__aenter__.return_value.post.call_args
            headers = call_args[1]['headers']
            assert 'X-API-Key' in headers

    @pytest.mark.asyncio
    async def test_authentication_failure(self):
        """Test authentication failure handling"""
        mock_response = AsyncMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        
        with patch('mcp_webanalyzer.mcp_client.httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            with pytest.raises(Exception):
                await discover_subpages_remote(
                    url="https://example.com",
                    max_depth=1
                )

    @pytest.mark.asyncio
    async def test_missing_api_key(self):
        """Test missing API key handling"""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError):
                await discover_subpages_remote(
                    url="https://example.com",
                    max_depth=1
                )


class TestMCPClientErrorHandling:
    """Test MCP client error handling"""

    @pytest.mark.asyncio
    async def test_network_error(self):
        """Test network error handling"""
        with patch('mcp_webanalyzer.mcp_client.httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post.side_effect = Exception("Network error")
            
            with pytest.raises(Exception):
                await discover_subpages_remote(
                    url="https://example.com",
                    max_depth=1
                )

    @pytest.mark.asyncio
    async def test_timeout_error(self):
        """Test timeout error handling"""
        with patch('mcp_webanalyzer.mcp_client.httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post.side_effect = asyncio.TimeoutError("Timeout")
            
            with pytest.raises(Exception):
                await discover_subpages_remote(
                    url="https://example.com",
                    max_depth=1
                )

    @pytest.mark.asyncio
    async def test_http_error_response(self):
        """Test HTTP error response handling"""
        mock_response = AsyncMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        
        with patch('mcp_webanalyzer.mcp_client.httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            with pytest.raises(Exception):
                await discover_subpages_remote(
                    url="https://example.com",
                    max_depth=1
                )

    @pytest.mark.asyncio
    async def test_invalid_json_response(self):
        """Test invalid JSON response handling"""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = Exception("Invalid JSON")
        
        with patch('mcp_webanalyzer.mcp_client.httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            with pytest.raises(Exception):
                await discover_subpages_remote(
                    url="https://example.com",
                    max_depth=1
                )


class TestMCPClientTaskPolling:
    """Test MCP client task polling functionality"""

    @pytest.mark.asyncio
    async def test_task_polling_success(self):
        """Test successful task polling"""
        # Mock task creation response
        mock_create_response = AsyncMock()
        mock_create_response.status_code = 200
        mock_create_response.json.return_value = {"task_id": "test-task-id"}
        
        # Mock task status responses
        mock_pending_response = AsyncMock()
        mock_pending_response.status_code = 200
        mock_pending_response.json.return_value = {"status": "PENDING"}
        
        mock_success_response = AsyncMock()
        mock_success_response.status_code = 200
        mock_success_response.json.return_value = {
            "status": "SUCCESS",
            "result": [{"url": "https://example.com/page1", "title": "Page 1"}]
        }
        
        with patch('mcp_webanalyzer.mcp_client.httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_create_response
            mock_client.return_value.__aenter__.return_value.get.side_effect = [
                mock_pending_response,
                mock_success_response
            ]
            
            result = await discover_subpages_remote(
                url="https://example.com",
                max_depth=1
            )
            
            assert isinstance(result, list)
            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_task_polling_failure(self):
        """Test task polling with failure"""
        # Mock task creation response
        mock_create_response = AsyncMock()
        mock_create_response.status_code = 200
        mock_create_response.json.return_value = {"task_id": "test-task-id"}
        
        # Mock task failure response
        mock_failure_response = AsyncMock()
        mock_failure_response.status_code = 200
        mock_failure_response.json.return_value = {
            "status": "FAILURE",
            "error": "Task failed"
        }
        
        with patch('mcp_webanalyzer.mcp_client.httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_create_response
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_failure_response
            
            with pytest.raises(Exception):
                await discover_subpages_remote(
                    url="https://example.com",
                    max_depth=1
                )

    @pytest.mark.asyncio
    async def test_task_polling_timeout(self):
        """Test task polling timeout"""
        # Mock task creation response
        mock_create_response = AsyncMock()
        mock_create_response.status_code = 200
        mock_create_response.json.return_value = {"task_id": "test-task-id"}
        
        # Mock task still pending response
        mock_pending_response = AsyncMock()
        mock_pending_response.status_code = 200
        mock_pending_response.json.return_value = {"status": "PENDING"}
        
        with patch('mcp_webanalyzer.mcp_client.httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_create_response
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_pending_response
            
            with patch('mcp_webanalyzer.mcp_client.asyncio.sleep') as mock_sleep:
                mock_sleep.return_value = None
                
                with pytest.raises(Exception):  # Should timeout
                    await discover_subpages_remote(
                        url="https://example.com",
                        max_depth=1
                    )


class TestMCPClientConfiguration:
    """Test MCP client configuration"""

    def test_client_initialization(self):
        """Test client initialization"""
        client = MCPClient(
            api_base_url="http://localhost:8080",
            api_key="test-api-key"
        )
        
        assert client.api_base_url == "http://localhost:8080"
        assert client.api_key == "test-api-key"

    def test_client_environment_variables(self):
        """Test client initialization from environment variables"""
        with patch.dict('os.environ', {
            'API_BASE_URL': 'http://test-server:8080',
            'API_KEY': 'env-test-key'
        }):
            client = MCPClient()
            
            assert client.api_base_url == "http://test-server:8080"
            assert client.api_key == "env-test-key"

    def test_client_default_configuration(self):
        """Test client default configuration"""
        client = MCPClient()
        
        assert client.api_base_url == "http://localhost:8080"
        assert client.timeout == 30
        assert client.max_retries == 3


class TestMCPClientIntegration:
    """Test MCP client integration scenarios"""

    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """Test full MCP client workflow"""
        # Test discover -> summary -> rag workflow
        mock_responses = [
            # Discover subpages
            AsyncMock(**{
                'status_code': 200,
                'json.return_value': {'task_id': 'discover-task-id'}
            }),
            AsyncMock(**{
                'status_code': 200,
                'json.return_value': {
                    'status': 'SUCCESS',
                    'result': [{'url': 'https://example.com/page1', 'title': 'Page 1'}]
                }
            }),
            # Extract summary
            AsyncMock(**{
                'status_code': 200,
                'json.return_value': {'task_id': 'summary-task-id'}
            }),
            AsyncMock(**{
                'status_code': 200,
                'json.return_value': {
                    'status': 'SUCCESS',
                    'result': {'summary': 'Test summary', 'title': 'Page 1'}
                }
            }),
            # Extract content for RAG
            AsyncMock(**{
                'status_code': 200,
                'json.return_value': {'task_id': 'rag-task-id'}
            }),
            AsyncMock(**{
                'status_code': 200,
                'json.return_value': {
                    'status': 'SUCCESS',
                    'result': {'content': 'Test content', 'metadata': {}}
                }
            })
        ]
        
        with patch('mcp_webanalyzer.mcp_client.httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post.side_effect = mock_responses[::2]
            mock_client.return_value.__aenter__.return_value.get.side_effect = mock_responses[1::2]
            
            # Test discover
            discover_result = await discover_subpages_remote("https://example.com", max_depth=1)
            assert len(discover_result) == 1
            
            # Test summary
            summary_result = await extract_page_summary_remote("https://example.com/page1")
            assert summary_result['summary'] == 'Test summary'
            
            # Test RAG
            rag_result = await extract_content_for_rag_remote("https://example.com/page1")
            assert rag_result['content'] == 'Test content'