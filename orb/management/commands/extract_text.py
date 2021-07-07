
from __future__ import unicode_literals

import os

import textract
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from orb.models import ResourceFile


class Command(BaseCommand):

    def handle(self, *args, **options):

        files = ResourceFile.objects.filter(file_full_text=None)
        for f in files:
            print(os.path.join(settings.MEDIA_ROOT, f.file.name))
            try:
                text = textract.process(os.path.join(
                    settings.MEDIA_ROOT, f.file.name))
                f.file_full_text = text
                f.save()
                # this just triggers the search indexing
                f.resource.save()
            except textract.exceptions.ExtensionNotSupported:
                # do nothing
                print("File type not supported... yet!")
