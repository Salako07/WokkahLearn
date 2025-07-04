# wokkahlearn/settings/test.py
"""
Django settings for WokkahLearn test environment.

This settings file is optimized for running tests with maximum performance
and reliability. It includes configurations for:
- Fast test database
- Disabled unnecessary services
- Mock configurations
- Security settings for testing
- Performance optimizations
"""

from .base import *
import tempfile
import os

# SECURITY WARNING: Use a test-specific secret key
SECRET_KEY = 'django-test-secret-key-not-for-production-use-only-in-tests'

# Debug should be False in tests to catch template errors
DEBUG = False

# Allow all hosts in tests
ALLOWED_HOSTS = ['*', 'testserver', 'localhost', '127.0.0.1']

# Test Database Configuration
# Use in-memory SQLite for speed, or PostgreSQL for production-like testing
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
        'OPTIONS': {
            'timeout': 300,
        },
        'TEST': {
            'NAME': ':memory:',
            'SERIALIZE': False,
        }
    }
}

# Alternative PostgreSQL test database (uncomment if needed)
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': 'wokkahlearn_test',
#         'USER': 'postgres',
#         'PASSWORD': 'postgres',
#         'HOST': 'localhost',
#         'PORT': '5432',
#         'OPTIONS': {
#             'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
#         },
#         'TEST': {
#             'NAME': 'test_wokkahlearn',
#             'SERIALIZE': False,
#             'CREATE_DB': True,
#         }
#     }
# }

# Cache Configuration - Use dummy cache for tests
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    },
    'redis': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Alternative: Use locmem cache for tests that need caching
# CACHES = {
#     'default': {
#         'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
#         'LOCATION': 'test-cache',
#         'TIMEOUT': 300,
#         'OPTIONS': {
#             'MAX_ENTRIES': 1000,
#             'CULL_FREQUENCY': 3,
#         }
#     }
# }

# Email Backend - Use dummy backend for tests
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Static and Media Files
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(tempfile.gettempdir(), 'wokkahlearn_test_static')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(tempfile.gettempdir(), 'wokkahlearn_test_media')

# File Storage - Use temporary directory for tests
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# Disable file compression and whitenoise in tests
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# Password Validation - Simplified for tests
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
]

# Logging Configuration - Reduce verbosity in tests
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'handlers': {
        'console': {
            'level': 'ERROR',
            'class': 'logging.StreamHandler',
        },
        'null': {
            'class': 'logging.NullHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['null'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['null'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['null'],
            'level': 'ERROR',
            'propagate': False,
        },
        'accounts': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'wokkahlearn': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['null'],
        'level': 'ERROR',
    },
}

# Celery Configuration - Use eager execution for tests
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_BROKER_URL = 'memory://'
CELERY_RESULT_BACKEND = 'cache+memory://'

# Redis Configuration - Use fake Redis for tests
REDIS_URL = 'redis://localhost:6379/0'

# Test-specific Django settings
USE_TZ = True
TIME_ZONE = 'UTC'

# Internationalization
LANGUAGE_CODE = 'en-us'
USE_I18N = True
USE_L10N = True

# Security Settings for Tests
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
SECURE_CONTENT_TYPE_NOSNIFF = False
SECURE_BROWSER_XSS_FILTER = False
X_FRAME_OPTIONS = 'DENY'

# Session Configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_SECURE = False
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_AGE = 3600  # 1 hour for tests

# CSRF Configuration
CSRF_COOKIE_SECURE = False
CSRF_TRUSTED_ORIGINS = ['http://localhost', 'http://127.0.0.1', 'http://testserver']

# JWT Configuration for Tests
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
}

# Django REST Framework Configuration for Tests
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
    'TEST_REQUEST_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
}

# Disable migrations for faster tests
class DisableMigrations:
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None

MIGRATION_MODULES = DisableMigrations()

# Test-specific middleware (remove unnecessary middleware)
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Performance optimizations for tests
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Disable debug toolbar in tests
if 'debug_toolbar' in INSTALLED_APPS:
    INSTALLED_APPS.remove('debug_toolbar')

if 'debug_toolbar.middleware.DebugToolbarMiddleware' in MIDDLEWARE:
    MIDDLEWARE.remove('debug_toolbar.middleware.DebugToolbarMiddleware')

# Test-specific apps
INSTALLED_APPS += [
    'django_extensions',  # For testing utilities
]

# Coverage Configuration
COVERAGE_MODULE_EXCLUDES = [
    'tests$', 'settings$', 'urls$', 'locale$',
    'migrations', 'fixtures', 'admin$', 'management',
    'wsgi$', 'asgi$'
]

# Testing Framework Configuration
TESTING = True

# Mock external services
OPENAI_API_KEY = 'test-openai-api-key'
ANTHROPIC_API_KEY = 'test-anthropic-api-key'

# File upload limits for tests
FILE_UPLOAD_MAX_MEMORY_SIZE = 1024 * 1024  # 1MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 1024 * 1024  # 1MB

# AI Service Configuration for Tests
AI_SERVICES = {
    'default': 'mock',
    'mock': {
        'enabled': True,
        'response_delay': 0.1,  # Simulate network delay
    },
    'openai': {
        'enabled': False,  # Disabled in tests
        'api_key': OPENAI_API_KEY,
        'model': 'gpt-3.5-turbo',
    },
    'anthropic': {
        'enabled': False,  # Disabled in tests
        'api_key': ANTHROPIC_API_KEY,
        'model': 'claude-instant-1',
    }
}

# Code Execution Configuration for Tests
CODE_EXECUTION = {
    'enabled': True,
    'docker_enabled': False,  # Use mock execution in tests
    'timeout': 5,  # Short timeout for tests
    'memory_limit': '128m',
    'supported_languages': ['python', 'javascript', 'java'],
}

# Collaboration Configuration for Tests
COLLABORATION = {
    'websocket_enabled': False,  # Use mock WebSocket in tests
    'max_room_participants': 10,
    'session_timeout': 300,  # 5 minutes
}

# Analytics Configuration for Tests
ANALYTICS = {
    'enabled': True,
    'batch_size': 10,  # Smaller batch size for tests
    'flush_interval': 1,  # 1 second for tests
    'storage': 'database',  # Use database for tests
}

# Search Configuration for Tests (if using Elasticsearch)
ELASTICSEARCH_DSL = {
    'default': {
        'hosts': 'localhost:9200',
        'timeout': 30,
    },
}

# Disable search indexing in tests
ELASTICSEARCH_DISABLED = True

# Channels Configuration for Tests
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer'
    }
}

# CORS Configuration for Tests
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://testserver",
]

CORS_ALLOW_ALL_ORIGINS = True  # Only for tests
CORS_ALLOW_CREDENTIALS = True

# API Documentation (disable in tests)
SPECTACULAR_SETTINGS = {
    'TITLE': 'WokkahLearn API (Test)',
    'DESCRIPTION': 'Test API for WokkahLearn platform',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,  # Disable schema serving in tests
}

# Health Check Configuration
HEALTH_CHECK = {
    'enabled': False,  # Disable health checks in tests
}

# Custom Test Settings
TEST_RUNNER = 'django.test.runner.DiscoverRunner'

# Test database settings
TEST_DATABASE_PARALLEL = 1  # Set to number of CPU cores for parallel testing

# Disable unnecessary signals in tests
DISABLE_SIGNALS = [
    'post_save',
    'pre_save',
    'post_delete',
    'pre_delete',
]

# Mock Services Configuration
MOCK_SERVICES = {
    'email': True,
    'sms': True,
    'push_notifications': True,
    'external_apis': True,
    'file_storage': False,  # Use real file storage for upload tests
    'cache': False,  # Use real cache for cache tests
}

# Test Data Configuration
TEST_DATA = {
    'fixtures_dir': os.path.join(BASE_DIR, 'fixtures', 'test'),
    'sample_data_size': 'small',  # small, medium, large
    'cleanup_after_tests': True,
}

# Performance Test Configuration
PERFORMANCE_TESTS = {
    'max_query_count': 10,
    'max_response_time': 2.0,
    'max_memory_usage': 50 * 1024 * 1024,  # 50MB
}

# Security Test Configuration
SECURITY_TESTS = {
    'check_sql_injection': True,
    'check_xss': True,
    'check_csrf': True,
    'check_authentication': True,
    'check_authorization': True,
}

# Import any test-specific overrides
try:
    from .test_local import *
except ImportError:
    pass