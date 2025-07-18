"""
Django settings for core project.

Generated by 'django-admin startproject' using Django 5.1.7.
"""

import os
from pathlib import Path
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


MEDIA_ROOT = os.environ.get("MEDIA_ROOT", BASE_DIR / "media")
MEDIA_URL  = "/media/"

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-*p-gc2k_^-f$j!z%rsn91h-)zsjl6c_h%j%-9(mhy95tm&iug='

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True  # Set to False for production
CSRF_TRUSTED_ORIGINS = ['https://rahulhost-1.tail64cc94.ts.net', 'https://rahulhost-1.tail64cc94.ts.net']# CSRF Settings
CSRF_TRUSTED_ORIGINS = ['https://rahulhost-1.tail64cc94.ts.net', 'https://rahulhost-1.tail64cc94.ts.net']
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_DOMAIN = '.genericinvoice.duckdns.org'
CSRF_USE_SESSIONS = True
ALLOWED_HOSTS = ['*', 'djangotemp-8sn5.onrender.com','genericinvoice.duckdns.org', 'localhost', '127.0.0.1', 'https://rahulhost-1.tail64cc94.ts.net']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party apps
    'whitenoise.runserver_nostatic',  # Whitenoise for serving static files

    # Your apps here
    'vendor',
    'product',
    'billing',
    'company',
    'authentication',
    'vehicle',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Serve static files efficiently
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
         'DIRS': [os.path.join(BASE_DIR, 'templates')],
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

WSGI_APPLICATION = 'core.wsgi.application'

# Database configuration (PostgreSQL on Render)
DATABASE_URL = "postgresql://postgres.vsqvjsipzgkkmukqnkhm:R@hul@88578@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres"

DATABASES = {
    'default': dj_database_url.parse(DATABASE_URL, conn_max_age=600, ssl_require=True)
}
# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'  # Collect static files here

# MEDIA_URL = '/media/'
# MEDIA_ROOT = BASE_DIR / 'media'  # For user-uploaded files

STATICFILES_DIRS = [
    BASE_DIR / 'static',  # If you have a static folder inside your project
]

# Ensure Whitenoise serves static files
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'login'

# CSRF Settings
CSRF_TRUSTED_ORIGINS = ['https://rahulhost-1.tail64cc94.ts.net']
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_DOMAIN = '.tail64cc94.ts.net'
CSRF_USE_SESSIONS = True
