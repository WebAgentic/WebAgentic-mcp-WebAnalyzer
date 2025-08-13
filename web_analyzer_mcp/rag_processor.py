"""
RAG (Retrieval Augmented Generation) processor for web content analysis.
Implements HTMLRAG-style functionality for question answering.
"""

import os
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

import openai
from .web_extractor import url_to_markdown


@dataclass
class TextChunk:
    """Represents a chunk of text with metadata."""
    content: str
    score: float = 0.0
    source_type: str = "text"  # text, table, image, etc.


class RAGProcessor:
    """Processes web content for RAG-based question answering."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize RAG processor with OpenAI client."""
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.client = None
        if self.api_key:
            try:
                self.client = openai.OpenAI(api_key=self.api_key)
            except Exception:
                pass
        self.max_chunk_size = 1000
        self.overlap_size = 100
    
    def chunk_content(self, content: str) -> List[TextChunk]:
        """Split content into manageable chunks for processing."""
        # Split by sections (markdown headers and paragraph breaks)
        sections = re.split(r'\n(?=#{1,3}\s|\n)', content)
        
        chunks = []
        for section in sections:
            section = section.strip()
            if not section:
                continue
            
            # Determine source type based on content markers
            source_type = "text"
            if section.startswith('|') or '[Table]' in section:
                source_type = "table"
            elif section.startswith('![') or '[Image]' in section:
                source_type = "image"
            elif '[Video]' in section or '[Popup]' in section:
                source_type = "media"
            
            # If section is too long, split it further
            if len(section) > self.max_chunk_size:
                # Split by sentences
                sentences = re.split(r'(?<=[.!?])\s+', section)
                current_chunk = ""
                
                for sentence in sentences:
                    if len(current_chunk + sentence) > self.max_chunk_size:
                        if current_chunk:
                            chunks.append(TextChunk(
                                content=current_chunk.strip(),
                                source_type=source_type
                            ))
                        current_chunk = sentence
                    else:
                        current_chunk += " " + sentence if current_chunk else sentence
                
                if current_chunk:
                    chunks.append(TextChunk(
                        content=current_chunk.strip(),
                        source_type=source_type
                    ))
            else:
                chunks.append(TextChunk(
                    content=section,
                    source_type=source_type
                ))
        
        return chunks
    
    def score_relevance(self, query: str, chunk: TextChunk) -> float:
        """Score how relevant a chunk is to the query."""
        query_lower = query.lower()
        content_lower = chunk.content.lower()
        
        # Basic keyword matching score
        query_words = set(re.findall(r'\b\w+\b', query_lower))
        content_words = set(re.findall(r'\b\w+\b', content_lower))
        
        if not query_words:
            return 0.0
        
        # Calculate overlap
        common_words = query_words.intersection(content_words)
        keyword_score = len(common_words) / len(query_words)
        
        # Boost score based on source type relevance
        type_boost = {
            "text": 1.0,
            "table": 1.2,  # Tables often contain structured important info
            "image": 0.8,
            "media": 0.6
        }
        
        # Boost for exact phrase matches
        phrase_boost = 1.0
        if len(query) > 10:  # Only for longer queries
            # Check for phrase matches (simplified)
            query_phrases = [phrase.strip() for phrase in query.split() if len(phrase) > 3]
            for phrase in query_phrases:
                if phrase.lower() in content_lower:
                    phrase_boost += 0.2
        
        final_score = keyword_score * type_boost.get(chunk.source_type, 1.0) * phrase_boost
        return min(final_score, 2.0)  # Cap at 2.0
    
    def select_relevant_chunks(self, query: str, chunks: List[TextChunk], max_chunks: int = 5) -> List[TextChunk]:
        """Select the most relevant chunks for a query."""
        # Score all chunks
        for chunk in chunks:
            chunk.score = self.score_relevance(query, chunk)
        
        # Sort by relevance and take top chunks
        relevant_chunks = sorted(chunks, key=lambda x: x.score, reverse=True)
        
        # Filter out chunks with very low scores
        relevant_chunks = [chunk for chunk in relevant_chunks if chunk.score > 0.1]
        
        return relevant_chunks[:max_chunks]
    
    def generate_answer(self, query: str, relevant_chunks: List[TextChunk]) -> str:
        """Generate an answer using OpenAI based on relevant chunks."""
        if not relevant_chunks:
            return "I couldn't find relevant information in the provided content to answer your question."
        
        # Check if OpenAI client is available
        if not self.client:
            return "OpenAI API key not configured. Please set OPENAI_API_KEY environment variable to use Q&A functionality."
        
        # Prepare context from chunks
        context_parts = []
        for i, chunk in enumerate(relevant_chunks, 1):
            context_parts.append(f"[Context {i}] ({chunk.source_type}):\n{chunk.content}\n")
        
        context = "\n".join(context_parts)
        
        # Prepare prompt
        system_prompt = """You are a helpful AI assistant that answers questions based on provided web content. 
Use only the information from the given context to answer the question. If the context doesn't contain 
enough information to answer the question, say so clearly. Be concise but comprehensive in your answer."""
        
        user_prompt = f"""Based on the following web content, please answer this question: {query}

Context:
{context}

Question: {query}

Answer:"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=500,
                temperature=0.1
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return f"Error generating answer: {str(e)}"
    
    def process_web_qna(self, url: str, question: str) -> str:
        """
        Process a URL and answer a question about its content.
        
        This is the main RAG function that combines web extraction and QA.
        
        Args:
            url: The URL to analyze
            question: The question to answer based on the URL content
            
        Returns:
            str: The answer to the question based on the web content
        """
        try:
            # Extract content from URL
            markdown_content = url_to_markdown(url)
            
            if markdown_content.startswith("Error"):
                return f"Could not process the URL: {markdown_content}"
            
            # Chunk the content
            chunks = self.chunk_content(markdown_content)
            
            if not chunks:
                return "No content could be extracted from the URL to answer your question."
            
            # Select relevant chunks
            relevant_chunks = self.select_relevant_chunks(question, chunks)
            
            if not relevant_chunks:
                return f"The content from {url} doesn't seem to contain information relevant to your question: '{question}'"
            
            # Generate answer
            answer = self.generate_answer(question, relevant_chunks)
            
            return answer
            
        except Exception as e:
            return f"Error processing question about {url}: {str(e)}"