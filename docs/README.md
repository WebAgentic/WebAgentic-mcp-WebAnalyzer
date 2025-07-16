# Documentation

This directory contains comprehensive documentation for the MCP WebAnalyzer.

## Documentation Structure

- `api/` - API documentation
- `guides/` - User guides and tutorials
- `development/` - Development documentation
- `deployment/` - Deployment guides
- `examples/` - Code examples

## Available Documentation

### API Documentation
- [API Reference](api/README.md) - Complete API documentation
- [Authentication](api/authentication.md) - Authentication methods
- [Rate Limiting](api/rate-limiting.md) - Rate limiting policies

### User Guides
- [Quick Start](../quick-start.md) - Quick start guide
- [Configuration](guides/configuration.md) - Configuration options
- [Troubleshooting](guides/troubleshooting.md) - Common issues and solutions

### Development
- [Architecture](../architecture.md) - System architecture
- [Contributing](development/contributing.md) - How to contribute
- [Testing](development/testing.md) - Testing guidelines

### Deployment
- [Local Deployment](../README.md) - Local development setup
- [Production Deployment](../REMOTE_DEPLOYMENT_GUIDE.md) - Production deployment
- [Docker Deployment](deployment/docker.md) - Docker deployment guide

## Building Documentation

```powershell
# Install documentation dependencies
pip install mkdocs mkdocs-material

# Serve documentation locally
mkdocs serve

# Build documentation
mkdocs build
```

## Contributing to Documentation

1. Write clear, concise documentation
2. Include code examples
3. Update documentation when code changes
4. Follow the existing structure and style