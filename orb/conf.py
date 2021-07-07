"""
App-specific settings go here.

This ensures that defaults can be provided for settings that may
not be explicitly available.
"""
from __future__ import unicode_literals

from django.conf import settings

try:
    DOWNLOAD_LOGIN_REQUIRED = settings.DOWNLOAD_LOGIN_REQUIRED
except AttributeError:
    DOWNLOAD_LOGIN_REQUIRED = False

try:
    DOWNLOAD_EXTRA_INFO = settings.DOWNLOAD_EXTRA_INFO
except AttributeError:
    DOWNLOAD_EXTRA_INFO = False


EMBEDDABLE_FILE_TYPES = getattr(
    settings,
    'EMBEDDABLE_FILE_TYPES ',
    ['pdf', 'mp4', 'pptx', 'jpg', 'png', 'ppt', 'docx', 'mov', 'm4v'],
)
