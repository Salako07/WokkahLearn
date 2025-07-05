#!/bin/sh

# Wait for database
echo "Waiting for Postgres..."
while ! nc -z db 5432; do
  sleep 1
done
echo "Postgres is up!"

# Apply database migrations
echo "Applying migrations..."
python manage.py makemigrations --noinput
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start the server
exec "$@"
