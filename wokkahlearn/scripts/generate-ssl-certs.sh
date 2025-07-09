#!/bin/bash
# scripts/generate-ssl-certs.sh - Windows-compatible SSL certificate generation

set -e

echo "🔐 Generating SSL certificates for WokkahLearn..."

# Create SSL directory
mkdir -p nginx/ssl

# Certificate configuration
DOMAIN="wokkahlearn.com"
COUNTRY="US"
STATE="California"
CITY="San Francisco"
ORG="WokkahLearn"
ORG_UNIT="IT Department"
EMAIL="admin@wokkahlearn.com"

# Generate private key
echo "📋 Generating private key..."
openssl genrsa -out nginx/ssl/key.pem 4096

# Create certificate configuration file (avoids subject line issues)
cat > nginx/ssl/cert.conf << EOF
[req]
default_bits = 4096
prompt = no
default_md = sha256
distinguished_name = dn
req_extensions = v3_req

[dn]
C=${COUNTRY}
ST=${STATE}
L=${CITY}
O=${ORG}
OU=${ORG_UNIT}
CN=${DOMAIN}
emailAddress=${EMAIL}

[v3_req]
basicConstraints = CA:FALSE
keyUsage = nonRepudiation, digitalSignature, keyEncipherment
subjectAltName = @alt_names

[alt_names]
DNS.1 = ${DOMAIN}
DNS.2 = www.${DOMAIN}
DNS.3 = localhost
DNS.4 = *.${DOMAIN}
IP.1 = 127.0.0.1
IP.2 = ::1
EOF

# Generate certificate signing request using config file
echo "📋 Generating certificate signing request..."
openssl req -new -key nginx/ssl/key.pem -out nginx/ssl/cert.csr -config nginx/ssl/cert.conf

# Generate self-signed certificate
echo "📋 Generating self-signed certificate..."
openssl x509 -req -in nginx/ssl/cert.csr -signkey nginx/ssl/key.pem -out nginx/ssl/cert.pem -days 365 -extensions v3_req -extfile nginx/ssl/cert.conf

# Set proper permissions (Windows compatible)
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    # Windows permissions
    chmod 600 nginx/ssl/key.pem 2>/dev/null || echo "Note: Unable to set Unix permissions on Windows"
    chmod 644 nginx/ssl/cert.pem 2>/dev/null || echo "Note: Unable to set Unix permissions on Windows"
else
    # Unix permissions
    chmod 600 nginx/ssl/key.pem
    chmod 644 nginx/ssl/cert.pem
fi

# Clean up temporary files
rm nginx/ssl/cert.csr nginx/ssl/cert.conf

echo "✅ SSL certificates generated successfully!"
echo "📁 Certificates location: nginx/ssl/"
echo "🔑 Private key: nginx/ssl/key.pem"
echo "📜 Certificate: nginx/ssl/cert.pem"
echo ""
echo "⚠️  These are self-signed certificates for development."
echo "   Browsers will show a security warning. Click 'Advanced' -> 'Proceed to localhost (unsafe)'"
echo ""
echo "🚀 For production, consider using Let's Encrypt certificates."

# Verify certificate (Windows compatible)
echo ""
echo "📋 Certificate details:"
if command -v openssl &> /dev/null; then
    openssl x509 -in nginx/ssl/cert.pem -text -noout | grep -E "(Subject:|DNS:|IP Address:|Not Before|Not After)" || echo "Certificate verification completed"
else
    echo "OpenSSL not found in PATH, but certificates should be valid"
fi

echo ""
echo "🎯 Next steps:"
echo "1. Update your nginx/nginx.conf with the SSL configuration"
echo "2. Update your docker-compose.yml nginx service"
echo "3. Run: docker-compose down && docker-compose build nginx && docker-compose up -d"