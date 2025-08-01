# Use Python 3.11 slim image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        libc6-dev \
        libffi-dev \
        libssl-dev \
        curl \
        netcat-openbsd \
        pkg-config \
        libfreetype6-dev \
        libpng-dev \
        libjpeg-dev \
        zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Create necessary directories with proper permissions
RUN mkdir -p /app/logs /app/static/css /app/static/js /app/uploads /app/instance /app/backups \
    && chmod 755 /app/logs /app/static /app/uploads /app/instance /app/backups

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Make entrypoint executable
RUN chmod +x docker-entrypoint.sh

# Create non-root user and set permissions
RUN adduser --disabled-password --gecos '' appuser \
    && chown -R appuser:appuser /app \
    && chmod -R 755 /app/logs /app/uploads /app/instance /app/backups

USER appuser

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Use entrypoint script
ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["python", "app.py"]
