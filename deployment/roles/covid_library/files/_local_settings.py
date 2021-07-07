# -*- coding: utf-8 -*-

"""
Local settings for django-covid

This is an example of config/local_settings.py

"""

# SECURITY WARNING: keep the secret key used in production secret!
# TODO: CHANGE ME!
SECRET_KEY = '1h*u)(+!m_4dj=eea5i!6od+ic9o+u3tg_1y26myy)t+qt5ta='

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False


# TODO: CHANGE ME!
ALLOWED_HOSTS = ['*']


# TODO: CHANGE ME!
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'name',
        'USER': 'user',
        'PASSWORD': 'password',
        'HOST': '',
        'PORT': '',
    }
}



LANGUAGE_CODE = 'en-us'
gettext = lambda s: s
LANGUAGES = [
    ('en', u'English'),
]

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

SITE_ID = 1

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
# TODO change me IF on a custom deployment
MEDIA_ROOT = '/home/www/platform/media/'

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = '/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
# TODO change me IF on a custom deployment
STATIC_ROOT = '/home/www/platform/static/'

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = '/static/'

# TODO: CHANGE ME!
SERVER_EMAIL = 'Covid Library <info@yourdomain.com>'
# TODO: CHANGE ME!
EMAIL_SUBJECT_PREFIX = '[COVIDLIBRARY]: '
# TODO: CHANGE ME!
ADMINS = (
    ('Your Name', 'you@yourdomain.com'),
)

