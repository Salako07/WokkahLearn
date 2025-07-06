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