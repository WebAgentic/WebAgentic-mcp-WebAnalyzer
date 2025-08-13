"""
Web content extraction and analysis module.
Adapted from the original summary_url.py with improved algorithms.
"""

import re
import time
from typing import Optional

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup, Comment, Tag
from difflib import get_close_matches


# Tag scoring system for content importance
TAG_SCORES = {
    'h1': 3.0, 'h2': 2.5, 'h3': 2.0, 'h4': 1.5,
    'p': 1.5, 'li': 1.2, 'ul': 1.0, 'ol': 1.0,
    'table': 2.0, 'thead': 0.5, 'tbody': 0.5,
    'tr': 0.3, 'td': 0.2, 'th': 0.3,
    'img': 1.5, 'figure': 1.5, 'figcaption': 1.2,
    'blockquote': 1.0, 'code': 1.0, 'pre': 1.0,
    'strong': 0.5, 'em': 0.5, 'a': 0.0,
    'span': 0.3, 'div': 0.5,
}

# Container scoring for parent elements
CONTAINER_SCORES = {
    'main': 3,
    'article': 2,
    'section': 2,
    'body': 1,
    'div': 0.5,
}


def validate_url(url: str) -> bool:
    """Validate if the given string is a valid URL."""
    url_regex = re.compile(
        r"^(https?:\/\/)?"
        r"(www\.)?"
        r"([a-zA-Z0-9.-]+)"
        r"(\.[a-zA-Z]{2,})?"
        r"(:\d+)?"
        r"(\/[^\s]*)?$",
        re.IGNORECASE,
    )
    return bool(url_regex.match(url))


def ensure_url_scheme(url: str) -> str:
    """Ensure the URL has a proper scheme (http/https)."""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    
    if not validate_url(url):
        raise ValueError(f"Invalid URL: {url}")
    return url


def extract_html_content(url: str) -> str:
    """Extract HTML content from a URL using Selenium."""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(url)
        time.sleep(3)  # Wait for page to load
        html_content = driver.page_source
        driver.quit()
        return html_content
    except Exception as e:
        if 'driver' in locals():
            driver.quit()
        raise Exception(f"Failed to extract HTML from {url}: {str(e)}")


def parse_special_elements(soup: BeautifulSoup) -> dict:
    """Parse special HTML elements (tables, images, iframes, popups)."""
    result = {
        'tables': [],
        'images': [],
        'videos': [],
        'popups': []
    }
    
    # Parse tables
    for table in soup.find_all('table'):
        table_data = {}
        
        # Extract caption
        caption = table.find('caption')
        if caption:
            table_data['caption'] = caption.get_text(strip=True)
        
        # Extract headers
        thead = table.find('thead')
        if thead:
            headers = [th.get_text(strip=True) for th in thead.find_all('th')]
            table_data['headers'] = headers
        
        # Extract rows
        tbody = table.find('tbody') or table
        rows = []
        for tr in tbody.find_all('tr'):
            row_data = []
            for td in tr.find_all(['td', 'th']):
                cell_text = td.get_text(strip=True)
                row_data.append(cell_text)
            if row_data:
                rows.append(row_data)
        table_data['rows'] = rows
        
        if table_data:
            result['tables'].append(table_data)
    
    # Parse images
    for img in soup.find_all('img'):
        alt = img.get('alt', '')
        src = img.get('src', '')
        if alt or src:
            result['images'].append({'alt': alt, 'src': src})
    
    # Parse videos/iframes
    for iframe in soup.find_all('iframe'):
        title = iframe.get('title', 'Embedded content')
        src = iframe.get('src', '')
        result['videos'].append({'title': title, 'src': src})
    
    # Parse popup-like elements
    popup_keywords = ['popup', 'modal', 'dialog', 'overlay', 'toast']
    for keyword in popup_keywords:
        for element in soup.find_all(class_=re.compile(keyword, re.I)):
            text = element.get_text(strip=True)[:100]  # Limit to 100 chars
            if text:
                result['popups'].append(text)
    
    return result


def clean_html_content(soup: BeautifulSoup) -> BeautifulSoup:
    """Remove unnecessary HTML elements and clean the content."""
    # Elements to remove completely
    remove_tags = [
        'script', 'style', 'meta', 'nav', 'footer', 
        'header', 'aside', 'form', 'input', 'noscript',
        'svg', 'canvas'
    ]
    
    for tag_name in remove_tags:
        for tag in soup.find_all(tag_name):
            tag.decompose()
    
    # Remove comments
    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        comment.extract()
    
    # Remove empty elements with minimal content
    for element in soup.find_all():
        text = element.get_text(strip=True)
        if len(text) < 3 and not element.find_all(['img', 'input', 'button']):
            element.decompose()
    
    # Remove all attributes to clean up the HTML
    for tag in soup.find_all(True):
        tag.attrs = {}
    
    return soup


def compute_element_score(tag: Tag) -> float:
    """Compute importance score for an HTML element."""
    score = TAG_SCORES.get(tag.name, 0)
    
    # Add parent container scores
    for parent in tag.parents:
        if parent.name in CONTAINER_SCORES:
            score += CONTAINER_SCORES[parent.name]
    
    # Penalize deeply nested elements
    depth = len(list(tag.parents))
    if depth > 5:
        score -= (depth - 5) * 0.1
    
    return max(0, round(score, 2))


def rank_content_by_importance(soup: BeautifulSoup) -> str:
    """Rank and organize content by importance using custom algorithm."""
    scored_content = {}
    all_texts = []
    
    for tag in soup.find_all():
        if not isinstance(tag, Tag):
            continue
            
        text = tag.get_text(strip=True)
        if not text or len(text) < 5:
            continue
        
        score = compute_element_score(tag)
        if score <= 0:
            continue
        
        # Handle duplicate text - keep highest score
        if text in scored_content:
            if score > scored_content[text][0]:
                scored_content[text] = (score, tag.name)
        else:
            # Check for similar text using fuzzy matching
            similar_texts = get_close_matches(text, all_texts, n=3, cutoff=0.7)
            if similar_texts:
                # Remove shorter similar text if current is longer
                longest_similar = max(similar_texts, key=len)
                if len(text) > len(longest_similar):
                    if longest_similar in scored_content:
                        del scored_content[longest_similar]
                    all_texts.remove(longest_similar)
                    all_texts.append(text)
                    scored_content[text] = (score, tag.name)
                else:
                    continue  # Skip if current text is shorter
            else:
                all_texts.append(text)
                scored_content[text] = (score, tag.name)
    
    # Sort by score and organize output
    sorted_content = sorted(scored_content.items(), key=lambda x: x[1][0], reverse=True)
    
    organized_content = []
    current_score = None
    
    for text, (score, tag_name) in sorted_content:
        if current_score is None or score < current_score:
            if organized_content:  # Add separator between score groups
                organized_content.append("")
            current_score = score
        
        organized_content.append(text)
    
    return "\n".join(organized_content)


def convert_to_markdown(special_elements: dict, main_content: str) -> str:
    """Convert extracted content to markdown format."""
    markdown_parts = []
    
    # Add tables
    for table in special_elements['tables']:
        if 'caption' in table:
            markdown_parts.append(f"## {table['caption']}\n")
        
        if 'headers' in table and table['headers']:
            header_row = "| " + " | ".join(table['headers']) + " |"
            separator = "|" + "---|" * len(table['headers'])
            markdown_parts.append(header_row)
            markdown_parts.append(separator)
        
        for row in table.get('rows', []):
            if row:
                row_markdown = "| " + " | ".join(str(cell) for cell in row) + " |"
                markdown_parts.append(row_markdown)
        
        markdown_parts.append("")  # Empty line after table
    
    # Add images
    for img in special_elements['images']:
        alt_text = img['alt'] or 'Image'
        src = img['src']
        markdown_parts.append(f"![{alt_text}]({src})")
    
    # Add videos/embedded content
    for video in special_elements['videos']:
        markdown_parts.append(f"**{video['title']}**: {video['src']}")
    
    # Add popup content
    for popup in special_elements['popups']:
        markdown_parts.append(f"*[Popup]* {popup}")
    
    # Add main content
    if markdown_parts:
        markdown_parts.append("\n---\n")
    
    markdown_parts.append(main_content)
    
    return "\n".join(markdown_parts)


def url_to_markdown(url: str) -> str:
    """
    Convert a URL to markdown format using advanced content extraction.
    
    This is the main function that replaces the original build_output function.
    It extracts HTML, analyzes content importance, and converts to markdown.
    
    Args:
        url: The URL to analyze and convert
        
    Returns:
        str: Markdown formatted content
    """
    try:
        # Ensure valid URL
        clean_url = ensure_url_scheme(url)
        
        # Extract HTML content
        html_content = extract_html_content(clean_url)
        
        # Parse HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract special elements before cleaning
        special_elements = parse_special_elements(soup)
        
        # Clean HTML content
        cleaned_soup = clean_html_content(soup)
        
        # Rank content by importance
        main_content = rank_content_by_importance(cleaned_soup)
        
        # Convert to markdown
        markdown_result = convert_to_markdown(special_elements, main_content)
        
        return markdown_result
        
    except Exception as e:
        return f"Error processing URL {url}: {str(e)}"