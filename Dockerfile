FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for building Python packages
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p backend/data/chroma_db backend/data/dual_source_chroma backend/data/uploads

# Expose port (Render/AWS will set PORT env var)
EXPOSE 8000

# Copy startup script
COPY docker-start.sh /app/docker-start.sh
RUN chmod +x /app/docker-start.sh

# Set working directory to root
WORKDIR /app

# Run application (PORT env var will be set by AWS/Render)
CMD ["/app/docker-start.sh"]

