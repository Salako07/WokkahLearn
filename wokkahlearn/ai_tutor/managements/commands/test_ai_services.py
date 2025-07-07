#!/usr/bin/env python
"""
WokkahLearn Diagnostic Script
Run this to diagnose common issues with your setup
"""

import os
import sys
import subprocess
import importlib.util

def check_mark(condition):
    return "✅" if condition else "❌"

def run_diagnostics():
    print("🔍 WokkahLearn Diagnostic Tool")
    print("=" * 40)
    
    # Check Python version
    python_version = sys.version_info
    print(f"\n🐍 Python Version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    print(f"   Minimum required: 3.8+ {check_mark(python_version >= (3, 8))}")
    
    # Check if Django is installed and can be imported
    print(f"\n📦 Package Checks:")
    
    packages = {
        'django': 'Django',
        'rest_framework': 'Django REST Framework',
        'channels': 'Django Channels',
        'openai': 'OpenAI Library',
        'anthropic': 'Anthropic Library',
        'redis': 'Redis Python Client',
        'psycopg2': 'PostgreSQL Adapter',
        'celery': 'Celery Task Queue'
    }
    
    for package, name in packages.items():
        try:
            spec = importlib.util.find_spec(package)
            if spec is not None:
                print(f"   {name}: ✅ Installed")
            else:
                print(f"   {name}: ❌ Not found")
        except ImportError:
            print(f"   {name}: ❌ Import error")
    
    # Check environment file
    print(f"\n🔧 Environment Configuration:")
    env_file_exists = os.path.exists('.env')
    print(f"   .env file exists: {check_mark(env_file_exists)}")
    
    if env_file_exists:
        with open('.env', 'r') as f:
            env_content = f.read()
            
        env_vars = {
            'SECRET_KEY': 'Django Secret Key',
            'DEBUG': 'Debug Mode',
            'ANTHROPIC_API_KEY': 'Anthropic API Key',
            'OPENAI_API_KEY': 'OpenAI API Key',
            'REDIS_URL': 'Redis URL'
        }
        
        for var, description in env_vars.items():
            has_var = var in env_content and not env_content.split(f'{var}=')[1].split('\n')[0].strip() in ['', 'your-key-here', 'your-openai-api-key-here', 'your-anthropic-api-key-here']
            print(f"   {description}: {check_mark(has_var)}")
    
    # Check Django setup
    print(f"\n⚙️ Django Configuration:")
    
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wokkahlearn.settings')
        import django
        django.setup()
        print(f"   Django setup: ✅ Success")
        
        # Check if we can import settings
        from django.conf import settings
        print(f"   Settings import: ✅ Success")
        
        # Check database connection
        try:
            from django.db import connection
            connection.ensure_connection()
            print(f"   Database connection: ✅ Success")
        except Exception as e:
            print(f"   Database connection: ❌ {str(e)}")
        
        # Check AI service configuration
        try:
            ai_settings = getattr(settings, 'AI_SERVICE_SETTINGS', None)
            if ai_settings:
                print(f"   AI Service Settings: ✅ Configured")
                print(f"     Default Provider: {ai_settings.get('default_provider', 'Not set')}")
            else:
                print(f"   AI Service Settings: ❌ Not configured")
        except Exception as e:
            print(f"   AI Service Settings: ❌ {str(e)}")
            
    except Exception as e:
        print(f"   Django setup: ❌ {str(e)}")
        return
    
    # Check AI services
    print(f"\n🤖 AI Services:")
    try:
        from ai_tutor.services import ai_tutor_service
        status = ai_tutor_service.get_service_status()
        
        print(f"   OpenAI Available: {check_mark(status.get('openai', False))}")
        print(f"   Anthropic Available: {check_mark(status.get('anthropic', False))}")
        print(f"   Mock Service Available: {check_mark(status.get('mock', False))}")
        print(f"   Default Service: {status.get('default', 'Not set')}")
        
    except Exception as e:
        print(f"   AI Service Import: ❌ {str(e)}")
    
    # Check file structure
    print(f"\n📁 File Structure:")
    
    required_files = {
        'manage.py': 'Django Management Script',
        'wokkahlearn/settings.py': 'Settings File',
        'wokkahlearn/urls.py': 'URL Configuration',
        'ai_tutor/models.py': 'AI Tutor Models',
        'ai_tutor/views.py': 'AI Tutor Views',
        'ai_tutor/services.py': 'AI Tutor Services',
    }
    
    for file_path, description in required_files.items():
        exists = os.path.exists(file_path)
        print(f"   {description}: {check_mark(exists)}")
    
    # Check directories
    required_dirs = ['logs', 'static', 'media', 'ai_tutor/management/commands']
    for dir_path in required_dirs:
        exists = os.path.exists(dir_path)
        print(f"   {dir_path}/ directory: {check_mark(exists)}")
    
    # Django management commands check
    print(f"\n🛠️ Management Commands:")
    try:
        result = subprocess.run([sys.executable, 'manage.py', 'help'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"   Django commands accessible: ✅ Success")
            
            # Check for custom commands
            if 'test_ai_services' in result.stdout:
                print(f"   Custom AI test command: ✅ Available")
            else:
                print(f"   Custom AI test command: ❌ Not found")
        else:
            print(f"   Django commands: ❌ Error")
            
    except Exception as e:
        print(f"   Django commands: ❌ {str(e)}")
    
    # Quick fixes suggestions
    print(f"\n🔧 Quick Fixes:")
    
    if not env_file_exists:
        print("   • Create .env file with required environment variables")
    
    if python_version < (3, 8):
        print("   • Upgrade Python to version 3.8 or higher")
    
    try:
        import openai
    except ImportError:
        print("   • Install OpenAI: pip install openai==1.3.0")
    
    try:
        import anthropic
    except ImportError:
        print("   • Install Anthropic: pip install anthropic==0.7.8")
    
    if not os.path.exists('logs'):
        print("   • Create logs directory: mkdir logs")
    
    print(f"\n🎯 Summary:")
    print("   Run this diagnostic anytime you encounter issues.")
    print("   Most problems can be fixed by:")
    print("   1. Setting up proper environment variables")
    print("   2. Installing missing dependencies")
    print("   3. Running database migrations")
    print("   4. Creating required directories")
    
if __name__ == "__main__":
    run_diagnostics()