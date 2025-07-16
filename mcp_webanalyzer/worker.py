"""Celery worker for async task processing."""

import asyncio
from typing import Dict, Any, List
from celery import Celery
from .config import get_settings
from .server import discover_subpages, extract_page_summary, extract_content_for_rag

settings = get_settings()

# Create Celery app
celery_app = Celery(
    "web-analyzer-worker",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["web_analyzer_mcp.worker"]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)


@celery_app.task(bind=True, name="discover_subpages_async")
def discover_subpages_task(self, url: str, max_depth: int = 2, max_pages: int = 100) -> Dict[str, Any]:
    """Async task for discovering subpages."""
    try:
        # Update task state
        self.update_state(state="PROGRESS", meta={"status": "Starting page discovery"})
        
        # Run the async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                discover_subpages(url, max_depth, max_pages)
            )
            
            return {
                "status": "SUCCESS",
                "result": result,
                "url": url,
                "max_depth": max_depth,
                "max_pages": max_pages,
                "pages_found": len(result) if isinstance(result, list) else 0
            }
        finally:
            loop.close()
            
    except Exception as exc:
        self.update_state(
            state="FAILURE",
            meta={"error": str(exc), "url": url}
        )
        raise


@celery_app.task(bind=True, name="extract_page_summary_async")
def extract_page_summary_task(self, url: str) -> Dict[str, Any]:
    """Async task for extracting page summary."""
    try:
        self.update_state(state="PROGRESS", meta={"status": "Extracting page summary"})
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(extract_page_summary(url))
            
            return {
                "status": "SUCCESS",
                "result": result,
                "url": url,
                "summary_length": len(result) if isinstance(result, str) else 0
            }
        finally:
            loop.close()
            
    except Exception as exc:
        self.update_state(
            state="FAILURE",
            meta={"error": str(exc), "url": url}
        )
        raise


@celery_app.task(bind=True, name="extract_content_for_rag_async")
def extract_content_for_rag_task(self, url: str, question: str = None) -> Dict[str, Any]:
    """Async task for extracting content for RAG."""
    try:
        self.update_state(state="PROGRESS", meta={"status": "Extracting RAG content"})
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(extract_content_for_rag(url, question))
            
            return {
                "status": "SUCCESS",
                "result": result,
                "url": url,
                "question": question,
                "content_length": result.get("content_length", 0) if isinstance(result, dict) else 0
            }
        finally:
            loop.close()
            
    except Exception as exc:
        self.update_state(
            state="FAILURE",
            meta={"error": str(exc), "url": url, "question": question}
        )
        raise


@celery_app.task(bind=True, name="batch_analyze_urls")
def batch_analyze_urls_task(self, urls: List[str], analysis_type: str = "summary") -> Dict[str, Any]:
    """Batch analyze multiple URLs."""
    try:
        self.update_state(
            state="PROGRESS", 
            meta={"status": "Starting batch analysis", "total_urls": len(urls)}
        )
        
        results = []
        failed_urls = []
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            for i, url in enumerate(urls):
                try:
                    self.update_state(
                        state="PROGRESS",
                        meta={
                            "status": f"Processing URL {i+1}/{len(urls)}",
                            "current_url": url,
                            "progress": (i / len(urls)) * 100
                        }
                    )
                    
                    if analysis_type == "summary":
                        result = loop.run_until_complete(extract_page_summary(url))
                    elif analysis_type == "discover":
                        result = loop.run_until_complete(discover_subpages(url, 1, 20))
                    elif analysis_type == "rag":
                        result = loop.run_until_complete(extract_content_for_rag(url))
                    else:
                        raise ValueError(f"Unknown analysis type: {analysis_type}")
                    
                    results.append({
                        "url": url,
                        "result": result,
                        "status": "success"
                    })
                    
                except Exception as e:
                    failed_urls.append({"url": url, "error": str(e)})
                    results.append({
                        "url": url,
                        "result": None,
                        "status": "failed",
                        "error": str(e)
                    })
            
            return {
                "status": "SUCCESS",
                "results": results,
                "total_urls": len(urls),
                "successful": len(urls) - len(failed_urls),
                "failed": len(failed_urls),
                "failed_urls": failed_urls,
                "analysis_type": analysis_type
            }
        finally:
            loop.close()
            
    except Exception as exc:
        self.update_state(
            state="FAILURE",
            meta={"error": str(exc), "urls": urls, "analysis_type": analysis_type}
        )
        raise


# Health check task
@celery_app.task(name="health_check")
def health_check_task() -> Dict[str, Any]:
    """Health check task for monitoring."""
    return {
        "status": "healthy",
        "worker": "web-analyzer-worker",
        "timestamp": asyncio.get_event_loop().time()
    }


def main():
    """Main entry point for the worker."""
    import sys
    # Start Celery worker with solo pool (better for Windows)
    celery_app.worker_main(argv=['worker', '--loglevel=info', '--pool=solo'])


if __name__ == "__main__":
    main()