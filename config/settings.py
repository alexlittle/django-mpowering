# -*- coding: utf-8 -*-

"""
Django settings for mpowering project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

import os

from django.core.urlresolvers import reverse_lazy

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

SECRET_KEY = '*****************************'

DEBUG = True
TEMPLATE_DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1', 'localhost']

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
    'orb',
    'tastypie',
    'tinymce',
    'django_wysiwyg',
    'haystack',
    'sorl.thumbnail',
    'orb.analytics',
    'orb.partners.OnemCHW',
]


MIDDLEWARE_CLASSES = [
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
TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.core.context_processors.request",
    "django.contrib.messages.context_processors.messages",
    'orb.context_processors.get_menu',
    'orb.context_processors.get_version',
    'orb.context_processors.base_context_processor',
)
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
    ('en', u'English'),
    ('es', u'Español'),
    ('pt-br', u'Português'),
]
MODELTRANSLATION_DEFAULT_LANGUAGE = 'en'
#####################################################################


#####################################################################
# Static assets & media uploads
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'orb/static')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
#####################################################################


#####################################################################
# Email
SERVER_EMAIL = 'ORB <orb@example.com>'
EMAIL_SUBJECT_PREFIX = '[ORB]: '
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
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
# ORB specific settings
ORB_RESOURCE_DESCRIPTION_MAX_WORDS = 150
ORB_GOOGLE_ANALYTICS_CODE = ''
ORB_INFO_EMAIL = 'orb@example.com'
ORB_RESOURCE_DESCRIPTION_MAX_WORDS = 150
ORB_PAGINATOR_DEFAULT = 20
ORB_RESOURCE_MIN_RATINGS = 3
ORB_PARTNER_DATA_ENABLED = False
TASK_UPLOAD_FILE_TYPE_BLACKLIST = [u'application/vnd.android']
TASK_UPLOAD_FILE_MAX_SIZE = "5242880"
STAGING = False  # used for version context processor
#####################################################################


DJANGO_WYSIWYG_FLAVOR = "tinymce_advanced"
CRISPY_TEMPLATE_PACK = 'bootstrap3'


try:
    from local_settings import *  # noqa
except ImportError:
    import warnings
    warnings.warn("Using default settings. Add `config.local_settings.py` for custom settings.")
