"""MCP Client for HTTP API integration."""

import json
import httpx
from typing import Dict, Any, List, Optional
from fastmcp import FastMCP
from .config import get_settings

settings = get_settings()

# MCP Client that connects to HTTP API
mcp_client = FastMCP("Web Analyzer HTTP Client")


class HTTPMCPClient:
    """HTTP client that mimics MCP tool interface."""
    
    def __init__(self, base_url: str, api_key: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=60.0)
        
    async def get_headers(self) -> Dict[str, str]:
        """Get HTTP headers for API requests."""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers
    
    async def call_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Call HTTP API tool endpoint."""
        url = f"{self.base_url}/mcp/tools/{tool_name}"
        headers = await self.get_headers()
        
        try:
            response = await self.client.post(url, json=parameters, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            return {"error": str(e), "status": "failed"}
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()


# Global HTTP client instance
http_client: Optional[HTTPMCPClient] = None


def get_http_client() -> HTTPMCPClient:
    """Get or create HTTP client instance."""
    global http_client
    if http_client is None:
        # These will be set via environment variables
        base_url = settings.api_base_url or "http://localhost:8000"
        api_key = settings.api_key
        http_client = HTTPMCPClient(base_url, api_key)
    return http_client


@mcp_client.tool()
async def discover_subpages_remote(
    url: str, 
    max_depth: int = 2, 
    max_pages: int = 100
) -> List[str]:
    """Discover subpages via HTTP API."""
    client = get_http_client()
    result = await client.call_tool("discover_subpages", {
        "url": url,
        "max_depth": max_depth,
        "max_pages": max_pages
    })
    
    if "error" in result:
        raise Exception(f"API Error: {result['error']}")
    
    return result.get("result", [])


@mcp_client.tool()
async def extract_page_summary_remote(url: str) -> str:
    """Extract page summary via HTTP API."""
    client = get_http_client()
    result = await client.call_tool("extract_page_summary", {
        "url": url
    })
    
    if "error" in result:
        raise Exception(f"API Error: {result['error']}")
    
    return result.get("result", "")


@mcp_client.tool()
async def extract_content_for_rag_remote(
    url: str, 
    question: Optional[str] = None
) -> Dict[str, Any]:
    """Extract content for RAG via HTTP API."""
    client = get_http_client()
    result = await client.call_tool("extract_content_for_rag", {
        "url": url,
        "question": question
    })
    
    if "error" in result:
        raise Exception(f"API Error: {result['error']}")
    
    return result.get("result", {})


def main():
    """Main entry point for HTTP MCP client."""
    mcp_client.run()


if __name__ == "__main__":
    main()