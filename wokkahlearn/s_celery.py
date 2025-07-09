import django, os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "wokkahlearn.settings")
django.setup()

from django.db import connection;

cursor = connection.cursor()
cursor.execute('SELECT 1 FROM django_celery_beat_periodictask LIMIT 1')
print('✅ Celery Beat tables verified')
