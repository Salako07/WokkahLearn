"""
WokkahLearn Django Settings
Production-ready configuration for EdTech platform
"""
import os
from pathlib import Path
from datetime import timedelta
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'

#ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
ALLOWED_HOSTS =["*"]

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
    #'learning',
    'ai_tutor',
    'code_execution',
    'collaboration',
    'analytics',
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

#WSGI_APPLICATION = 'wokkahlearn.wsgi.application'
ASGI_APPLICATION = 'wokkahlearn.asgi.application'

# Database configuration

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'postgres'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', '1234'),
        'HOST': os.getenv('DB_HOST', 'db'),
        'PORT': os.getenv('DB_PORT', '5432'),
        #'OPTIONS': {
        #    'charset': 'utf8mb4',
        #},
    }
}

print (f"Database config:{DATABASES}")

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

# Add health check settings
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

AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME', 'wokka-staging')

print (f'Bucket name {AWS_STORAGE_BUCKET_NAME}')

# File storage (AWS S3 in production)
if not DEBUG:
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    STATICFILES_STORAGE = 'storages.backends.s3boto3.S3StaticStorage'
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID', 'DO00PYG7UMRW3Z9VDAKX')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY', 'ebmhAAhY+bkVF9WCtLmaVP+wmYkTb1QJ5XMdoR8UJaI')
    AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME', 'wokka-staging')
    AWS_S3_REGION_NAME = os.getenv('AWS_S3_REGION_NAME', 'nyc3')
    AWS_S3_CUSTOM_DOMAIN = "https://nyc3.digitaloceanspaces.com"

# Celery configuration
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# CORS settings
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # React development server
    "http://127.0.0.1:3000",
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
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
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
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
AI_SERVICE_URL = os.getenv('AI_SERVICE_URL', 'http://localhost:8001')

# Code execution configuration
CODE_EXECUTION_TIMEOUT = 30  # seconds
MAX_MEMORY_USAGE = 128  # MB
DOCKER_NETWORK = 'wokkahlearn_execution'

# Default auto field
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom user model
AUTH_USER_MODEL = 'accounts.User'

if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = 'smtp.mailgun.org'
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = os.getenv('MAILGUN_SMTP_USERNAME')  
    EMAIL_HOST_PASSWORD = os.getenv('MAILGUN_SMTP_PASSWORD') 

    # Default email settings
    DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'WokkahLearn <noreply@yourdomain.com>')
    SERVER_EMAIL = DEFAULT_FROM_EMAIL

    # Mailgun API Configuration (for advanced features)
    MAILGUN_API_KEY = os.getenv('MAILGUN_API_KEY')
    MAILGUN_DOMAIN = os.getenv('MAILGUN_DOMAIN') 
    FRONTEND_URL = os.getenv('FRONTEND_URL', 'https://wokkahlearn.com')



DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@wokkahlearn.com')
FRONTEND_URL = os.getenv('FRONTEND_URL', 'https://wokkahlearn.com')
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# Mailgun Configuration (HTTP API)
MAILGUN_API_KEY = os.getenv('MAILGUN_API_KEY', '')
MAILGUN_DOMAIN = os.getenv('MAILGUN_DOMAIN','mail.wokkah.com')  # mail.wokkah.com
MAILGUN_URL = os.getenv('MAILGUN_URL', 'https://api.mailgun.net')
MAIL_FROM_ADDRESS = os.getenv('MAIL_FROM_ADDRESS', 'Wokkah Learn <noreply@mail.wokkah.com>')

# Frontend URL for email links
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:8000/api/auth/')

# Email Backend (Optional - you can still use Django's email for other purposes)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'  # For development logging
DEFAULT_FROM_EMAIL = MAIL_FROM_ADDRESS

# Validate Mailgun configuration
if not MAILGUN_API_KEY or not MAILGUN_DOMAIN:
    import warnings
    warnings.warn("Mailgun credentials not configured. Email sending will not work.")
else:
    print(f"✅ Mailgun configured for domain: {MAILGUN_DOMAIN}")


# AI Configuration
AI_SERVICES = {
    'default_provider': os.getenv('AI_DEFAULT_PROVIDER', 'mock'),
    'fallback_to_mock': os.getenv('AI_FALLBACK_TO_MOCK', 'True').lower() == 'true',
    'openai': {
        'api_key': os.getenv('OPENAI_API_KEY'),
        'model': 'gpt-4',
        'max_tokens': int(os.getenv('AI_MAX_TOKENS', 2000)),
        'temperature': float(os.getenv('AI_TEMPERATURE', 0.7)),
    },
    'anthropic': {
        'api_key': os.getenv('ANTHROPIC_API_KEY'),
        'model': 'claude-3-sonnet-20240229',
        'max_tokens': int(os.getenv('AI_MAX_TOKENS', 2000)),
        'temperature': float(os.getenv('AI_TEMPERATURE', 0.7)),
    },
    'features': {
        'code_analysis': os.getenv('AI_CODE_ANALYSIS_ENABLED', 'True').lower() == 'true',
        'recommendations': os.getenv('AI_RECOMMENDATIONS_ENABLED', 'True').lower() == 'true',
        'tutoring': os.getenv('AI_TUTORING_ENABLED', 'True').lower() == 'true',
    },
    'rate_limiting': {
        'enabled': os.getenv('AI_RATE_LIMIT_ENABLED', 'True').lower() == 'true',
        'requests_per_minute': 60,
        'requests_per_hour': 1000,
    },
    'caching': {
        'enabled': os.getenv('AI_CACHE_RESPONSES', 'True').lower() == 'true',
        'ttl': 3600,  # 1 hour
    }
}


# wokkahlearn/settings.py - Add code execution settings

# Docker Configuration
DOCKER_NETWORK = 'wokkahlearn_execution'
CODE_EXECUTION_TIMEOUT = 30  # seconds
MAX_MEMORY_USAGE = 128  # MB
MAX_CONCURRENT_EXECUTIONS = 10

# Code Execution Settings
CODE_EXECUTION = {
    'enabled': True,
    'docker_network': DOCKER_NETWORK,
    'default_timeout': CODE_EXECUTION_TIMEOUT,
    'max_memory_mb': MAX_MEMORY_USAGE,
    'max_concurrent_executions': MAX_CONCURRENT_EXECUTIONS,
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

import crontab
from celery import CELERY_BEAT_SCHEDULE
# Celery Configuration for Background Processing
CELERY_BEAT_SCHEDULE.update({
    'cleanup-old-executions': {
        'task': 'code_execution.tasks.cleanup_old_executions',
        'schedule': crontab(minute=0, hour=2),  # 2 AM daily
    },
    'collect-execution-statistics': {
        'task': 'code_execution.tasks.collect_daily_statistics',
        'schedule': crontab(minute=30, hour=23),  # 11:30 PM daily
    },
})