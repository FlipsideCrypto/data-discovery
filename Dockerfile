# Use UV's official Python image with UV pre-installed
FROM ghcr.io/astral-sh/uv:python3.10-bookworm-slim

# Set working directory
WORKDIR /app

# Set UV cache directory to our mounted cache
ENV UV_CACHE_DIR=/tmp/uv-cache

# Copy project files first (including README.md)
COPY pyproject.toml uv.lock README.md ./

# Install dependencies first (for better layer caching)
RUN --mount=type=cache,target=/tmp/uv-cache \
    uv sync --locked --no-install-project

# Copy the project code
COPY src/ ./src/

# Install the project
RUN --mount=type=cache,target=/tmp/uv-cache \
    uv sync --locked

# Set environment variables
ENV DEPLOYMENT_MODE=api
ENV DEBUG_MODE=false
ENV LOG_LEVEL=INFO
ENV MAX_PROJECTS=50

# Add the virtual environment to PATH
ENV PATH="/app/.venv/bin:$PATH"

# Expose port
EXPOSE 8000

# Run the FastAPI application
CMD ["uvicorn", "src.data_discovery.main:app", "--host", "0.0.0.0", "--port", "8000"]