# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import os

from django.urls import reverse_lazy

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

SECRET_KEY = '*****************************'

DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1', 'localhost', 'testserver']

ADMINS = (
    ('Admin', 'org@example.com'),
)

SITE_ID = 1

ROOT_URLCONF = 'config.urls'

WSGI_APPLICATION = 'config.wsgi.application'


INSTALLED_APPS = [
    'modeltranslation',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.humanize',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'crispy_forms',
    'tastypie',
    'tinymce',
    'django_wysiwyg',
    'haystack',
    'sorl.thumbnail',
    'orb',
    # 'orb.courses',
    'orb.peers',
    'orb.review',
    'orb.analytics',
    'modeltranslation_exim',
    'django_extensions',
    'ckeditor',
    'webpack_loader',
]


MIDDLEWARE = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'orb.middleware.SearchFormMiddleware',
]


#####################################################################
# Templates

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.request',
                'django.contrib.messages.context_processors.messages',
                'orb.context_processors.get_menu',
                'orb.context_processors.get_version',
                'orb.context_processors.base_context_processor',
            ],
            'debug': DEBUG,
        },
    },
]

#####################################################################


#####################################################################
# Database configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'orb.sqlite3',
    }
}
#####################################################################


#####################################################################
# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True
LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'orb/locale'),
]
gettext = lambda s: s  # noqa
LANGUAGES = [
    ('en','English'),
]
MODELTRANSLATION_DEFAULT_LANGUAGE = 'en'
#####################################################################


#####################################################################
# Static assets & media uploads
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, '..', 'static')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, '..', 'media')

# DJANGO WEBPACK BUNDLING
WEBPACK_LOADER = {
    "COVID_LIBRARY": {
        "CACHE": not DEBUG,
        # "CACHE": False,
        "BUNDLE_DIR_NAME": 'covid/',  # must end with slash
        "STATS_FILE": os.path.join(BASE_DIR, "orb/webpack-stats.json"),
    },
}
#####################################################################


#####################################################################
# Email
SERVER_EMAIL = 'COVID-19 Library <orb@example.com>'
EMAIL_SUBJECT_PREFIX = '[COVID-19 Library]: '
EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
EMAIL_FILE_PATH = '/tmp/'
#####################################################################


#####################################################################
# Search settings
HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.solr_backend.SolrEngine',
        'URL': 'http://127.0.0.1:8983/solr'
    },
}
HAYSTACK_SIGNAL_PROCESSOR = 'haystack.signals.RealtimeSignalProcessor'

ADVANCED_SEARCH_CATEGORIES = [
    ('health_topic', 'health-domain'),
    ('resource_type', 'type'),
    ('audience', 'audience'),
    ('geography', 'geography'),
    ('language', 'language'),
    ('device', 'device'),
]
#####################################################################


#####################################################################
# Authentication
LOGIN_URL = reverse_lazy('profile_login')
AUTHENTICATION_BACKENDS =  [
    'orb.auth.UserModelEmailBackend',
    'django.contrib.auth.backends.ModelBackend',
]
#####################################################################


#####################################################################
# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'root': {
        'level': 'WARNING',
        'handlers': ['console'],
    },
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s '
                      '%(process)d %(thread)d %(message)s',
        },
        'simple': {
            'format': '%(levelname)s %(asctime)s %(module)s %(message)s',
        }
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        }
    },
    'loggers': {
        'django.db.backends': {
            'level': 'ERROR',
            'handlers': ['console'],
            'propagate': False,
        },
        'orb': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': False,
        },
    },
}
#####################################################################


#####################################################################
# COVID-19 Library specific settings
ORB_RESOURCE_DESCRIPTION_MAX_WORDS = 150
ORB_GOOGLE_ANALYTICS_CODE = ''
ORB_INFO_EMAIL = 'orb@example.com'
ORB_PAGINATOR_DEFAULT = 20
ORB_RESOURCE_MIN_RATINGS = 3
TASK_UPLOAD_FILE_TYPE_BLACKLIST = ['application/vnd.android']
TASK_UPLOAD_FILE_MAX_SIZE = 20971520
STAGING = False  # used for version context processor
IP_STACK_API_KEY = '' # set this in your local_settings.py
#####################################################################


DJANGO_WYSIWYG_FLAVOR = "tinymce_advanced"
CRISPY_TEMPLATE_PACK = 'bootstrap3'

TINYMCE_DEFAULT_CONFIG = {
    'theme': "advanced", # default value
    'relative_urls': False, # default value
    'width': '100%',
    'height': 300,
    'position': 'top',
}

# Simple settings flags for download features
DOWNLOAD_LOGIN_REQUIRED = False
DOWNLOAD_EXTRA_INFO = False


try:
    from .local_settings import *  # noqa
except ImportError:
    import warnings
    warnings.warn("Using default settings. Add `config.local_settings.py` for custom settings.")
