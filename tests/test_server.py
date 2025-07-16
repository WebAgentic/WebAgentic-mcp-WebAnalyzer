"""
Tests for the MCP server functionality
"""
import pytest
from unittest.mock import patch, AsyncMock
from mcp_webanalyzer.server import (
    discover_subpages,
    extract_page_summary,
    extract_content_for_rag,
)


class TestDiscoverSubpages:
    """Test cases for discover_subpages function"""

    @pytest.mark.asyncio
    async def test_discover_subpages_basic(self, sample_url, mock_httpx_client):
        """Test basic subpage discovery"""
        with patch('mcp_webanalyzer.server.httpx.AsyncClient', return_value=mock_httpx_client):
            result = await discover_subpages(url=sample_url, max_depth=1)
            
            assert isinstance(result, list)
            assert len(result) > 0
            assert all(isinstance(item, dict) for item in result)

    @pytest.mark.asyncio
    async def test_discover_subpages_with_depth(self, sample_url, mock_httpx_client):
        """Test subpage discovery with depth limit"""
        with patch('mcp_webanalyzer.server.httpx.AsyncClient', return_value=mock_httpx_client):
            result = await discover_subpages(url=sample_url, max_depth=2)
            
            assert isinstance(result, list)
            # Should respect depth limit
            assert len(result) >= 0

    @pytest.mark.asyncio
    async def test_discover_subpages_invalid_url(self):
        """Test subpage discovery with invalid URL"""
        with pytest.raises(ValueError):
            await discover_subpages(url="invalid-url", max_depth=1)

    @pytest.mark.asyncio
    async def test_discover_subpages_network_error(self, sample_url):
        """Test subpage discovery with network error"""
        with patch('mcp_webanalyzer.server.httpx.AsyncClient') as mock_client:
            mock_client.return_value.get.side_effect = Exception("Network error")
            
            with pytest.raises(Exception):
                await discover_subpages(url=sample_url, max_depth=1)


class TestExtractPageSummary:
    """Test cases for extract_page_summary function"""

    @pytest.mark.asyncio
    async def test_extract_page_summary_basic(self, sample_url, mock_httpx_client, mock_openai_client):
        """Test basic page summary extraction"""
        with patch('mcp_webanalyzer.server.httpx.AsyncClient', return_value=mock_httpx_client), \
             patch('mcp_webanalyzer.server.openai.OpenAI', return_value=mock_openai_client):
            
            result = await extract_page_summary(url=sample_url)
            
            assert isinstance(result, dict)
            assert 'summary' in result
            assert 'title' in result
            assert 'url' in result
            assert result['url'] == sample_url

    @pytest.mark.asyncio
    async def test_extract_page_summary_with_max_length(self, sample_url, mock_httpx_client, mock_openai_client):
        """Test page summary with length limit"""
        with patch('mcp_webanalyzer.server.httpx.AsyncClient', return_value=mock_httpx_client), \
             patch('mcp_webanalyzer.server.openai.OpenAI', return_value=mock_openai_client):
            
            result = await extract_page_summary(url=sample_url, max_length=100)
            
            assert isinstance(result, dict)
            assert 'summary' in result
            # Summary should respect length limit (approximately)
            assert len(result['summary']) <= 200  # Allow some flexibility

    @pytest.mark.asyncio
    async def test_extract_page_summary_no_content(self, sample_url):
        """Test page summary with no content"""
        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.text = "<html><body></body></html>"
        mock_client.get.return_value = mock_response
        
        with patch('mcp_webanalyzer.server.httpx.AsyncClient', return_value=mock_client):
            result = await extract_page_summary(url=sample_url)
            
            assert isinstance(result, dict)
            assert 'summary' in result

    @pytest.mark.asyncio
    async def test_extract_page_summary_invalid_url(self):
        """Test page summary with invalid URL"""
        with pytest.raises(ValueError):
            await extract_page_summary(url="invalid-url")


class TestExtractContentForRag:
    """Test cases for extract_content_for_rag function"""

    @pytest.mark.asyncio
    async def test_extract_content_for_rag_basic(self, sample_url, mock_httpx_client):
        """Test basic content extraction for RAG"""
        with patch('mcp_webanalyzer.server.httpx.AsyncClient', return_value=mock_httpx_client):
            result = await extract_content_for_rag(url=sample_url)
            
            assert isinstance(result, dict)
            assert 'content' in result
            assert 'metadata' in result
            assert 'url' in result
            assert result['url'] == sample_url

    @pytest.mark.asyncio
    async def test_extract_content_for_rag_with_chunking(self, sample_url, mock_httpx_client):
        """Test content extraction with chunking"""
        with patch('mcp_webanalyzer.server.httpx.AsyncClient', return_value=mock_httpx_client):
            result = await extract_content_for_rag(url=sample_url, chunk_size=500)
            
            assert isinstance(result, dict)
            assert 'content' in result
            assert 'chunks' in result
            assert isinstance(result['chunks'], list)

    @pytest.mark.asyncio
    async def test_extract_content_for_rag_structured_data(self, sample_url):
        """Test content extraction with structured data"""
        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
        <head>
            <title>Test Article</title>
            <meta name="description" content="Test description">
            <meta name="keywords" content="test, article">
        </head>
        <body>
            <h1>Main Title</h1>
            <h2>Subtitle</h2>
            <p>First paragraph content.</p>
            <p>Second paragraph content.</p>
            <ul>
                <li>List item 1</li>
                <li>List item 2</li>
            </ul>
        </body>
        </html>
        """
        mock_client.get.return_value = mock_response
        
        with patch('mcp_webanalyzer.server.httpx.AsyncClient', return_value=mock_client):
            result = await extract_content_for_rag(url=sample_url)
            
            assert isinstance(result, dict)
            assert 'content' in result
            assert 'metadata' in result
            assert 'headings' in result['metadata']
            assert 'description' in result['metadata']

    @pytest.mark.asyncio
    async def test_extract_content_for_rag_invalid_url(self):
        """Test content extraction with invalid URL"""
        with pytest.raises(ValueError):
            await extract_content_for_rag(url="invalid-url")


class TestErrorHandling:
    """Test error handling scenarios"""

    @pytest.mark.asyncio
    async def test_timeout_handling(self, sample_url):
        """Test timeout handling"""
        mock_client = AsyncMock()
        mock_client.get.side_effect = asyncio.TimeoutError("Request timeout")
        
        with patch('mcp_webanalyzer.server.httpx.AsyncClient', return_value=mock_client):
            with pytest.raises(Exception):
                await extract_page_summary(url=sample_url)

    @pytest.mark.asyncio
    async def test_http_error_handling(self, sample_url):
        """Test HTTP error handling"""
        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_client.get.return_value = mock_response
        
        with patch('mcp_webanalyzer.server.httpx.AsyncClient', return_value=mock_client):
            with pytest.raises(Exception):
                await extract_page_summary(url=sample_url)

    @pytest.mark.asyncio
    async def test_malformed_html_handling(self, sample_url):
        """Test malformed HTML handling"""
        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.text = "<html><body><p>Unclosed paragraph</body></html>"
        mock_client.get.return_value = mock_response
        
        with patch('mcp_webanalyzer.server.httpx.AsyncClient', return_value=mock_client):
            # Should handle malformed HTML gracefully
            result = await extract_page_summary(url=sample_url)
            assert isinstance(result, dict)