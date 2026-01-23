"""
Base settings for Ripple project.
Common settings shared across all environments.
"""
from decouple import config
from pathlib import Path
import os
import warnings
import sys

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY')

# Stripe Configuration
STRIPE_PUBLIC_KEY = config('STRIPE_PUBLIC_KEY', default='')
STRIPE_SECRET_KEY = config('STRIPE_SECRET_KEY', default='')

# Custom User Model
# After restructuring: AUTH_USER_MODEL = 'accounts.CustomUser'
AUTH_USER_MODEL = 'accounts.CustomUser'

# Silence specific system checks
SILENCED_SYSTEM_CHECKS = [
    'ckeditor.W001',  # CKEditor security warning
    'mysql.W002',     # MariaDB Strict Mode warning
]

# Application definition
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
]

THIRD_PARTY_APPS = [
    'jazzmin',
    'django_paystack',
    'crispy_forms',
    'crispy_bootstrap5',
    'django_json_widget',
    'ckeditor',
]

# LOCAL_APPS after restructuring (uncomment when migration complete):
# LOCAL_APPS = [
#     'apps.core',
#     'apps.accounts',
#     'apps.cms',
#     'apps.projects',
#     'apps.funding',
#     'apps.payments',
#     'apps.srt',
#     'apps.incubator',
# ]

# Transitional: Use old 'projects' app until restructuring is complete
LOCAL_APPS = [
    'apps.core',
    'apps.accounts',
    'apps.cms',
    'apps.projects',
    'apps.funding',
    'apps.payments',
    'apps.srt',
    'apps.incubator',
]

INSTALLED_APPS = ['jazzmin'] + DJANGO_APPS + THIRD_PARTY_APPS[1:] + LOCAL_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.core.middleware.ProfileCompletionMiddleware',
]

ROOT_URLCONF = 'ripple.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.cms.context_processors.site_settings',
                'apps.cms.context_processors.social_links',
            ],
        },
    },
]

WSGI_APPLICATION = 'ripple.wsgi.application'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Authentication Settings
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'home'

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

# Media files (user-uploaded content)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Crispy Forms (for Bootstrap 5 forms)
CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
CRISPY_TEMPLATE_PACK = 'bootstrap5'

# Internationalization
LANGUAGE_CODE = 'en'
LANGUAGES = [
    ('en', 'English'),
    ('fr', 'Français'),
]
USE_I18N = True
LOCALE_PATHS = [BASE_DIR / 'locale']

TIME_ZONE = 'UTC'
USE_TZ = True

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Admin Email Configuration
ADMIN_EMAIL = config('ADMIN_EMAIL', default='admin@startupripple.com')
ADMIN_EMAILS = [ADMIN_EMAIL]  # List of admin emails for notifications

# Paystack Configuration
PAYSTACK_PUBLIC_KEY = config('PAYSTACK_PUBLIC_KEY', default='')
PAYSTACK_SECRET_KEY = config('PAYSTACK_SECRET_KEY', default='')
PAYSTACK_CALLBACK_URL = 'payment_callback'

PAYSTACK_SETTINGS = {
    'BUTTON_ID': 'pay-button',
    'SUCCESS_URL': 'payment_success',
    'FAILURE_URL': 'payment_failed',
    'CURRENCY': 'NGN',
    'BUTTON_CLASS': 'btn btn-class',
    'BUTTON_TEXT': 'Pay Now',
}

# CKEditor configuration
CKEDITOR_UPLOAD_PATH = 'uploads/'
CKEDITOR_CONFIGS = {
    'default': {
        'toolbar': 'Custom',
        'toolbar_Custom': [
            ['Bold', 'Italic', 'Underline'],
            ['NumberedList', 'BulletedList', '-', 'Outdent', 'Indent'],
            ['Link', 'Unlink'],
            ['Image', 'Table'],
            ['RemoveFormat', 'Source']
        ],
        'height': 300,
        'width': '100%',
        'removePlugins': 'elementspath',
        'forcePasteAsPlainText': True,
        'disableNativeSpellChecker': False,
        'removeDialogTabs': 'image:advanced;link:advanced',
    },
}

# Suppress CKEditor deprecation warning
if not sys.warnoptions:
    warnings.filterwarnings('ignore', message='.*CKEditor.*')
    warnings.filterwarnings('ignore', module='ckeditor.*')

# Jazzmin Admin Settings
JAZZMIN_SETTINGS = {
    "site_title": "StartUpRipple Admin",
    "site_header": "StartUpRipple",
    "site_brand": "StartUpRipple",
    "site_logo_classes": "img-circle",
    "login_logo": None,
    "site_icon": None,
    "welcome_sign": "Welcome to StartUpRipple Admin",
    "copyright": "StartUpRipple Ltd",
    "search_model": "accounts.CustomUser",
    "user_avatar": None,
    "topmenu_links": [
        {"name": "Home", "url": "admin:index", "permissions": ["accounts.view_customuser"]},
        {"name": "Support", "url": "https://github.com/farridav/django-jazzmin/issues", "new_window": True},
        {"model": "accounts.CustomUser"},
        {"app": "projects"},
    ],
    "usermenu_links": [
        {"name": "Support", "url": "https://github.com/farridav/django-jazzmin/issues", "new_window": True},
        {"model": "accounts.CustomUser"}
    ],
    "show_sidebar": True,
    "navigation_expanded": True,
    "hide_apps": [],
    "hide_models": [],
    "order_with_respect_to": ["auth", "accounts", "projects", "funding", "srt", "cms"],
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.Group": "fas fa-users",
        "accounts.CustomUser": "fas fa-user",
        "accounts.FounderProfile": "fas fa-user-tie",
        "accounts.InvestorProfile": "fas fa-user-graduate",
        "accounts.PartnerProfile": "fas fa-handshake",
        "projects.Project": "fas fa-project-diagram",
        "projects.Category": "fas fa-tags",
        "projects.FundingType": "fas fa-money-bill",
        "projects.Reward": "fas fa-gift",
        "funding.Investment": "fas fa-hand-holding-usd",
        "funding.Pledge": "fas fa-donate",
        "srt.Venture": "fas fa-rocket",
        "cms.SiteSettings": "fas fa-cog",
    },
    "default_icon_parents": "fas fa-folder",
    "default_icon_children": "fas fa-circle",
    "related_modal_active": True,
    "custom_css": None,
    "custom_js": None,
    "show_ui_builder": True,
    "changeform_format": "horizontal_tabs",
    "changeform_format_overrides": {"accounts.customuser": "collapsible", "auth.group": "vertical_tabs"},
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-success",
    "accent": "accent-teal",
    "navbar": "navbar-dark",
    "no_navbar_border": False,
    "navbar_fixed": False,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": False,
    "sidebar": "sidebar-dark-success",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": False,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,
    "theme": "default",
    "dark_mode_theme": None,
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success"
    }
}
