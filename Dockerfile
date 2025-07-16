# Multi-stage build for Python application
FROM python:3.11-slim AS builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock* ./
COPY README.md ./

# Create virtual environment and install dependencies
RUN uv sync --frozen --no-dev

# Production stage
FROM python:3.11-slim AS runtime

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install Chrome for Selenium (optional for advanced scraping)
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Install ChromeDriver
RUN CHROMEDRIVER_VERSION=`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE` && \
    mkdir -p /opt/chromedriver-$CHROMEDRIVER_VERSION && \
    curl -sS -o /tmp/chromedriver_linux64.zip http://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip && \
    unzip -qq /tmp/chromedriver_linux64.zip -d /opt/chromedriver-$CHROMEDRIVER_VERSION && \
    rm /tmp/chromedriver_linux64.zip && \
    chmod +x /opt/chromedriver-$CHROMEDRIVER_VERSION/chromedriver && \
    ln -fs /opt/chromedriver-$CHROMEDRIVER_VERSION/chromedriver /usr/local/bin/chromedriver

# Copy virtual environment from builder stage
COPY --from=builder /app/.venv /app/.venv

# Set working directory
WORKDIR /app

# Copy application code
COPY mcp_webanalyzer/ mcp_webanalyzer/
COPY README.md ./
COPY .env* ./

# Make sure we use the virtual environment
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app"

# Create directories for logs and data
RUN mkdir -p /app/logs /app/data

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Health check for API server
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose ports
EXPOSE 8000 9090

# Default command (can be overridden)
CMD ["python", "-m", "mcp_webanalyzer.api_server"]