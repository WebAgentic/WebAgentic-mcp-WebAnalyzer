"""
FastMCP server for web content analysis and RAG functionality.
"""

import os
from typing import Optional

from fastmcp import FastMCP
from .web_extractor import url_to_markdown
from .rag_processor import RAGProcessor


# Initialize MCP server
mcp = FastMCP("Web Analyzer MCP")

# Initialize RAG processor
rag_processor = RAGProcessor()


@mcp.tool()
def url_to_markdown_tool(url: str) -> str:
    """
    Extract and convert web page content to markdown format.
    
    This tool scrapes a web page, removes unnecessary elements, 
    ranks content by importance using a custom algorithm, and 
    returns clean markdown. Perfect for RAG applications.
    
    Args:
        url: The web page URL to analyze and convert
        
    Returns:
        str: Clean markdown representation of the web page content
    """
    return url_to_markdown(url)


@mcp.tool()
def web_content_qna(url: str, question: str) -> str:
    """
    Answer questions about web page content using RAG.
    
    This tool combines web scraping with RAG (Retrieval Augmented Generation)
    to answer specific questions about web page content. It extracts relevant
    content sections and uses AI to provide accurate answers.
    
    Args:
        url: The web page URL to analyze
        question: The question to answer based on the page content
        
    Returns:
        str: AI-generated answer based on the web page content
    """
    return rag_processor.process_web_qna(url, question)



def main():
    """Main entry point for the MCP server."""
    # Initialize without requiring API key
    mcp.run()


if __name__ == "__main__":
    main()