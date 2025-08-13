# 🔍 Web Analyzer MCP

<a href="https://glama.ai/mcp/servers/@kimdonghwi94/web-analyzer-mcp">
  <img width="380" height="200" src="https://glama.ai/mcp/servers/@kimdonghwi94/web-analyzer-mcp/badge" alt="WebAnalyzer MCP server" />
</a>

A powerful MCP (Model Context Protocol) server for intelligent web content analysis and summarization. Built with FastMCP, this server provides smart web scraping, content extraction, and AI-powered question-answering capabilities.

## ✨ Features

### 🎯 Core Tools

1. **`url_to_markdown`** - Extract and summarize web pages to markdown
   - Analyzes content importance using custom algorithms
   - Removes ads, navigation, and irrelevant content
   - Keeps only essential information (tables, images, key text)
   - Outputs structured markdown perfect for analysis

2. **`web_content_qna`** - AI-powered Q&A about web content
   - Extracts relevant content sections from web pages
   - Uses intelligent chunking and relevance matching
   - Answers questions using OpenAI GPT models

### 🚀 Key Features

- **Smart Content Ranking**: Algorithm-based content importance scoring
- **Essential Content Only**: Removes clutter, keeps what matters
- **Multi-IDE Support**: Works with Claude Desktop, Cursor, VS Code, PyCharm
- **Flexible Models**: Choose from GPT-3.5, GPT-4, GPT-4 Turbo, or GPT-5

## 📦 Installation

### Prerequisites
- Python 3.10+
- Chrome/Chromium browser (for Selenium)
- OpenAI API key (for Q&A functionality)

### Install the Package

```bash
pip install web-analyzer-mcp
```

### Or Install from Source

```bash
git clone https://github.com/kimdonghwi94/web-analyzer-mcp.git
cd web-analyzer-mcp
pip install -e .
```

### Modern Development with npm

```bash
# Clone and setup
git clone https://github.com/kimdonghwi94/web-analyzer-mcp.git
cd web-analyzer-mcp

# Install dependencies (both Node.js and Python)
npm install
npm run install

# Build the project
npm run build

# Test with MCP Inspector
npm test

# Start development server
npm run dev
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file or set environment variables:

```env
OPENAI_API_KEY=your_openai_api_key_here
```

### IDE/Editor Integration

<details>
<summary><b>Claude Desktop</b></summary>

Add to your Claude Desktop configuration file:

**Windows**: `%APPDATA%/Claude/claude_desktop_config.json`
**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Linux**: `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "web-analyzer": {
      "command": "python",
      "args": ["-m", "web_analyzer_mcp.server"],
      "env": {
        "OPENAI_API_KEY": "your_openai_api_key_here",
        "OPENAI_MODEL": "gpt-3.5-turbo"
      }
    }
  }
}
```

*Note: `OPENAI_MODEL` is optional - defaults to gpt-3.5-turbo if not specified*
</details>

<details>
<summary><b>Cursor IDE</b></summary>

Add to your Cursor settings (`File > Preferences > Settings > Extensions > MCP`):

```json
{
  "mcp.servers": {
    "web-analyzer": {
      "command": "python",
      "args": ["-m", "web_analyzer_mcp.server"],
      "env": {
        "OPENAI_API_KEY": "your_openai_api_key_here",
        "OPENAI_MODEL": "gpt-4"
      }
    }
  }
}
```

*Note: `OPENAI_MODEL` is optional - defaults to gpt-3.5-turbo if not specified*
</details>

<details>
<summary><b>Claude Code (VS Code Extension)</b></summary>

Add to your VS Code settings.json:

```json
{
  "claude-code.mcpServers": {
    "web-analyzer": {
      "command": "python",
      "args": ["-m", "web_analyzer_mcp.server"],
      "cwd": "${workspaceFolder}/web-analyzer-mcp",
      "env": {
        "OPENAI_API_KEY": "your_openai_api_key_here",
        "OPENAI_MODEL": "gpt-4-turbo"
      }
    }
  }
}
```

*Note: `OPENAI_MODEL` is optional - defaults to gpt-3.5-turbo if not specified*
</details>

<details>
<summary><b>PyCharm (with MCP Plugin)</b></summary>

Create a run configuration in PyCharm:

1. Go to `Run > Edit Configurations`
2. Add new Python configuration:
   - **Script path**: `/path/to/web_analyzer_mcp/server.py`
   - **Parameters**: (leave empty)
   - **Environment variables**:
     ```
     OPENAI_API_KEY=your_openai_api_key_here
     OPENAI_MODEL=gpt-4o
     ```
   - **Working directory**: `/path/to/web-analyzer-mcp`

*Note: `OPENAI_MODEL` is optional - defaults to gpt-3.5-turbo if not specified*

Or use the external tool configuration:
```xml
<tool name="Web Analyzer MCP" description="Start Web Analyzer MCP Server" showInMainMenu="false" showInEditor="false" showInProject="false" showInSearchPopup="false">
  <exec>
    <option name="COMMAND" value="python" />
    <option name="PARAMETERS" value="-m web_analyzer_mcp.server" />
    <option name="WORKING_DIRECTORY" value="$ProjectFileDir$" />
  </exec>
</tool>
```
</details>

## 🔨 Usage Examples

### Basic Web Content Extraction

```python
# Extract clean markdown from a web page
result = url_to_markdown("https://example.com/article")
print(result)
```

### Q&A about Web Content

```python
# Ask questions about web page content
answer = web_content_qna(
    url="https://example.com/documentation", 
    question="What are the main features of this product?"
)
print(answer)
```


## 🎛️ Tool Descriptions

### `url_to_markdown`
Converts web pages to clean markdown format with essential content extraction.

**Parameters:**
- `url` (string): The web page URL to analyze

**Returns:** Clean markdown content with structured data preservation

### `web_content_qna` 
Answers questions about web page content using intelligent content analysis.

**Parameters:**
- `url` (string): The web page URL to analyze
- `question` (string): Question about the page content

**Returns:** AI-generated answer based on page content


## 🏗️ Architecture

### Content Extraction Pipeline

1. **URL Validation** - Ensures proper URL format
2. **HTML Fetching** - Uses Selenium for dynamic content
3. **Content Parsing** - BeautifulSoup for HTML processing
4. **Element Scoring** - Custom algorithm ranks content importance
5. **Content Filtering** - Removes duplicates and low-value content
6. **Markdown Conversion** - Structured output generation

### Q&A Processing Pipeline

1. **Content Chunking** - Intelligent text segmentation
2. **Relevance Scoring** - Matches content to questions
3. **Context Selection** - Picks most relevant chunks
4. **Answer Generation** - OpenAI GPT integration

## 🏗️ Project Structure

```
web-analyzer-mcp/
├── web_analyzer_mcp/          # Main Python package
│   ├── __init__.py           # Package initialization
│   ├── server.py             # FastMCP server with tools
│   ├── web_extractor.py      # Web content extraction engine
│   └── rag_processor.py      # RAG-based Q&A processor
├── scripts/                   # Build and utility scripts
│   └── build.js              # Node.js build script
├── README.md                 # English documentation
├── README.ko.md              # Korean documentation
├── package.json              # npm configuration and scripts
├── pyproject.toml            # Python package configuration
├── .env.example              # Environment variables template
└── dist-info.json            # Build information (generated)
```

## 🛠️ Development

### Modern Development Workflow

```bash
# Clone repository
git clone https://github.com/kimdonghwi94/web-analyzer-mcp.git
cd web-analyzer-mcp

# Setup environment
npm install              # Install Node.js dependencies
npm run install         # Install Python dependencies

# Development commands
npm run build           # Full build with validation
npm run dev            # Start development server
npm test               # Test with MCP Inspector
npm run lint           # Code formatting and linting
npm run typecheck      # Type checking
npm run clean          # Clean build artifacts
```

### Traditional Python Development

```bash
# Setup Python environment
pip install -e .[dev]

# Development commands
python -m web_analyzer_mcp.server  # Start server
python -m pytest tests/            # Run tests (if available)
python -m black web_analyzer_mcp/  # Format code
python -m mypy web_analyzer_mcp/   # Type checking
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📋 Roadmap

- [ ] Support for more content types (PDFs, videos)
- [ ] Multi-language content extraction
- [ ] Custom extraction rules
- [ ] Caching for frequently accessed content
- [ ] Webhook support for real-time updates

## ⚠️ Limitations

- Requires Chrome/Chromium for JavaScript-heavy sites
- OpenAI API key needed for Q&A functionality
- Rate limited to prevent abuse
- Some sites may block automated access

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙋‍♂️ Support

- Create an issue for bug reports or feature requests
- Contribute to discussions in the GitHub repository
- Check the [documentation](https://github.com/kimdonghwi94/web-analyzer-mcp) for detailed guides

## 🌟 Acknowledgments

- Built with [FastMCP](https://github.com/jlowin/fastmcp) framework
- Inspired by HTMLRAG techniques for web content processing
- Thanks to the MCP community for feedback and contributions

---

**Made with ❤️ for the MCP community**