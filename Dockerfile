# Multi-stage build for optimal image size
FROM python:3.11-slim as builder

WORKDIR /app

# Copy only requirements first for better layer caching
COPY pyproject.toml ./
COPY web_analyzer_mcp/ ./web_analyzer_mcp/

# Build wheel
RUN pip install --no-cache-dir build && \
    python -m build --wheel

# Final stage
FROM python:3.11-slim

# Install Chrome/Chromium for Selenium
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        chromium \
        chromium-driver \
        curl \
        && rm -rf /var/lib/apt/lists/* \
        && apt-get clean

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash mcp && \
    mkdir -p /app && \
    chown -R mcp:mcp /app

WORKDIR /app
USER mcp

# Copy wheel from builder stage
COPY --from=builder --chown=mcp:mcp /app/dist/*.whl ./

# Install the wheel
RUN pip install --no-cache-dir --user *.whl && \
    rm -f *.whl

# Set environment variables
ENV PATH="/home/mcp/.local/bin:$PATH"
ENV PYTHONPATH="/home/mcp/.local/lib/python3.11/site-packages:$PYTHONPATH"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import web_analyzer_mcp; print('OK')" || exit 1

# Default command to run the MCP server
CMD ["python", "-m", "web_analyzer_mcp.server"]
