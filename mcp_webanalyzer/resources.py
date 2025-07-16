"""Dynamic resource generation system for reports and data."""

import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse, parse_qs
import aiofiles
from jinja2 import Template
from .utils.cache import cache_manager
from .config import get_settings

settings = get_settings()


class ResourceError(Exception):
    """Custom exception for resource errors."""
    pass


class ResourceGenerator:
    """Generator for dynamic resources."""
    
    def __init__(self):
        self.templates = {}
        self._load_templates()
    
    def _load_templates(self):
        """Load HTML templates for reports."""
        self.templates["report"] = Template("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
        .header { border-bottom: 2px solid #007acc; padding-bottom: 20px; margin-bottom: 30px; }
        .title { color: #007acc; margin: 0; }
        .subtitle { color: #666; margin: 5px 0 0 0; }
        .section { margin: 30px 0; }
        .section h2 { color: #333; border-left: 4px solid #007acc; padding-left: 15px; }
        .metadata { background: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0; }
        .url-list { list-style: none; padding: 0; }
        .url-list li { background: #fff; margin: 10px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
        .url-list li strong { color: #007acc; }
        .content-preview { background: #f9f9f9; padding: 15px; border-left: 3px solid #007acc; margin: 10px 0; }
        .timestamp { color: #888; font-size: 0.9em; }
        .stats { display: flex; gap: 20px; margin: 20px 0; }
        .stat { background: #007acc; color: white; padding: 15px; border-radius: 5px; text-align: center; flex: 1; }
        .stat .number { font-size: 2em; font-weight: bold; display: block; }
        .stat .label { font-size: 0.9em; opacity: 0.9; }
    </style>
</head>
<body>
    <div class="header">
        <h1 class="title">{{ title }}</h1>
        <p class="subtitle">{{ subtitle }}</p>
        <div class="timestamp">Generated on {{ timestamp }}</div>
    </div>
    
    <div class="metadata">
        <strong>Report ID:</strong> {{ report_id }}<br>
        <strong>Analysis Type:</strong> {{ analysis_type }}<br>
        <strong>Base URL:</strong> {{ base_url }}<br>
        <strong>Status:</strong> {{ status }}
    </div>
    
    {% if stats %}
    <div class="stats">
        {% for stat in stats %}
        <div class="stat">
            <span class="number">{{ stat.value }}</span>
            <span class="label">{{ stat.label }}</span>
        </div>
        {% endfor %}
    </div>
    {% endif %}
    
    {% for section in sections %}
    <div class="section">
        <h2>{{ section.title }}</h2>
        {% if section.type == 'url_list' %}
            <ul class="url-list">
            {% for item in section.content %}
                <li>
                    <strong>{{ item.url }}</strong>
                    {% if item.summary %}
                    <div class="content-preview">{{ item.summary }}</div>
                    {% endif %}
                </li>
            {% endfor %}
            </ul>
        {% elif section.type == 'content' %}
            <div class="content-preview">{{ section.content }}</div>
        {% elif section.type == 'json' %}
            <pre style="background: #f5f5f5; padding: 15px; overflow-x: auto;">{{ section.content | tojson(indent=2) }}</pre>
        {% endif %}
    </div>
    {% endfor %}
</body>
</html>
        """)
        
        self.templates["dashboard"] = Template("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Web Analyzer Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: white; padding: 30px; border-radius: 10px; margin-bottom: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .card { background: white; padding: 25px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .metric { text-align: center; padding: 20px; background: linear-gradient(135deg, #007acc, #0056b3); color: white; border-radius: 10px; }
        .metric .value { font-size: 3em; font-weight: bold; display: block; }
        .metric .label { opacity: 0.9; margin-top: 10px; }
        .recent-reports { list-style: none; padding: 0; }
        .recent-reports li { padding: 15px; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; align-items: center; }
        .recent-reports li:last-child { border-bottom: none; }
        .status { padding: 5px 10px; border-radius: 15px; font-size: 0.8em; font-weight: bold; }
        .status.completed { background: #d4edda; color: #155724; }
        .status.pending { background: #fff3cd; color: #856404; }
        .status.failed { background: #f8d7da; color: #721c24; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Web Analyzer Dashboard</h1>
            <p>Real-time analytics and report management</p>
        </div>
        
        <div class="grid">
            <div class="metric">
                <span class="value">{{ total_reports }}</span>
                <div class="label">Total Reports</div>
            </div>
            <div class="metric">
                <span class="value">{{ active_tasks }}</span>
                <div class="label">Active Tasks</div>
            </div>
            <div class="metric">
                <span class="value">{{ cached_items }}</span>
                <div class="label">Cached Items</div>
            </div>
        </div>
        
        <div class="card">
            <h2>Recent Reports</h2>
            <ul class="recent-reports">
            {% for report in recent_reports %}
                <li>
                    <div>
                        <strong>{{ report.title }}</strong><br>
                        <small>{{ report.created_at }}</small>
                    </div>
                    <span class="status {{ report.status }}">{{ report.status }}</span>
                </li>
            {% endfor %}
            </ul>
        </div>
    </div>
</body>
</html>
        """)
    
    async def generate_report(
        self, 
        report_id: str, 
        data: Dict[str, Any],
        template_type: str = "report"
    ) -> str:
        """Generate HTML report from data."""
        try:
            if template_type not in self.templates:
                raise ResourceError(f"Unknown template type: {template_type}")
            
            template = self.templates[template_type]
            
            # Add default values
            data.setdefault("timestamp", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"))
            data.setdefault("report_id", report_id)
            
            html_content = template.render(**data)
            
            # Cache the generated report
            await cache_manager.set(
                f"report:{report_id}", 
                html_content, 
                ttl=86400,  # 24 hours
                prefix="resources"
            )
            
            return html_content
            
        except Exception as e:
            raise ResourceError(f"Failed to generate report: {str(e)}")
    
    async def generate_dashboard(self, stats: Dict[str, Any]) -> str:
        """Generate dashboard HTML."""
        try:
            dashboard_data = {
                "total_reports": stats.get("total_reports", 0),
                "active_tasks": stats.get("active_tasks", 0),
                "cached_items": stats.get("cached_items", 0),
                "recent_reports": stats.get("recent_reports", [])
            }
            
            html_content = self.templates["dashboard"].render(**dashboard_data)
            
            # Cache dashboard for 5 minutes
            await cache_manager.set(
                "dashboard", 
                html_content, 
                ttl=300,
                prefix="resources"
            )
            
            return html_content
            
        except Exception as e:
            raise ResourceError(f"Failed to generate dashboard: {str(e)}")


class ResourceManager:
    """Manager for dynamic resources."""
    
    def __init__(self):
        self.generator = ResourceGenerator()
    
    async def create_analysis_report(
        self, 
        analysis_results: Dict[str, Any],
        analysis_type: str,
        base_url: str
    ) -> str:
        """Create analysis report from results."""
        report_id = str(uuid.uuid4())
        
        # Prepare report data
        report_data = {
            "title": f"Web Analysis Report - {analysis_type.title()}",
            "subtitle": f"Analysis of {base_url}",
            "report_id": report_id,
            "analysis_type": analysis_type,
            "base_url": base_url,
            "status": "completed",
            "sections": []
        }
        
        # Add statistics
        stats = []
        if analysis_type == "discover_subpages":
            results = analysis_results.get("result", [])
            stats.append({"value": len(results), "label": "Pages Found"})
            
            report_data["sections"].append({
                "title": "Discovered Pages",
                "type": "url_list",
                "content": [{"url": url, "summary": None} for url in results]
            })
            
        elif analysis_type == "summary":
            result = analysis_results.get("result", "")
            stats.append({"value": len(result), "label": "Characters"})
            
            report_data["sections"].append({
                "title": "Page Summary",
                "type": "content",
                "content": result
            })
            
        elif analysis_type == "rag":
            result = analysis_results.get("result", {})
            content_length = result.get("content_length", 0)
            headings_count = len(result.get("headings", []))
            
            stats.extend([
                {"value": content_length, "label": "Content Length"},
                {"value": headings_count, "label": "Headings"}
            ])
            
            report_data["sections"].extend([
                {
                    "title": "Content Summary",
                    "type": "content",
                    "content": result.get("summary", "")
                },
                {
                    "title": "Full Analysis Data",
                    "type": "json",
                    "content": result
                }
            ])
        
        report_data["stats"] = stats
        
        # Generate report
        html_content = await self.generator.generate_report(report_id, report_data)
        
        # Store report metadata
        metadata = {
            "report_id": report_id,
            "analysis_type": analysis_type,
            "base_url": base_url,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "completed"
        }
        
        await cache_manager.set(
            f"metadata:{report_id}",
            metadata,
            ttl=86400,
            prefix="reports"
        )
        
        return report_id
    
    async def get_report(self, report_id: str) -> Optional[str]:
        """Get report HTML by ID."""
        return await cache_manager.get(f"report:{report_id}", prefix="resources")
    
    async def get_report_metadata(self, report_id: str) -> Optional[Dict[str, Any]]:
        """Get report metadata by ID."""
        return await cache_manager.get(f"metadata:{report_id}", prefix="reports")
    
    async def list_reports(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List recent reports."""
        # This is a simplified implementation
        # In production, you'd want to use a proper database
        reports = []
        
        # Get cached report metadata (this is a demo implementation)
        for i in range(min(limit, 10)):  # Demo: return up to 10 dummy reports
            reports.append({
                "report_id": f"demo-{i}",
                "title": f"Demo Report {i}",
                "analysis_type": "summary",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "status": "completed"
            })
        
        return reports
    
    async def create_dashboard(self) -> str:
        """Create dashboard with current statistics."""
        # Gather statistics
        reports = await self.list_reports(10)
        
        stats = {
            "total_reports": len(reports),
            "active_tasks": 0,  # Would be fetched from Celery
            "cached_items": 0,  # Would be fetched from Redis
            "recent_reports": reports[:5]
        }
        
        dashboard_html = await self.generator.generate_dashboard(stats)
        return dashboard_html
    
    def parse_resource_uri(self, uri: str) -> Dict[str, Any]:
        """Parse resource URI and extract parameters."""
        try:
            parsed = urlparse(uri)
            
            if not parsed.scheme == "data":
                raise ResourceError("Invalid resource URI scheme")
            
            path_parts = parsed.path.strip("/").split("/")
            
            if len(path_parts) < 2:
                raise ResourceError("Invalid resource URI format")
            
            resource_type = path_parts[0]
            resource_id = path_parts[1]
            
            # Parse query parameters
            query_params = parse_qs(parsed.query) if parsed.query else {}
            
            return {
                "type": resource_type,
                "id": resource_id,
                "params": {k: v[0] if len(v) == 1 else v for k, v in query_params.items()}
            }
            
        except Exception as e:
            raise ResourceError(f"Failed to parse resource URI: {str(e)}")


# Global resource manager instance
resource_manager = ResourceManager()


async def get_resource_manager() -> ResourceManager:
    """Dependency to get resource manager."""
    return resource_manager