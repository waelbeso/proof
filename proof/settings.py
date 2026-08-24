import os
from pathlib import Path

import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'dev-only-secret-key')
DEBUG = os.getenv('DJANGO_DEBUG', '1') == '1'

ALLOWED_HOSTS = [
    x.strip()
    for x in os.getenv('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
    if x.strip()
]
render_hostname = os.getenv('RENDER_EXTERNAL_HOSTNAME')
if render_hostname and render_hostname not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(render_hostname)

INSTALLED_APPS = [
    'django.contrib.admin','django.contrib.auth','django.contrib.contenttypes',
    'django.contrib.sessions','django.contrib.messages','django.contrib.staticfiles',
    'rest_framework','rest_framework.authtoken','core','api',
]
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware','django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware','django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
ROOT_URLCONF = 'proof.urls'
TEMPLATES = [{'BACKEND':'django.template.backends.django.DjangoTemplates','DIRS':[],'APP_DIRS':True,
              'OPTIONS':{'context_processors':['django.template.context_processors.request','django.contrib.auth.context_processors.auth','django.contrib.messages.context_processors.messages','core.context_processors.ui_context']}}]
WSGI_APPLICATION = 'proof.wsgi.application'

if os.getenv('DATABASE_URL'):
    DATABASES = {
        'default': dj_database_url.config(
            default=os.environ['DATABASE_URL'],
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
elif os.getenv('POSTGRES_HOST'):
    DATABASES = {'default': {'ENGINE':'django.db.backends.postgresql','NAME':os.getenv('POSTGRES_DB','proof'),
                 'USER':os.getenv('POSTGRES_USER','proof'),'PASSWORD':os.getenv('POSTGRES_PASSWORD','proof'),
                 'HOST':os.getenv('POSTGRES_HOST','db'),'PORT':os.getenv('POSTGRES_PORT','5432')}}
else:
    DATABASES = {'default': {'ENGINE':'django.db.backends.sqlite3','NAME':BASE_DIR/'db.sqlite3'}}

AUTH_PASSWORD_VALIDATORS = []
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'},
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': ['rest_framework.authentication.TokenAuthentication','rest_framework.authentication.SessionAuthentication'],
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.IsAuthenticatedOrReadOnly'],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}
CELERY_BROKER_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = CELERY_BROKER_URL

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'
