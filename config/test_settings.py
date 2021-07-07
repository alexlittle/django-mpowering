# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os

import dj_database_url  # NOTE: This is not in the project requirements!

from .settings import *

#DATABASES = {
#    "default": dj_database_url.config(default="mysql://root:root@127.0.0.1:3306/orb")
#}
#DATABASES["default"]["TEST"] = {"NAME": os.environ.get("TEST_DB_NAME", "test_orb")}

DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": "orb",}}

HAYSTACK_SIGNAL_PROCESSOR = "haystack.signals.BaseSignalProcessor"

# GDAL_LIBRARY_PATH = os.environ.get('GDAL_LIBRARY_PATH', '/usr/local/lib/libgdal.dylib')
# ctypes.CDLL(GDAL_LIBRARY_PATH)
LANGUAGES = [
    ('en','English'),
    # ('es','Español'),
    # ('pt-br','Português'),
]
