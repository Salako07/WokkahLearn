# Use official Python image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=wokkahlearn.settings

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        netcat-traditional \
        curl \
        git && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy entrypoint script and make it executable
COPY backend/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Copy entire Django project into container
COPY . /app/

# Create media and static directories
RUN mkdir -p /app/media /app/staticfiles

# Create a non-root user
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port for development server
EXPOSE 8000

# Default command (overridden in docker-compose if needed)
CMD ["/app/entrypoint.sh", "python", "manage.py", "runserver", "0.0.0.0:8000"]
