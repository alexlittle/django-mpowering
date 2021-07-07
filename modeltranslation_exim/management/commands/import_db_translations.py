# -*- coding: utf-8 -*-

"""
Management command that generates a PO file for a specified language
based on django-modeltranslation fields.

This generates a quasi-complete PO file, in that it cannot be turned
into a usable compiled MO file.

Use polib to

We want a graph of

This example::

    #: myapp.MyModel.name:300 myapp.OtherModel.title:12
    msgid "Advanced search"
    msgstr "Búsqueda avanzada"

Would find occcurences of the string "Advanced search" in the `name` field
of the MyModel model (in the `myapp` app), in the instance with primary key
value of 12, and also in the `title` field of the `OtherModel` model for
primary key 12.

"""

from __future__ import unicode_literals

from optparse import make_option

from django.core.management.base import BaseCommand, CommandError

from modeltranslation_exim import POTranslations


class Command(BaseCommand):
    """
    Imports translations from a PO file into database translation fields
    """
    help = "Update database translations from specially formatted PO file"
    args = "<PO file path>"

    def add_arguments(self, parser):
        parser.add_argument(
            'filepath',
        )
        parser.add_argument(
            '--language',
            dest='language',
            required=True,
            help='Language code for target language, e.g. `pt-br` (required)',
        )

    def handle(self, *args, **options):
        filepath= options.get('filepath')
        language = options.get('language')
        translator = POTranslations(filepath, language, output=self.stdout)
        translator.save()
