# Claude Desktop Integration Guide

This guide explains how to integrate the Web Analyzer MCP Server with Claude Desktop.

## Prerequisites

- Claude Desktop installed
- Web Analyzer MCP Server installed (`uv sync` completed)

## Configuration Steps

### 1. Locate Claude Desktop Configuration

**macOS:**
```bash
~/Library/Application Support/Claude/claude_desktop_config.json
```

**Windows:**
```bash
%APPDATA%\Claude\claude_desktop_config.json
```

### 2. Add Server Configuration

Open the configuration file and add the web-analyzer server:

```json
{
  "mcpServers": {
    "web-analyzer": {
      "command": "uv",
      "args": ["run", "web-analyzer-mcp"],
      "cwd": "/absolute/path/to/web-analyzer-mcp",
      "env": {
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

**Important:** Replace `/absolute/path/to/web-analyzer-mcp` with the actual path to your project directory.

### 3. Restart Claude Desktop

Close and restart Claude Desktop for the changes to take effect.

## Verification

1. Open Claude Desktop
2. Start a new conversation
3. You should see the web-analyzer tools available in the tool palette
4. Try using one of the tools:

```
Can you analyze the content of https://example.com for me?
```

## Available Tools

- `discover_subpages`: Find all subpages of a website
- `extract_page_summary`: Get a one-line summary of a page
- `extract_content_for_rag`: Extract structured content for RAG applications

## Troubleshooting

### Server Not Starting

1. Check the path in `cwd` is correct
2. Ensure `uv` is available in your PATH
3. Verify the project is properly installed (`uv sync`)

### Permission Issues

On macOS/Linux, you might need to make the script executable:

```bash
chmod +x /path/to/web-analyzer-mcp/src/web_analyzer_mcp/server.py
```

### Logs

Check Claude Desktop logs for error messages:

**macOS:**
```bash
~/Library/Logs/Claude/claude_desktop.log
```

**Windows:**
```bash
%LOCALAPPDATA%\Claude\logs\claude_desktop.log
```

## Advanced Configuration

### Custom Environment Variables

```json
{
  "mcpServers": {
    "web-analyzer": {
      "command": "uv",
      "args": ["run", "web-analyzer-mcp"],
      "cwd": "/path/to/web-analyzer-mcp",
      "env": {
        "LOG_LEVEL": "DEBUG",
        "TIMEOUT": "60",
        "MAX_PAGES": "200"
      }
    }
  }
}
```

### Using Virtual Environment Directly

If you prefer not to use `uv run`:

```json
{
  "mcpServers": {
    "web-analyzer": {
      "command": "/path/to/web-analyzer-mcp/.venv/bin/python",
      "args": ["-m", "web_analyzer_mcp.server"],
      "cwd": "/path/to/web-analyzer-mcp",
      "env": {
        "PYTHONPATH": "/path/to/web-analyzer-mcp/src"
      }
    }
  }
}
```

## Example Usage

Once configured, you can use the tools in Claude Desktop:

1. **Discover subpages:**
   > "Find all the subpages of https://docs.python.org with a maximum depth of 2"

2. **Get page summary:**
   > "Give me a summary of https://fastapi.tiangolo.com/"

3. **Extract content for RAG:**
   > "Extract the content from https://example.com/docs and analyze it for the question 'How do I install this software?'"