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

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from modeltranslation_exim import DatabaseTranslations


class Command(BaseCommand):
    """
    Exports translatable database fields to a PO file format

    By default it should only return PO files for languages that
    are in the site LANGUAGES. To force an additional language
    should require an optional flag.

    This should also only optionally depend on modeltranslation
    for export, as it may be the case that you want to export
    database content before modeltranslation has been added.
    To that end, importing the translator should be used if and
    only if the model/field names have not been specified in the
    command arguments.
    """
    help = ("Create a specially formatted PO file from database fields using stdout. "
            "This may be used to return blank msgstrs or existing translations.")

    args = "<module.Class.field> <module.Class.field> ... "

    def add_arguments(self, parser):
        parser.add_argument(
            'fields',
            nargs='*',
            help=('Optional dotted paths to model field names'),
        )
        parser.add_argument(
            '--language',
            dest='language',
            help=('Language code for target language, e.g. `pt-br` (optional). '
                  'This will return existing translations, without specification it will return '
                  'an blank msgstr values.'),
        )

    def handle(self, *args, **options):
        language = options.get('language', None)
        fields = options.get('fields', [])
        if language and language not in [i[0] for i in settings.LANGUAGES]:
            raise CommandError(
                "'{}' is not one of the available language choices for this installation.".format(language))

        exported = DatabaseTranslations.from_paths(language, *fields)
        exported.save()
