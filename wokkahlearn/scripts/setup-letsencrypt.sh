set -e

# Configuration
DOMAIN="wokkahlearn.com"
EMAIL="admin@wokkahlearn.com"
STAGING=false  # Set to true for testing

echo "🔐 Setting up Let's Encrypt SSL for ${DOMAIN}..."

# Create necessary directories
mkdir -p nginx/ssl
mkdir -p certbot/conf
mkdir -p certbot/www

# Create docker-compose override for Let's Encrypt
cat > docker-compose.letsencrypt.yml << EOF
version: '3.8'

services:
  nginx:
    volumes:
      - ./certbot/conf:/etc/letsencrypt:ro
      - ./certbot/www:/var/www/certbot:ro
    command: "/bin/sh -c 'while :; do sleep 6h & wait \${!}; nginx -s reload; done & nginx -g \"daemon off;\"'"

  certbot:
    image: certbot/certbot:latest
    restart: unless-stopped
    volumes:
      - ./certbot/conf:/etc/letsencrypt
      - ./certbot/www:/var/www/certbot
    entrypoint: "/bin/sh -c 'trap exit TERM; while :; do certbot renew; sleep 12h & wait \${!}; done;'"
EOF

# Create initial nginx config for Let's Encrypt challenge
cat > nginx/nginx-letsencrypt.conf << EOF
server {
    listen 80;
    server_name ${DOMAIN} www.${DOMAIN};
    
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    location / {
        return 301 https://\$server_name\$request_uri;
    }
}
EOF

echo "📋 Starting nginx with Let's Encrypt challenge support..."

# Start nginx for the challenge
docker-compose -f docker-compose.yml -f docker-compose.letsencrypt.yml up -d nginx

# Wait for nginx to be ready
sleep 10

# Generate the certificate
if [ "$STAGING" = true ]; then
    echo "📋 Generating staging certificate (for testing)..."
    docker-compose -f docker-compose.yml -f docker-compose.letsencrypt.yml run --rm certbot \
        certonly --webroot -w /var/www/certbot \
        --staging \
        --email $EMAIL \
        --agree-tos \
        --no-eff-email \
        -d $DOMAIN -d www.$DOMAIN
else
    echo "📋 Generating production certificate..."
    docker-compose -f docker-compose.yml -f docker-compose.letsencrypt.yml run --rm certbot \
        certonly --webroot -w /var/www/certbot \
        --email $EMAIL \
        --agree-tos \
        --no-eff-email \
        -d $DOMAIN -d www.$DOMAIN
fi

# Update nginx configuration to use Let's Encrypt certificates
sed -i 's|/etc/nginx/ssl/cert.pem|/etc/letsencrypt/live/'$DOMAIN'/fullchain.pem|g' nginx/nginx.conf
sed -i 's|/etc/nginx/ssl/key.pem|/etc/letsencrypt/live/'$DOMAIN'/privkey.pem|g' nginx/nginx.conf

# Restart nginx with SSL
docker-compose -f docker-compose.yml -f docker-compose.letsencrypt.yml restart nginx

echo "✅ Let's Encrypt SSL certificates configured successfully!"
echo "🌐 Your site should now be available at: https://$DOMAIN"
echo "🔄 Certificates will auto-renew every 12 hours"

# Test the certificate
echo ""
echo "📋 Testing SSL certificate..."
openssl s_client -connect $DOMAIN:443 -servername $DOMAIN < /dev/null 2>/dev/null | openssl x509 -noout -dates