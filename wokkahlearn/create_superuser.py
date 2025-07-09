import os
import django

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "wokkahlearn.settings")
django.setup()

from django.contrib.auth import get_user_model
import os

User = get_user_model()

email = "6testadmin@wokkahlearn.com"
password = "6testadmin123"

if not User.objects.filter(email=email).exists():
    print("Creating superuser...")
    User.objects.create_superuser(email=email, password=password, username=email)
    print(f"✅ Superuser created: {email} / {password}")
else:
    print(f"✅ Superuser already exists: {email}")

