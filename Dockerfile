# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create cache directory for embeddings
RUN mkdir -p .cache

# Expose port (Railway will set PORT env var)
EXPOSE 8000

# Run the application (use PORT from environment if available)
CMD sh -c "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"
