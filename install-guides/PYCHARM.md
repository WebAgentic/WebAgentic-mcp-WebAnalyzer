# PyCharm Integration Guide

This guide explains how to integrate the Web Analyzer MCP Server with PyCharm IDE.

## Prerequisites

- PyCharm IDE (Professional or Community Edition)
- Web Analyzer MCP Server installed (`uv sync` completed)
- MCP plugin for PyCharm (if available)

## Configuration Steps

### Method 1: Plugin Configuration (Recommended)

If MCP plugin is available:

1. **Install MCP Plugin:**
   - Go to `File > Settings > Plugins`
   - Search for "MCP" or "Model Context Protocol"
   - Install the plugin and restart PyCharm

2. **Configure Server:**
   - Go to `File > Settings > Tools > MCP Servers`
   - Click "Add Server"
   - Fill in the configuration:
     - **Name:** `web-analyzer`
     - **Command:** `uv`
     - **Arguments:** `run web-analyzer-mcp`
     - **Working Directory:** `/absolute/path/to/web-analyzer-mcp`
     - **Environment Variables:**
       - `LOG_LEVEL=INFO`
       - `PYTHONPATH=/absolute/path/to/web-analyzer-mcp/src`

### Method 2: External Tools Configuration

If no MCP plugin is available, set up as external tools:

1. **Go to External Tools:**
   - `File > Settings > Tools > External Tools`
   - Click the "+" button to add a new tool

2. **Configure Each Tool:**

   **Tool 1: Discover Subpages**
   - **Name:** `Web Analyzer - Discover Subpages`
   - **Program:** `uv`
   - **Arguments:** `run python -c "import asyncio; from web_analyzer_mcp.server import discover_subpages; print(asyncio.run(discover_subpages('$Prompt$')))"`
   - **Working directory:** `/path/to/web-analyzer-mcp`

   **Tool 2: Page Summary**
   - **Name:** `Web Analyzer - Page Summary`
   - **Program:** `uv`
   - **Arguments:** `run python -c "import asyncio; from web_analyzer_mcp.server import extract_page_summary; print(asyncio.run(extract_page_summary('$Prompt$')))"`
   - **Working directory:** `/path/to/web-analyzer-mcp`

   **Tool 3: RAG Content**
   - **Name:** `Web Analyzer - RAG Content`
   - **Program:** `uv`
   - **Arguments:** `run python -c "import asyncio; from web_analyzer_mcp.server import extract_content_for_rag; print(asyncio.run(extract_content_for_rag('$Prompt$')))"`
   - **Working directory:** `/path/to/web-analyzer-mcp`

### Method 3: Run Configuration

Create a run configuration for the MCP server:

1. **Create New Configuration:**
   - Go to `Run > Edit Configurations`
   - Click "+" and select "Python"

2. **Configure:**
   - **Name:** `Web Analyzer MCP Server`
   - **Script path:** `/path/to/web-analyzer-mcp/src/web_analyzer_mcp/server.py`
   - **Working directory:** `/path/to/web-analyzer-mcp`
   - **Environment variables:**
     - `PYTHONPATH=/path/to/web-analyzer-mcp/src`
     - `LOG_LEVEL=INFO`

## Project-Specific Configuration

### .idea/externalTools.xml

Add to your project's `.idea` directory:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<toolSet name="Web Analyzer MCP">
  <tool name="Discover Subpages" description="Find all subpages of a website" showInMainMenu="false" showInEditor="true" showInProject="false" showInSearchPopup="false" disabled="false" useConsole="true" showConsoleOnStdOut="false" showConsoleOnStdErr="false" synchronizeAfterRun="true">
    <exec>
      <option name="COMMAND" value="uv" />
      <option name="PARAMETERS" value="run python -c &quot;import asyncio; from web_analyzer_mcp.server import discover_subpages; print(asyncio.run(discover_subpages('$Prompt$')))&quot;" />
      <option name="WORKING_DIRECTORY" value="$ProjectFileDir$/web-analyzer-mcp" />
    </exec>
  </tool>
  
  <tool name="Page Summary" description="Extract page summary" showInMainMenu="false" showInEditor="true" showInProject="false" showInSearchPopup="false" disabled="false" useConsole="true" showConsoleOnStdOut="false" showConsoleOnStdErr="false" synchronizeAfterRun="true">
    <exec>
      <option name="COMMAND" value="uv" />
      <option name="PARAMETERS" value="run python -c &quot;import asyncio; from web_analyzer_mcp.server import extract_page_summary; print(asyncio.run(extract_page_summary('$Prompt$')))&quot;" />
      <option name="WORKING_DIRECTORY" value="$ProjectFileDir$/web-analyzer-mcp" />
    </exec>
  </tool>
  
  <tool name="RAG Content" description="Extract content for RAG" showInMainMenu="false" showInEditor="true" showInProject="false" showInSearchPopup="false" disabled="false" useConsole="true" showConsoleOnStdOut="false" showConsoleOnStdErr="false" synchronizeAfterRun="true">
    <exec>
      <option name="COMMAND" value="uv" />
      <option name="PARAMETERS" value="run python -c &quot;import asyncio; from web_analyzer_mcp.server import extract_content_for_rag; print(asyncio.run(extract_content_for_rag('$Prompt$')))&quot;" />
      <option name="WORKING_DIRECTORY" value="$ProjectFileDir$/web-analyzer-mcp" />
    </exec>
  </tool>
</toolSet>
```

## Usage

### Via External Tools

1. Right-click in the editor or project panel
2. Select `External Tools > Web Analyzer - [Tool Name]`
3. Enter the URL when prompted

### Via Run Configuration

1. Select the "Web Analyzer MCP Server" configuration
2. Run it to start the server
3. Use MCP client tools to connect

### Via Terminal

Open PyCharm terminal and run:

```bash
cd web-analyzer-mcp
uv run web-analyzer-mcp
```

## Integration with PyCharm Features

### Code Generation

Create a Live Template for quick MCP tool usage:

1. Go to `File > Settings > Editor > Live Templates`
2. Add a new template:
   - **Abbreviation:** `mcpweb`
   - **Template text:**
     ```python
     import asyncio
     from web_analyzer_mcp.server import $TOOL$
     
     result = asyncio.run($TOOL$("$URL$"))
     print(result)
     ```

### File Watchers

Set up a file watcher to automatically analyze URLs from files:

1. Go to `File > Settings > Tools > File Watchers`
2. Add a new watcher:
   - **File type:** `Text files`
   - **Scope:** `Project Files`
   - **Program:** `uv`
   - **Arguments:** `run python -c "import asyncio; from web_analyzer_mcp.server import extract_page_summary; [print(asyncio.run(extract_page_summary(line.strip()))) for line in open('$FilePath$') if line.strip().startswith('http')]"`

## Debugging

### Debug Server

1. Create a debug configuration:
   - **Script:** `/path/to/web-analyzer-mcp/src/web_analyzer_mcp/server.py`
   - **Working directory:** `/path/to/web-analyzer-mcp`
   - **Environment:** `LOG_LEVEL=DEBUG`

2. Set breakpoints in the server code
3. Run in debug mode

### Check Dependencies

```python
# In PyCharm Python Console
import sys
sys.path.append('/path/to/web-analyzer-mcp/src')
import web_analyzer_mcp
print(web_analyzer_mcp.__version__)
```

## Troubleshooting

### Common Issues

1. **Module not found:**
   - Check PYTHONPATH includes `/path/to/web-analyzer-mcp/src`
   - Verify virtual environment is activated

2. **uv command not found:**
   - Add uv to PyCharm's PATH
   - Use full path to uv executable

3. **Permission errors:**
   - Ensure PyCharm has permission to execute external tools
   - Check file permissions on the project directory

### Logging

Enable detailed logging in PyCharm:

1. Go to `Help > Diagnostic Tools > Debug Log Settings`
2. Add: `com.intellij.execution`
3. Restart PyCharm and check logs in `Help > Show Log in Files`

## Advanced Features

### Custom Plugin Development

If you want to create a custom PyCharm plugin for better integration:

1. Create a new IntelliJ Platform Plugin project
2. Implement MCP client functionality
3. Add tool windows and actions for web analysis tools

### Macro Integration

Create macros for common tasks:

```python
# PyCharm Macro
import asyncio
from web_analyzer_mcp.server import discover_subpages, extract_page_summary

def analyze_website():
    url = input("Enter website URL: ")
    
    # Discover subpages
    subpages = asyncio.run(discover_subpages(url, max_depth=2, max_pages=10))
    
    # Summarize each page
    for page in subpages[:5]:  # Limit to first 5 pages
        summary = asyncio.run(extract_page_summary(page))
        print(f"{page}: {summary}")
```