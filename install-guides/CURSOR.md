# Cursor IDE Integration Guide

This guide explains how to integrate the Web Analyzer MCP Server with Cursor IDE.

## Prerequisites

- Cursor IDE installed
- Web Analyzer MCP Server installed (`uv sync` completed)
- MCP extension for Cursor (if available)

## Configuration Steps

### 1. Open Cursor Settings

1. Open Cursor IDE
2. Go to `File > Preferences > Settings` (or `Ctrl/Cmd + ,`)
3. Search for "MCP" in the settings search bar

### 2. Configure MCP Server

Add the following configuration to your workspace settings or user settings:

**Via Settings UI:**
1. Look for "MCP: Servers" setting
2. Click "Edit in settings.json"

**Via settings.json directly:**

```json
{
  "mcp.servers": [
    {
      "name": "web-analyzer",
      "command": ["uv", "run", "web-analyzer-mcp"],
      "cwd": "/absolute/path/to/web-analyzer-mcp",
      "env": {
        "LOG_LEVEL": "INFO",
        "PYTHONPATH": "/absolute/path/to/web-analyzer-mcp/src"
      }
    }
  ],
  "mcp.enabled": true,
  "mcp.autoStart": true
}
```

**Important:** Replace `/absolute/path/to/web-analyzer-mcp` with the actual path to your project directory.

### 3. Workspace-Specific Configuration

For project-specific configuration, create `.vscode/settings.json` in your workspace:

```json
{
  "mcp.servers": [
    {
      "name": "web-analyzer",
      "command": ["uv", "run", "web-analyzer-mcp"],
      "cwd": "${workspaceFolder}/web-analyzer-mcp",
      "env": {
        "LOG_LEVEL": "INFO",
        "PYTHONPATH": "${workspaceFolder}/web-analyzer-mcp/src"
      }
    }
  ]
}
```

### 4. Restart Cursor

Restart Cursor IDE for the changes to take effect.

## Verification

1. Open the Command Palette (`Ctrl/Cmd + Shift + P`)
2. Search for "MCP" commands
3. You should see web-analyzer tools available
4. Open the MCP panel to see active servers

## Available Tools

- `discover_subpages`: Find all subpages of a website
- `extract_page_summary`: Get a one-line summary of a page
- `extract_content_for_rag`: Extract structured content for RAG applications

## Usage Examples

### Using the Command Palette

1. Press `Ctrl/Cmd + Shift + P`
2. Type "MCP: Run Tool"
3. Select the web-analyzer tool you want to use
4. Provide the required parameters

### Using AI Chat

If integrated with Cursor's AI features:

```
@web-analyzer discover_subpages https://example.com --max_depth 2 --max_pages 50
```

### In Code Comments

```python
# @web-analyzer extract_page_summary https://docs.python.org/3/
# This will extract a summary of the Python documentation
```

## Troubleshooting

### Server Not Starting

1. Check that `uv` is available in your PATH
2. Verify the project path in `cwd` is correct
3. Ensure dependencies are installed (`uv sync`)

### Check Server Status

1. Open Command Palette
2. Run "MCP: Show Server Status"
3. Look for "web-analyzer" in the list

### View Logs

1. Open Command Palette
2. Run "MCP: Show Logs"
3. Look for any error messages from the web-analyzer server

### Path Issues

Make sure paths are absolute or use Cursor variables:
- `${workspaceFolder}`: Current workspace root
- `${userHome}`: User home directory

## Advanced Configuration

### Custom Keybindings

Add to `keybindings.json`:

```json
[
  {
    "key": "ctrl+shift+w",
    "command": "mcp.runTool",
    "args": {
      "server": "web-analyzer",
      "tool": "extract_page_summary"
    }
  }
]
```

### Environment-Specific Settings

For different environments (dev, staging, prod):

```json
{
  "mcp.servers": [
    {
      "name": "web-analyzer-dev",
      "command": ["uv", "run", "web-analyzer-mcp"],
      "cwd": "/path/to/web-analyzer-mcp",
      "env": {
        "LOG_LEVEL": "DEBUG",
        "ENVIRONMENT": "development"
      }
    },
    {
      "name": "web-analyzer-prod",
      "command": ["uv", "run", "web-analyzer-mcp"],
      "cwd": "/path/to/web-analyzer-mcp",
      "env": {
        "LOG_LEVEL": "WARNING",
        "ENVIRONMENT": "production"
      }
    }
  ]
}
```

## Integration with Cursor AI

If using Cursor's AI features, you can reference the tools in your conversations:

```markdown
Please use the web-analyzer tools to:
1. Discover all subpages of https://example.com
2. Extract summaries for each page
3. Create a content map for the website
```

## Debugging

### Enable Debug Logging

```json
{
  "mcp.servers": [
    {
      "name": "web-analyzer",
      "command": ["uv", "run", "web-analyzer-mcp"],
      "cwd": "/path/to/web-analyzer-mcp",
      "env": {
        "LOG_LEVEL": "DEBUG"
      }
    }
  ],
  "mcp.logLevel": "debug"
}
```

### Manual Testing

Test the server manually:

```bash
cd /path/to/web-analyzer-mcp
uv run web-analyzer-mcp
```

The server should start and show available tools.