from .settings import *

# Override settings for staging
DEBUG = False

ALLOWED_HOSTS = ['staging.startupripple.com']  

# Database settings (you might want to use a different database for staging)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': config('STAGING_DB_NAME', default='startupr_stagingdb'),
        'USER': config('STAGING_DB_USER', default='startupr_stagingdb_user'),
        'PASSWORD': config('STAGING_DB_PASSWORD'),
        'HOST': 'localhost',
        'PORT': '3306',
    }
}

# Email settings - you might want to use a different email for staging
DEFAULT_FROM_EMAIL = 'staging@startupripple.com'

# Set a different site URL for staging
SITE_URL = 'https://staging.startupripple.com'

# You can add any other staging-specific settings here