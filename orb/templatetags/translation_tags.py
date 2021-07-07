from __future__ import unicode_literals

from django import template
from django.conf import settings
from modeltranslation.utils import build_localized_fieldname

register = template.Library()


@register.simple_tag
def translated_fields(obj, field_name):
    """
    Gets all of the translated values for a given field on an object

    Args:
        obj: a model instance
        field_name: name of the translated model field

    Returns:
        a list of non-blank field values

    """
    field_names = [build_localized_fieldname(field_name, language[0]) for language in settings.LANGUAGES]
    return [getattr(obj, trans_field) for trans_field in field_names if getattr(obj, trans_field, None)]
