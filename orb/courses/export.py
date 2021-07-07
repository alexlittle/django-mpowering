# -*- coding: utf-8 -*-

"""
Base course export functionality

"""

from __future__ import unicode_literals

import hashlib
import time
from typing import Dict  # noqa
from typing import Text  # noqa

import markdown
from autoslugged.settings import slugify
from django.utils.functional import cached_property
from six import text_type


def format_page_as_markdown(activity):
    # type: (Dict) -> Text
    """Create an HTML fo
    rmatted page from a simple course activity"""
    header = "# {}\n\n".format(activity["intro"])
    content = header + activity["content"]
    return markdown.markdown(content)


def sequenced_string(sequence):
    """Returns the elements of sequence as a comma separated string

    >>> sequenced_string([1, 2 ,3])
    "1,2,3"

    """
    return ",".join([str(i) for i in sequence])


class CourseExport(object):
    """
    Builds structure for exporting to an Oppia compatible format

    It starts from a base zip file that contains the common folders
    and files in an Oppia export.

    For each resource (file): write it to resources/file-name.
    The metadata goes in module.xml

    We track order of sections and order of activities in sectiosn

    everythign has a digest.

    """

    default_filename = ""

    def __init__(self, name, id, sections=None, activities=None, version=1, **kwargs):
        """

        Args:
            name: name of the course
            id: given ID in the system
            content: all course content in a list by sections
            **kwargs:
        """
        self.sections = [] if sections is None else sections
        self.activities = [] if activities is None else activities

        for activity in self.activities:
            activity["section"] += 1
            activity["digest"] = hashlib.md5(
                text_type(activity["id"]) + activity["type"]
            ).hexdigest()

        # Make sure sections IDs start at 1
        for section in self.sections:
            section["id"] += 1
            section["activities"] = [
                activity
                for activity in self.activities
                if activity["section"] == section["id"]
            ]

        self.name = name
        self.slug = slugify(name)
        self.courseid = str(id)
        self.version = version
        self.backup_filename = kwargs.pop("backup_filename", self.default_filename)
        self.validate_backup_filename()

    def validate_backup_filename(self):
        raise NotImplementedError("Export class must define validate_backup_filename")

    def _by_resource_type(self, resource_type):
        for course_resource in self.activities:
            if course_resource["type"] == resource_type:
                yield course_resource

    def pages(self):
        return self._by_resource_type("page")

    def resources(self):
        """Returns only resource activities"""
        return self._by_resource_type("resource")

    @cached_property
    def backup_date(self):
        # type: () -> text_type
        """Returns the backup date/time in epoch seconds"""
        return "{}".format(int(time.time()))
