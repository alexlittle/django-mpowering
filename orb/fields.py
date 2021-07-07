# coding: utf-8

"""
Model field definitions for Django ORB
"""

from __future__ import unicode_literals

from autoslugged import AutoSlugField as BaseSlugField
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile

from orb.compat import HTTPError, URLError, urlopen


class AutoSlugField(BaseSlugField):
    """
    Redefined AutoSlugField with defaults selected

    - unique: True
    """
    def __init__(self, *args, **kwargs):
        if "unique" not in kwargs and "unique_with" not in kwargs:
            kwargs["unique"] = True
        super(AutoSlugField, self).__init__(*args, **kwargs)


def image_cleaner(instance, field_name="image", url=None):
    """

    Args:
        instance: a model instance
        field_name: the name of the image field

    Returns:
        the same instance

    """
    img_temp = NamedTemporaryFile()
    image_field = getattr(instance, field_name)

    url = url if url else image_field.name

    try:
        img_temp.write(urlopen(url).read())
    except (HTTPError, URLError):
        # TODO(bennylope) log this
        return instance

    img_temp.flush()

    img_filename = image_field.name.split("/")[-1]
    image_field.save(img_filename, File(img_temp))

    return instance
