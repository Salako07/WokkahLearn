#!/bin/bash

# WokkahLearn Nginx Fix Script
set -e

echo "🔧 WokkahLearn Nginx Fix Script"
echo "================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    print_error "docker-compose is not installed or not in PATH"
    exit 1
fi

# Stop existing containers
print_status "Stopping existing containers..."
docker-compose down --remove-orphans || true

# Backup original nginx.conf if it exists
if [ -f "nginx/nginx.conf" ]; then
    print_warning "Backing up original nginx.conf to nginx.conf.backup"
    cp nginx/nginx.conf nginx/nginx.conf.backup
fi

# Check if nginx directory exists
if [ ! -d "nginx" ]; then
    print_status "Creating nginx directory..."
    mkdir -p nginx
fi

print_status "Creating fixed nginx configuration..."

# Create the fixed nginx.conf
cat > nginx/nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log warn;

    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 100M;

    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json image/svg+xml;

    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=login:10m rate=1r/s;

    upstream backend {
        server backend:8000;
        keepalive 32;
    }

    server {
        listen 80;
        server_name localhost;

        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header Referrer-Policy "no-referrer-when-downgrade" always;

        # API routes
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }

        # Admin routes
        location /admin/ {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # WebSocket routes - FIXED TRUNCATED LINE
        location /ws/ {
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_cache_bypass $http_upgrade;
        }

        # Static files
        location /static/ {
            alias /var/www/static/;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }

        # Media files
        location /media/ {
            alias /var/www/media/;
            expires 30d;
            add_header Cache-Control "public";
        }

        # Health check
        location /health/ {
            proxy_pass http://backend;
            access_log off;
        }

        # Frontend (for development)
        location / {
            return 404;
        }
    }
}
EOF

print_status "Creating nginx Dockerfile..."

# Create nginx Dockerfile
cat > nginx/Dockerfile << 'EOF'
FROM nginx:1.25-alpine

# Remove default nginx configuration
RUN rm /etc/nginx/conf.d/default.conf

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Create directories for static and media files
RUN mkdir -p /var/www/static /var/www/media

# Create nginx user and set permissions
RUN chown -R nginx:nginx /var/www /var/cache/nginx /var/run /var/log/nginx

# Expose port 80
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/health/ || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
EOF

# Test nginx configuration syntax
print_status "Testing nginx configuration syntax..."
docker run --rm -v $(pwd)/nginx/nginx.conf:/etc/nginx/nginx.conf:ro nginx:1.25-alpine nginx -t

if [ $? -eq 0 ]; then
    print_status "✅ Nginx configuration syntax is valid!"
else
    print_error "❌ Nginx configuration has syntax errors!"
    exit 1
fi

# Build and start services
print_status "Building nginx service..."
docker-compose build nginx

print_status "Starting all services..."
docker-compose up -d

# Wait a moment for services to start
sleep 10

# Check service status
print_status "Checking service status..."
docker-compose ps

# Test health endpoints
print_status "Testing health endpoints..."

echo -n "Testing backend health endpoint... "
if curl -s -f http://localhost:8000/health/ > /dev/null 2>&1; then
    echo -e "${GREEN}✅ OK${NC}"
else
    echo -e "${RED}❌ FAILED${NC}"
    print_warning "Backend may still be starting up. Check logs with: docker-compose logs backend"
fi

echo -n "Testing nginx proxy health endpoint... "
if curl -s -f http://localhost/health/ > /dev/null 2>&1; then
    echo -e "${GREEN}✅ OK${NC}"
else
    echo -e "${RED}❌ FAILED${NC}"
    print_warning "Nginx proxy not working. Check logs with: docker-compose logs nginx"
fi

echo
print_status "🎉 Nginx fix completed!"
echo
echo "Next steps:"
echo "1. Check all services are running: docker-compose ps"
echo "2. View logs if needed: docker-compose logs nginx"
echo "3. Test your application at: http://localhost"
echo
echo "If you encounter issues, check the troubleshooting guide."