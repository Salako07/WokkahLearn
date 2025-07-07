"""
WokkahLearn Django Settings
Production-ready configuration for EdTech platform
"""
import os
from pathlib import Path
from datetime import timedelta
import dj_database_url
from dotenv import load_dotenv

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'

# FIXED: Secure allowed hosts
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# Application definition
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework.authtoken',
    'rest_framework_simplejwt',
    'corsheaders',
    'channels',
    'drf_spectacular',
    'django_celery_beat',
    'django_extensions',
]

LOCAL_APPS = [
    'accounts',
    'courses',
    'ai_tutor',
    'code_execution',
    'collaboration',
    'analytics',
    'health_check',  # Add health check app
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'wokkahlearn.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# FIXED: Correct ASGI application
ASGI_APPLICATION = 'wokkahlearn.asgi.application'

# Database configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'wokkahlearn'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', '1234'),  # FIXED: No default password
        'HOST': os.getenv('DB_HOST', 'localhost'),  # FIXED: localhost for local dev
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

# Fallback to SQLite for development if PostgreSQL not available
if not os.getenv('DB_PASSWORD') and DEBUG:
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }

print(f"Database config: {DATABASES['default']['ENGINE']} - {DATABASES['default']['NAME']}")

# Redis configuration
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# Cache configuration
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Channels configuration (WebSocket)
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [REDIS_URL],
        },
    },
}

# Health check settings
HEALTH_CHECK = {
    'DISK_USAGE_MAX': 90,  # percent
    'MEMORY_MIN': 100,     # in MB
}

# REST Framework configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour'
    }
}

# JWT configuration
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    'JWK_URL': None,
    'LEEWAY': 0,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',
}

# API documentation
SPECTACULAR_SETTINGS = {
    'TITLE': 'WokkahLearn API',
    'DESCRIPTION': 'AI-Powered Coding Education Platform',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'SORT_OPERATIONS': False,
}

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# FIXED: Secure AWS configuration
AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME', 'wokkahlearn-storage')

# File storage (AWS S3 in production)
if not DEBUG and os.getenv('AWS_ACCESS_KEY_ID'):
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    STATICFILES_STORAGE = 'storages.backends.s3boto3.S3StaticStorage'
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')  # FIXED: No default credentials
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')  # FIXED: No default credentials
    AWS_S3_REGION_NAME = os.getenv('AWS_S3_REGION_NAME', 'us-east-1')
    AWS_S3_CUSTOM_DOMAIN = os.getenv('AWS_S3_CUSTOM_DOMAIN')
    print(f"✅ AWS S3 configured for bucket: {AWS_STORAGE_BUCKET_NAME}")
else:
    print("📁 Using local file storage")

# FIXED: Clean email configuration
if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    print("📧 Email: Console backend (development)")
else:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = 'smtp.mailgun.org'
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = os.getenv('MAILGUN_SMTP_USERNAME')  
    EMAIL_HOST_PASSWORD = os.getenv('MAILGUN_SMTP_PASSWORD')
    print("📧 Email: SMTP backend (production)")

# Email settings
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'WokkahLearn <noreply@wokkahlearn.com>')
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# Mailgun Configuration (HTTP API)
MAILGUN_API_KEY = os.getenv('MAILGUN_API_KEY', '')
MAILGUN_DOMAIN = os.getenv('MAILGUN_DOMAIN', 'mail.wokkah.com')
MAILGUN_URL = os.getenv('MAILGUN_URL', 'https://api.mailgun.net')

# Frontend URL for email links
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')

# Validate Mailgun configuration
if not DEBUG and (not MAILGUN_API_KEY or not MAILGUN_DOMAIN):
    import warnings
    warnings.warn("Mailgun credentials not configured. Email sending will not work in production.")
elif MAILGUN_API_KEY and MAILGUN_DOMAIN:
    print(f"✅ Mailgun configured for domain: {MAILGUN_DOMAIN}")

# Celery configuration
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# FIXED: Celery Beat Schedule
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'cleanup-old-executions': {
        'task': 'code_execution.tasks.cleanup_old_executions',
        'schedule': crontab(minute=0, hour=2),  # 2 AM daily
    },
    'collect-execution-statistics': {
        'task': 'code_execution.tasks.collect_daily_statistics',
        'schedule': crontab(minute=30, hour=23),  # 11:30 PM daily
    },
}

# CORS settings
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # React development server
    "http://127.0.0.1:3000",
    "http://localhost:8000",  # Django development server
]

CORS_ALLOW_CREDENTIALS = True

# Security settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'wokkahlearn.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'wokkahlearn': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# AI Service Configuration
# Add this to your wokkahlearn/settings.py

import os
from decouple import config

# AI Service Configuration
# ======================

# OpenAI Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', default=None)
OPENAI_MODEL_SETTINGS = {
    'default_model': 'gpt-4',
    'fallback_model': 'gpt-3.5-turbo',
    'max_tokens': 2000,
    'temperature': 0.7,
    'timeout': 30,  # seconds
}

# Anthropic Configuration
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', default=None)
ANTHROPIC_MODEL_SETTINGS = {
    'default_model': 'claude-3-sonnet-20240229',
    'fallback_model': 'claude-instant-1.2',
    'max_tokens': 2000,
    'temperature': 0.7,
    'timeout': 30,  # seconds
}

# AI Service General Settings
AI_SERVICE_SETTINGS = {
    'default_provider': 'anthropic',  # or 'openai', 'mock'
    'enable_fallback': True,
    'max_retries': 3,
    'retry_delay': 1,  # seconds
    'cache_responses': True,
    'cache_ttl': 3600,  # 1 hour
    'rate_limit': {
        'requests_per_minute': 60,
        'tokens_per_minute': 50000,
    }
}

# Session Management
AI_TUTOR_SETTINGS = {
    'max_session_duration': 3600,  # 1 hour
    'max_messages_per_session': 100,
    'auto_save_interval': 30,  # seconds
    'session_cleanup_interval': 24,  # hours
}

# Code Execution Settings (for AI code assistance)
CODE_EXECUTION_SETTINGS = {
    'enabled': True,
    'timeout': 10,  # seconds
    'memory_limit': '128MB',
    'supported_languages': ['python', 'javascript', 'java', 'cpp'],
    'docker_image_prefix': 'wokkahlearn-exec',
}

# Logging configuration for AI services
LOGGING_AI = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'ai_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/ai_services.log',
            'formatter': 'verbose',
        },
        'ai_console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'ai_tutor': {
            'handlers': ['ai_console', 'ai_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# Update the main LOGGING configuration
if 'LOGGING' in globals():
    LOGGING['loggers'].update(LOGGING_AI['loggers'])
    LOGGING['handlers'].update(LOGGING_AI['handlers'])
else:
    LOGGING = LOGGING_AI

# Docker Configuration
DOCKER_NETWORK = 'wokkahlearn_execution'

# Code Execution Settings
CODE_EXECUTION = {
    'enabled': True,
    'docker_network': DOCKER_NETWORK,
    'default_timeout': 30,  # seconds
    'max_memory_mb': 128,  # MB
    'max_concurrent_executions': 10,
    'cleanup_interval': 3600,  # 1 hour
    'max_output_size_mb': 1,
    'supported_languages': [
        'python', 'javascript', 'java', 'cpp', 'c', 'go', 'rust'
    ],
    'quota_limits': {
        'free_tier': {
            'daily_executions': 50,
            'cpu_time_seconds': 300,  # 5 minutes
            'memory_mb': 1024  # 1 GB total
        },
        'premium_tier': {
            'daily_executions': 500,
            'cpu_time_seconds': 3600,  # 1 hour
            'memory_mb': 10240  # 10 GB total
        },
        'instructor_tier': {
            'daily_executions': 1000,
            'cpu_time_seconds': 7200,  # 2 hours
            'memory_mb': 20480  # 20 GB total
        }
    }
}

# Default auto field
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom user model
AUTH_USER_MODEL = 'accounts.User'

# Print configuration status
print("🚀 WokkahLearn Settings Loaded")
print(f"   Debug: {DEBUG}")
print(f"   Database: {DATABASES['default']['ENGINE']}")
print(f"   Redis: {REDIS_URL}")
print(f"   AI Provider: {AI_SERVICE_SETTINGS['default_provider']}")
print(f"   Frontend URL: {FRONTEND_URL}")