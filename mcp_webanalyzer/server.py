"""Main MCP server implementation for web analysis tools."""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse
import httpx
from bs4 import BeautifulSoup
import html2text
from readability import Document
from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP("Web Analyzer")


@mcp.tool()
async def discover_subpages(url: str, max_depth: int = 2, max_pages: int = 100) -> List[str]:
    """
    Discover all subpages from a given URL up to a specified depth.
    
    Args:
        url: The base URL to start crawling from
        max_depth: Maximum depth to crawl (default: 2)
        max_pages: Maximum number of pages to discover (default: 100)
    
    Returns:
        List of discovered URLs
    """
    discovered_urls = set()
    base_domain = urlparse(url).netloc
    to_visit = [(url, 0)]
    visited = set()
    
    async with httpx.AsyncClient(
        timeout=30.0,
        headers={'User-Agent': 'Web-Analyzer-MCP/1.0'}
    ) as client:
        while to_visit and len(discovered_urls) < max_pages:
            current_url, depth = to_visit.pop(0)
            
            if current_url in visited or depth > max_depth:
                continue
                
            visited.add(current_url)
            
            try:
                response = await client.get(current_url)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                discovered_urls.add(current_url)
                
                if depth < max_depth:
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        absolute_url = urljoin(current_url, href)
                        parsed = urlparse(absolute_url)
                        
                        if (parsed.netloc == base_domain and 
                            absolute_url not in visited and
                            not any(ext in absolute_url.lower() for ext in ['.pdf', '.jpg', '.png', '.gif', '.css', '.js'])):
                            to_visit.append((absolute_url, depth + 1))
                            
            except Exception as e:
                logger.warning(f"Failed to process {current_url}: {e}")
                continue
    
    return sorted(list(discovered_urls))


@mcp.tool()
async def extract_page_summary(url: str) -> str:
    """
    Extract a one-line summary description of a web page.
    
    Args:
        url: The URL of the page to summarize
        
    Returns:
        A brief one-line description of the page content
    """
    try:
        async with httpx.AsyncClient(
            timeout=30.0,
            headers={'User-Agent': 'Web-Analyzer-MCP/1.0'}
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Try to get meta description first
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc and meta_desc.get('content'):
                return meta_desc['content'].strip()
            
            # Try OpenGraph description
            og_desc = soup.find('meta', attrs={'property': 'og:description'})
            if og_desc and og_desc.get('content'):
                return og_desc['content'].strip()
            
            # Try title + first paragraph
            title = soup.find('title')
            title_text = title.get_text().strip() if title else ""
            
            # Find first meaningful paragraph
            paragraphs = soup.find_all('p')
            for p in paragraphs:
                text = p.get_text().strip()
                if len(text) > 50:  # Skip very short paragraphs
                    return f"{title_text}: {text[:200]}..." if title_text else f"{text[:200]}..."
            
            # Fallback to title only
            return title_text or f"Page content from {url}"
            
    except Exception as e:
        logger.error(f"Failed to extract summary from {url}: {e}")
        return f"Unable to extract summary from {url}: {str(e)}"


@mcp.tool()
async def extract_content_for_rag(
    url: str, 
    question: Optional[str] = None
) -> Dict[str, Any]:
    """
    Extract and summarize web page content optimized for RAG applications.
    
    Args:
        url: The URL of the page to analyze
        question: Optional question to focus the extraction on
        
    Returns:
        Dictionary containing title, summary, main_content, and metadata
    """
    try:
        async with httpx.AsyncClient(
            timeout=30.0,
            headers={'User-Agent': 'Web-Analyzer-MCP/1.0'}
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            
            # Use readability to extract main content
            doc = Document(response.text)
            main_content_html = doc.summary()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            main_soup = BeautifulSoup(main_content_html, 'html.parser')
            
            # Extract metadata
            title = soup.find('title')
            title_text = title.get_text().strip() if title else ""
            
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            description = meta_desc.get('content').strip() if meta_desc and meta_desc.get('content') else ""
            
            # Convert to clean text
            h = html2text.HTML2Text()
            h.ignore_links = True
            h.ignore_images = True
            clean_content = h.handle(main_content_html)
            
            # Extract headings for structure
            headings = []
            for heading in main_soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                headings.append({
                    'level': heading.name,
                    'text': heading.get_text().strip()
                })
            
            # Create summary (first few paragraphs or description)
            summary = description
            if not summary:
                paragraphs = clean_content.split('\n\n')
                meaningful_paragraphs = [p.strip() for p in paragraphs if len(p.strip()) > 100]
                if meaningful_paragraphs:
                    summary = meaningful_paragraphs[0][:500] + "..." if len(meaningful_paragraphs[0]) > 500 else meaningful_paragraphs[0]
            
            result = {
                'url': url,
                'title': title_text,
                'summary': summary,
                'main_content': clean_content,
                'headings': headings,
                'content_length': len(clean_content),
                'metadata': {
                    'description': description,
                    'readability_score': doc.title(),
                }
            }
            
            # If question is provided, add relevance analysis
            if question:
                question_lower = question.lower()
                content_lower = clean_content.lower()
                
                # Simple relevance scoring based on keyword matching
                question_words = set(question_lower.split())
                content_words = set(content_lower.split())
                common_words = question_words.intersection(content_words)
                relevance_score = len(common_words) / len(question_words) if question_words else 0
                
                result['question_analysis'] = {
                    'question': question,
                    'relevance_score': relevance_score,
                    'matching_keywords': list(common_words),
                    'relevant_sections': []
                }
                
                # Find sections that might be relevant to the question
                for i, paragraph in enumerate(clean_content.split('\n\n')):
                    if any(word in paragraph.lower() for word in question_words):
                        result['question_analysis']['relevant_sections'].append({
                            'paragraph_index': i,
                            'content': paragraph.strip()
                        })
            
            return result
            
    except Exception as e:
        logger.error(f"Failed to extract content from {url}: {e}")
        return {
            'url': url,
            'error': str(e),
            'title': '',
            'summary': '',
            'main_content': '',
            'headings': [],
            'content_length': 0,
            'metadata': {}
        }


def main():
    """Main entry point for the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()