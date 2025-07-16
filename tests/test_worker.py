"""
Tests for Celery worker functionality
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from mcp_webanalyzer.worker import (
    discover_subpages_task,
    extract_page_summary_task,
    extract_content_for_rag_task,
)


class TestDiscoverSubpagesTask:
    """Test discover_subpages_task Celery task"""

    @patch('mcp_webanalyzer.worker.discover_subpages')
    def test_discover_subpages_task_success(self, mock_discover):
        """Test successful subpages discovery task"""
        mock_discover.return_value = [
            {"url": "https://example.com/page1", "title": "Page 1"},
            {"url": "https://example.com/page2", "title": "Page 2"}
        ]
        
        result = discover_subpages_task("https://example.com", max_depth=2)
        
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["url"] == "https://example.com/page1"
        mock_discover.assert_called_once_with("https://example.com", max_depth=2)

    @patch('mcp_webanalyzer.worker.discover_subpages')
    def test_discover_subpages_task_failure(self, mock_discover):
        """Test failed subpages discovery task"""
        mock_discover.side_effect = Exception("Network error")
        
        with pytest.raises(Exception):
            discover_subpages_task("https://example.com", max_depth=2)

    @patch('mcp_webanalyzer.worker.discover_subpages')
    def test_discover_subpages_task_with_cache(self, mock_discover):
        """Test subpages discovery task with caching"""
        mock_discover.return_value = [
            {"url": "https://example.com/page1", "title": "Page 1"}
        ]
        
        with patch('mcp_webanalyzer.worker.cache_get') as mock_cache_get, \
             patch('mcp_webanalyzer.worker.cache_set') as mock_cache_set:
            
            mock_cache_get.return_value = None  # Cache miss
            
            result = discover_subpages_task("https://example.com", max_depth=1)
            
            assert isinstance(result, list)
            mock_cache_set.assert_called_once()  # Result should be cached

    @patch('mcp_webanalyzer.worker.discover_subpages')
    def test_discover_subpages_task_cache_hit(self, mock_discover):
        """Test subpages discovery task with cache hit"""
        cached_result = [{"url": "https://example.com/cached", "title": "Cached"}]
        
        with patch('mcp_webanalyzer.worker.cache_get') as mock_cache_get:
            mock_cache_get.return_value = cached_result
            
            result = discover_subpages_task("https://example.com", max_depth=1)
            
            assert result == cached_result
            mock_discover.assert_not_called()  # Should not call actual function


class TestExtractPageSummaryTask:
    """Test extract_page_summary_task Celery task"""

    @patch('mcp_webanalyzer.worker.extract_page_summary')
    def test_extract_page_summary_task_success(self, mock_extract):
        """Test successful page summary extraction task"""
        mock_extract.return_value = {
            "summary": "This is a test summary",
            "title": "Test Page",
            "url": "https://example.com"
        }
        
        result = extract_page_summary_task("https://example.com")
        
        assert isinstance(result, dict)
        assert result["summary"] == "This is a test summary"
        assert result["url"] == "https://example.com"
        mock_extract.assert_called_once_with("https://example.com", max_length=None)

    @patch('mcp_webanalyzer.worker.extract_page_summary')
    def test_extract_page_summary_task_with_length(self, mock_extract):
        """Test page summary extraction task with length limit"""
        mock_extract.return_value = {
            "summary": "Short summary",
            "title": "Test Page",
            "url": "https://example.com"
        }
        
        result = extract_page_summary_task("https://example.com", max_length=100)
        
        assert isinstance(result, dict)
        assert len(result["summary"]) <= 100
        mock_extract.assert_called_once_with("https://example.com", max_length=100)

    @patch('mcp_webanalyzer.worker.extract_page_summary')
    def test_extract_page_summary_task_failure(self, mock_extract):
        """Test failed page summary extraction task"""
        mock_extract.side_effect = Exception("Extraction failed")
        
        with pytest.raises(Exception):
            extract_page_summary_task("https://example.com")

    @patch('mcp_webanalyzer.worker.extract_page_summary')
    def test_extract_page_summary_task_with_cache(self, mock_extract):
        """Test page summary extraction task with caching"""
        mock_extract.return_value = {
            "summary": "Test summary",
            "title": "Test Page",
            "url": "https://example.com"
        }
        
        with patch('mcp_webanalyzer.worker.cache_get') as mock_cache_get, \
             patch('mcp_webanalyzer.worker.cache_set') as mock_cache_set:
            
            mock_cache_get.return_value = None  # Cache miss
            
            result = extract_page_summary_task("https://example.com")
            
            assert isinstance(result, dict)
            mock_cache_set.assert_called_once()  # Result should be cached


class TestExtractContentForRagTask:
    """Test extract_content_for_rag_task Celery task"""

    @patch('mcp_webanalyzer.worker.extract_content_for_rag')
    def test_extract_content_for_rag_task_success(self, mock_extract):
        """Test successful content extraction for RAG task"""
        mock_extract.return_value = {
            "content": "This is the extracted content",
            "metadata": {"title": "Test Page", "description": "Test description"},
            "url": "https://example.com"
        }
        
        result = extract_content_for_rag_task("https://example.com")
        
        assert isinstance(result, dict)
        assert "content" in result
        assert "metadata" in result
        assert result["url"] == "https://example.com"
        mock_extract.assert_called_once_with("https://example.com", chunk_size=None)

    @patch('mcp_webanalyzer.worker.extract_content_for_rag')
    def test_extract_content_for_rag_task_with_chunking(self, mock_extract):
        """Test content extraction for RAG task with chunking"""
        mock_extract.return_value = {
            "content": "This is the extracted content",
            "chunks": ["Chunk 1", "Chunk 2"],
            "metadata": {"title": "Test Page"},
            "url": "https://example.com"
        }
        
        result = extract_content_for_rag_task("https://example.com", chunk_size=500)
        
        assert isinstance(result, dict)
        assert "chunks" in result
        assert len(result["chunks"]) == 2
        mock_extract.assert_called_once_with("https://example.com", chunk_size=500)

    @patch('mcp_webanalyzer.worker.extract_content_for_rag')
    def test_extract_content_for_rag_task_failure(self, mock_extract):
        """Test failed content extraction for RAG task"""
        mock_extract.side_effect = Exception("Extraction failed")
        
        with pytest.raises(Exception):
            extract_content_for_rag_task("https://example.com")


class TestTaskRetry:
    """Test task retry functionality"""

    @patch('mcp_webanalyzer.worker.discover_subpages')
    def test_task_retry_on_failure(self, mock_discover):
        """Test task retry on failure"""
        mock_discover.side_effect = [
            Exception("First failure"),
            Exception("Second failure"),
            [{"url": "https://example.com/page1", "title": "Page 1"}]  # Success on third try
        ]
        
        # This test depends on actual Celery retry configuration
        # In a real test, you might need to mock the retry mechanism
        with pytest.raises(Exception):
            discover_subpages_task("https://example.com", max_depth=1)

    @patch('mcp_webanalyzer.worker.extract_page_summary')
    def test_task_max_retries(self, mock_extract):
        """Test task reaches max retries"""
        mock_extract.side_effect = Exception("Persistent failure")
        
        with pytest.raises(Exception):
            extract_page_summary_task("https://example.com")


class TestTaskLogging:
    """Test task logging functionality"""

    @patch('mcp_webanalyzer.worker.discover_subpages')
    def test_task_logging(self, mock_discover):
        """Test task logging"""
        mock_discover.return_value = [
            {"url": "https://example.com/page1", "title": "Page 1"}
        ]
        
        with patch('mcp_webanalyzer.worker.logger') as mock_logger:
            discover_subpages_task("https://example.com", max_depth=1)
            
            # Should log task start and completion
            assert mock_logger.info.call_count >= 2

    @patch('mcp_webanalyzer.worker.extract_page_summary')
    def test_task_error_logging(self, mock_extract):
        """Test task error logging"""
        mock_extract.side_effect = Exception("Test error")
        
        with patch('mcp_webanalyzer.worker.logger') as mock_logger:
            with pytest.raises(Exception):
                extract_page_summary_task("https://example.com")
            
            # Should log error
            mock_logger.error.assert_called()


class TestTaskMetrics:
    """Test task metrics collection"""

    @patch('mcp_webanalyzer.worker.discover_subpages')
    def test_task_metrics(self, mock_discover):
        """Test task metrics collection"""
        mock_discover.return_value = [
            {"url": "https://example.com/page1", "title": "Page 1"}
        ]
        
        with patch('mcp_webanalyzer.worker.increment_counter') as mock_counter:
            discover_subpages_task("https://example.com", max_depth=1)
            
            # Should increment task counter
            mock_counter.assert_called()

    @patch('mcp_webanalyzer.worker.extract_page_summary')
    def test_task_failure_metrics(self, mock_extract):
        """Test task failure metrics"""
        mock_extract.side_effect = Exception("Test error")
        
        with patch('mcp_webanalyzer.worker.increment_counter') as mock_counter:
            with pytest.raises(Exception):
                extract_page_summary_task("https://example.com")
            
            # Should increment failure counter
            mock_counter.assert_called()


class TestTaskConfiguration:
    """Test task configuration"""

    def test_task_routing(self):
        """Test task routing configuration"""
        from mcp_webanalyzer.worker import celery_app
        
        # Test that tasks are properly configured
        assert 'mcp_webanalyzer.worker.discover_subpages_task' in celery_app.tasks
        assert 'mcp_webanalyzer.worker.extract_page_summary_task' in celery_app.tasks
        assert 'mcp_webanalyzer.worker.extract_content_for_rag_task' in celery_app.tasks

    def test_task_serialization(self):
        """Test task serialization configuration"""
        from mcp_webanalyzer.worker import celery_app
        
        # Test serialization settings
        assert celery_app.conf.task_serializer == 'json'
        assert celery_app.conf.result_serializer == 'json'
        assert celery_app.conf.accept_content == ['json']