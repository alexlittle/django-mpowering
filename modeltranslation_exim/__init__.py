# -*- coding: utf-8 -*-

"""
django-modeltranslation-exim modeltranslation_exim is a package
for importing and exporting translations to and from the database.

It is designed to work in conjunction with django-modeltranslation,
but designed such that the content can be exported prior to
installing django-modeltranslation.

PO FILE FORMATTING
==================

Standard PO file formatting uses the file path and the line number
to provide a reference for where the string can be found. This occurrence
information is a helpful reference but the `msgid` is used by gettext
to look up the translated `msgstr` value. In the case of database
-stored content, this isn't feasible (at least the way we get this
content with Django and available tools).

The alternatives are to treat the PO file like a typical PO file
and run updates for matching strings, or store the specific location
of text in the database and use that to make isolated updates. This
package uses the latter strategy, and uses the occurrences data to
store the database location of each occurrence.

It does this by replacing the file path with a dotted path to the
Django model class and field, and replacing the line number with the
primary key. Instead of something like:

    #: myapp/forms.py:22
    msgid: "This form is not valid"
    msgstr: ""

To reference line 22 in `myapp/forms.py`, this would look like:

    # myapp.models.Tag.title: 78
    # otherapp.models.Model.title: 123
    msgid: "Hello world"
    msgstr: ""

In the preceding example there are two instances where the string is
found. **The ramification of this choice is that the occurrence
information is extremely important and must not be discarded or
tampered with.**

The advantage of the alternative method is that it is slightly more
robust and, in the event string are repeated *in the same field
frequently* it may be more efficient. However it requires making
updates for each string value and field combination, whereas this
strategy requires only one update per row, regardless of how many
fields are translated per model.

USAGE
=====

The package ships with two management commands, one to export database
content to a PO file and another to update database fields from a
modeltranslation_exim formatted PO file.

Export
------

Model fields are specified using a dotted path:

    ./manage.py export_db_translations orb.Category.title orb.Tag.name orb.Tag.summary

This will write a PO file to stdout for the `title` field on the `Category`
model and the `name` and `summary` fields on the `Tag` model.

Dotted paths can be specified using the standard short form Django format as
used in the example, i.e. `app_name.Model_name.field` or the full
Python module path, i.e. `module.Class.field`.

Import
------

Translations are imported from a PO file by specifying the path and the language

    ./manage.py import_db_translations /home/user/django.po --language=es

The import strategy is to update translations on a row-by-row basis.


TODO
====

Future enhancements, planned or under consideration.

- The export to PO file should allow specifying a language code and then
  including any existing translations from the database as msgstr values.

    ./manage.py export_db_translations orb.Category.title orb.Tag.name orb.Tag.summary --language=es

- Allow export field selection by previously registered model fields,
  without requiring field name specification in the command line.

    ./manage.py export_db_translations --language=es --registered

- Add 'safe' importing, which would not override existing translations.

- Add 'forced' importing which would use the `update` queryset method, halving
  the number of queries and also bypassing each model's `save` method.

"""

from __future__ import unicode_literals

from modeltranslation_exim.exim import DatabaseTranslations, POTranslations

__title__ = 'modeltranslation_exim'
__version__ = '0.1.0'
__author__ = 'Ben Lopatin'
