# Use Python 3.13 slim image as base
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install system dependencies required for the application
RUN apt-get update && apt-get install -y \
    # Required for python-magic
    libmagic1 \
    # Required for some document processing
    libpoppler-cpp-dev \
    # Required for building some Python packages
    gcc \
    g++ \
    # Required for health checks
    curl \
    # Clean up to reduce image size
    && rm -rf /var/lib/apt/lists/*

# Install uv - fast Python package installer
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy dependency files
COPY pyproject.toml ./
COPY uv.lock ./

# Install dependencies using UV sync (creates virtual environment automatically)
RUN uv sync --frozen --no-dev

# Set UV environment variables to use the project virtual environment
ENV UV_PROJECT_ENVIRONMENT=/app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Copy the application code
COPY . .

# Create logs directory with proper permissions
RUN mkdir -p logs && chmod 755 logs

# Expose the port the app runs on
EXPOSE 8000

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Health check to ensure the application is running
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Command to run the application
CMD ["fastapi", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8000"]