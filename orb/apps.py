from __future__ import unicode_literals

from django.apps import AppConfig
from django.db.models.signals import post_save


class ORBConfig(AppConfig):
    name = 'orb'
    verbose_name = "ORB"

    def ready(self):
        from orb import callbacks
        from tastypie.models import create_api_key
        from django.contrib.auth import get_user_model
        Resource = self.get_model('Resource')
        post_save.connect(callbacks.resource_submitted_callback, sender=Resource)
        post_save.connect(create_api_key, sender=get_user_model())
