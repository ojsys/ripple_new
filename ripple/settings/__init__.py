"""
Settings package for Ripple project.

This file determines which settings module to load based on the
DJANGO_ENV environment variable.

Usage:
    - Development: DJANGO_ENV=development (or unset - default)
    - Staging: DJANGO_ENV=staging
    - Production: DJANGO_ENV=production

Alternatively, you can specify the full settings module:
    DJANGO_SETTINGS_MODULE=ripple.settings.development
"""
import os
from decouple import config

# Get environment from env variable, default to 'development'
ENVIRONMENT = config('DJANGO_ENV', default='development')

if ENVIRONMENT == 'production':
    from .production import *
elif ENVIRONMENT == 'staging':
    from .staging import *
else:
    from .development import *
