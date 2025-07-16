"""External API integrations for enhanced analysis."""

import httpx
from typing import Dict, Any, Optional, List
from openai import AsyncOpenAI
import anthropic
from .config import get_settings
from .utils.cache import cache_async

settings = get_settings()


class ExternalAPIError(Exception):
    """Custom exception for external API errors."""
    pass


class OpenAIClient:
    """OpenAI API client for content analysis."""
    
    def __init__(self):
        if not settings.openai_api_key:
            raise ExternalAPIError("OpenAI API key not configured")
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
    
    @cache_async(ttl=3600, prefix="openai_analysis")
    async def analyze_content(
        self, 
        content: str, 
        task: str = "summarize",
        question: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze content using OpenAI."""
        try:
            if task == "summarize":
                prompt = f"Summarize the following content in 2-3 sentences:\n\n{content[:4000]}"
            elif task == "extract_keywords":
                prompt = f"Extract the top 10 keywords from this content:\n\n{content[:4000]}"
            elif task == "answer_question":
                if not question:
                    raise ValueError("Question required for answer_question task")
                prompt = f"Based on this content, answer the question: {question}\n\nContent:\n{content[:4000]}"
            elif task == "categorize":
                prompt = f"Categorize this content into relevant topics:\n\n{content[:4000]}"
            else:
                raise ValueError(f"Unknown task: {task}")
            
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful content analyzer."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            return {
                "task": task,
                "result": response.choices[0].message.content,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
            
        except Exception as e:
            raise ExternalAPIError(f"OpenAI API error: {str(e)}")


class AnthropicClient:
    """Anthropic Claude API client for content analysis."""
    
    def __init__(self):
        if not settings.anthropic_api_key:
            raise ExternalAPIError("Anthropic API key not configured")
        self.client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    
    @cache_async(ttl=3600, prefix="anthropic_analysis")
    async def analyze_content(
        self, 
        content: str, 
        task: str = "summarize",
        question: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze content using Anthropic Claude."""
        try:
            if task == "summarize":
                prompt = f"Please summarize the following content in 2-3 sentences:\n\n{content[:4000]}"
            elif task == "extract_keywords":
                prompt = f"Extract the top 10 most important keywords from this content:\n\n{content[:4000]}"
            elif task == "answer_question":
                if not question:
                    raise ValueError("Question required for answer_question task")
                prompt = f"Based on this content, please answer the question: {question}\n\nContent:\n{content[:4000]}"
            elif task == "categorize":
                prompt = f"Categorize this content into relevant topics and themes:\n\n{content[:4000]}"
            else:
                raise ValueError(f"Unknown task: {task}")
            
            response = await self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return {
                "task": task,
                "result": response.content[0].text,
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens
                }
            }
            
        except Exception as e:
            raise ExternalAPIError(f"Anthropic API error: {str(e)}")


class WebhookClient:
    """Client for sending webhooks to external services."""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def send_webhook(
        self, 
        url: str, 
        data: Dict[str, Any], 
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Send webhook to external URL."""
        try:
            default_headers = {"Content-Type": "application/json"}
            if headers:
                default_headers.update(headers)
            
            response = await self.client.post(url, json=data, headers=default_headers)
            response.raise_for_status()
            
            return {
                "status": "success",
                "status_code": response.status_code,
                "response": response.json() if response.content else None
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


class SlackClient:
    """Slack API client for notifications."""
    
    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def send_notification(
        self, 
        message: str, 
        channel: Optional[str] = None,
        title: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send notification to Slack."""
        if not self.webhook_url:
            raise ExternalAPIError("Slack webhook URL not configured")
        
        try:
            payload = {
                "text": title or "Web Analyzer Notification",
                "attachments": [
                    {
                        "color": "good",
                        "text": message,
                        "ts": int(asyncio.get_event_loop().time())
                    }
                ]
            }
            
            if channel:
                payload["channel"] = channel
            
            response = await self.client.post(self.webhook_url, json=payload)
            response.raise_for_status()
            
            return {"status": "success", "message": "Notification sent"}
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


class ExternalAPIManager:
    """Manager for all external API clients."""
    
    def __init__(self):
        self.openai_client: Optional[OpenAIClient] = None
        self.anthropic_client: Optional[AnthropicClient] = None
        self.webhook_client = WebhookClient()
        self.slack_client: Optional[SlackClient] = None
    
    def get_openai_client(self) -> OpenAIClient:
        """Get OpenAI client (lazy initialization)."""
        if self.openai_client is None:
            self.openai_client = OpenAIClient()
        return self.openai_client
    
    def get_anthropic_client(self) -> AnthropicClient:
        """Get Anthropic client (lazy initialization)."""
        if self.anthropic_client is None:
            self.anthropic_client = AnthropicClient()
        return self.anthropic_client
    
    def get_slack_client(self, webhook_url: Optional[str] = None) -> SlackClient:
        """Get Slack client (lazy initialization)."""
        if self.slack_client is None:
            self.slack_client = SlackClient(webhook_url)
        return self.slack_client
    
    async def enhance_analysis(
        self, 
        content: str, 
        provider: str = "openai",
        task: str = "summarize",
        question: Optional[str] = None
    ) -> Dict[str, Any]:
        """Enhance analysis using external APIs."""
        try:
            if provider == "openai":
                client = self.get_openai_client()
            elif provider == "anthropic":
                client = self.get_anthropic_client()
            else:
                raise ValueError(f"Unknown provider: {provider}")
            
            return await client.analyze_content(content, task, question)
            
        except ExternalAPIError:
            # If external API fails, return basic analysis
            return {
                "task": task,
                "result": "External API unavailable. Basic analysis performed.",
                "provider": provider,
                "status": "fallback"
            }
    
    async def close(self):
        """Close all clients."""
        await self.webhook_client.close()
        if self.slack_client:
            await self.slack_client.close()


# Global API manager instance
api_manager = ExternalAPIManager()


async def get_api_manager() -> ExternalAPIManager:
    """Dependency to get API manager."""
    return api_manager