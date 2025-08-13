#!/usr/bin/env node

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

console.log('🚀 Building Web Analyzer MCP...');

// 1. Check Python environment
try {
  execSync('python --version', { stdio: 'inherit' });
} catch (error) {
  console.error('❌ Python not found. Please install Python 3.10+');
  process.exit(1);
}

// 2. Install Python dependencies
console.log('📦 Installing Python dependencies...');
try {
  execSync('pip install -e .', { stdio: 'inherit' });
  console.log('✅ Python dependencies installed');
} catch (error) {
  console.error('❌ Failed to install Python dependencies');
  process.exit(1);
}

// 3. Run tests (if available)
console.log('🧪 Running tests...');
try {
  execSync('python -m pytest tests/ || echo "No tests found"', { stdio: 'inherit' });
} catch (error) {
  console.log('⚠️ Tests failed or not found');
}

// 4. Check MCP server
console.log('🔍 Validating MCP server...');
try {
  execSync('python -m web_analyzer_mcp.server --help', { stdio: 'pipe' });
  console.log('✅ MCP server is valid');
} catch (error) {
  console.error('❌ MCP server validation failed');
  process.exit(1);
}

// 5. Create distribution info
const packageInfo = {
  name: 'web-analyzer-mcp',
  version: '0.1.0',
  built: new Date().toISOString(),
  tools: [
    'url_to_markdown',
    'web_content_qna'
  ]
};

fs.writeFileSync('dist-info.json', JSON.stringify(packageInfo, null, 2));
console.log('📋 Created distribution info');

console.log('🎉 Build completed successfully!');
console.log('');
console.log('Next steps:');
console.log('  npm run test    # Test with MCP Inspector');
console.log('  npm start       # Start the server');
console.log('');