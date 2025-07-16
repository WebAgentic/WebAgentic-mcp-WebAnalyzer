"""
Test configuration and fixtures for MCP WebAnalyzer
"""
import pytest
import asyncio
import os
import sys
from unittest.mock import AsyncMock, MagicMock

# Add src to path for importing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from mcp_webanalyzer.config import Settings


@pytest.fixture
def test_settings():
    """Test settings fixture"""
    return Settings(
        debug=True,
        redis_url="redis://localhost:6379/15",  # Test DB
        celery_broker_url="redis://localhost:6379/15",
        celery_result_backend="redis://localhost:6379/15",
        secret_key="test-secret-key",
        api_key="test-api-key",
        log_level="DEBUG",
        host="127.0.0.1",
        port=8081,
    )


@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    mock_client = MagicMock()
    mock_client.get.return_value = None
    mock_client.set.return_value = True
    mock_client.delete.return_value = True
    mock_client.ping.return_value = True
    return mock_client


@pytest.fixture
def mock_celery_app():
    """Mock Celery app"""
    mock_app = MagicMock()
    mock_app.send_task.return_value = MagicMock(id="test-task-id")
    return mock_app


@pytest.fixture
def sample_html():
    """Sample HTML content for testing"""
    return """
    <html>
    <head>
        <title>Test Page</title>
        <meta name="description" content="Test page description">
    </head>
    <body>
        <h1>Test Heading</h1>
        <p>This is a test paragraph with some content.</p>
        <a href="/page1">Link 1</a>
        <a href="/page2">Link 2</a>
        <a href="https://external.com">External Link</a>
    </body>
    </html>
    """


@pytest.fixture
def sample_url():
    """Sample URL for testing"""
    return "https://example.com"


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_httpx_client():
    """Mock httpx async client"""
    mock_client = AsyncMock()
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.text = """
    <html>
    <head><title>Test Page</title></head>
    <body>
        <h1>Test Content</h1>
        <p>This is test content.</p>
    </body>
    </html>
    """
    mock_client.get.return_value = mock_response
    return mock_client


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client"""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "This is a test summary."
    mock_client.chat.completions.create.return_value = mock_response
    return mock_client