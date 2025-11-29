# =============================================================================
# DOCKERFILE FOR RAILWAY DEPLOYMENT - AUTHORFLOW STUDIOS ENGINE
# =============================================================================

FROM python:3.11-slim

# Install system dependencies (ffmpeg for audio processing)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY apps/engine/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the engine application
COPY apps/engine/ .

# Set PYTHONPATH so absolute imports work (pipelines, agents, core, etc.)
ENV PYTHONPATH=/app

# Expose port (Railway sets PORT env var)
EXPOSE 8000

# Start the FastAPI server
CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
