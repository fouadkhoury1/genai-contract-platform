# Multi-stage build for Django backend
FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Create and set work directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements/ requirements/
RUN pip install --no-cache-dir --user -r requirements/base.txt

# Production stage
FROM python:3.11-slim as production

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH=/home/app/.local/bin:$PATH

# Create app user
RUN groupadd -r app && useradd -r -g app app

# Create directories
RUN mkdir -p /home/app/web && \
    mkdir -p /home/app/web/logs && \
    mkdir -p /home/app/web/staticfiles

# Set work directory
WORKDIR /home/app/web

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependencies from builder stage
COPY --from=builder /root/.local /home/app/.local

# Copy project files
COPY . .

# Create logs directory and set permissions
RUN chown -R app:app /home/app/web

# Switch to app user
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/healthz/ || exit 1

# Run application
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"] 