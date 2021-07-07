# -*- coding: utf-8 -*-

"""
Models for COVID-19 Library courses
"""

from __future__ import unicode_literals

import json
import logging
from collections import OrderedDict
from enum import Enum
from typing import Optional  # noqa

from autoslugged.settings import slugify
from django.conf import settings
from django.contrib.auth.models import User  # noqa
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext
from six import text_type

from orb.courses.moodle_export import MoodleCourse
from orb.courses.oppia_client import OppiaClient
from orb.courses.oppia_export import OppiaExport
from orb.models import ResourceFile, TimestampBase

logger = logging.getLogger("orb.courses")


class BaseChoices(Enum):
    @classmethod
    def as_choices(cls):
        return [(child.name, child.name) for child in cls]

    @classmethod
    def initial(cls):
        """By default returns the first item"""
        for child in cls:
            return child.name


class CourseStatus(BaseChoices):
    draft = ugettext("Draft")
    published = ugettext("Published")
    archived = ugettext("Archived")


def page_activity(activity_id, intro, content, section):
    """Returns a page activity dictionary

    Separate function to ensure consistent re-use
    """
    return {
        "id": activity_id,
        "type": "page",
        "intro": intro,
        "content": content,
        "section": section,
    }


def render_activity(activity, resource_id, section_count):
    if activity.get("type") == "CourseResource":
        try:
            rf = ResourceFile.objects.get(pk=activity["id"])
        except ResourceFile.DoesNotExist as err:
            return resource_error(resource_id, activity, section_count, err)

        try:
            sha1 = rf.sha1sum()
        except IOError as err:
            return resource_error(resource_id, activity, section_count, err)

        return {
            "id": resource_id,
            "type": "resource",
            "intro": activity["title"],
            "content": activity["description"],
            "section": section_count,
            "file_path": rf.full_path,
            "file_name": rf.filename(),
            "file_sha": sha1,
            "file_size": rf.filesize(),
            "file_mimetype": rf.mimetype,
            "license": rf.license(),
            "author": rf.author(),
            "created": rf.create_timestamp(),
            "modified": rf.update_timestamp(),
            "export_path": "files/{}/{}".format(sha1[:2], sha1),
        }

    return page_activity(
        activity_id=resource_id,
        intro=activity["title"],
        content=activity["description"],
        section=section_count,
    )


def resource_error(resource_id, activity, section_count, err):
    """Handle an error getting a resource file into a Moodle backup"""
    if isinstance(err, IOError):
        logger.error("IOError for resourcefile_id={}".format(activity["id"]))
        return page_activity(
            activity_id=resource_id,
            intro="[ERROR] File missing",
            content="The file for '{}' could not be found for export".format(
                activity["title"]
            ),
            section=section_count,
        )
    if isinstance(err, ObjectDoesNotExist):
        logger.error(
            "ResourceFile missing for resourcefile_id={}".format(activity["id"])
        )
        return page_activity(
            activity_id=resource_id,
            intro="[ERROR] Resource missing",
            content="The specified resource for '{}' might have been deleted prior to export".format(
                activity["title"]
            ),
            section=section_count,
        )
    else:
        logger.exception("Error rendering resource file for backup")
        return page_activity(
            activity_id=resource_id,
            intro="[ERROR] Unknown error",
            content="There was an unknown error export the resource for '{}'".format(
                activity["title"]
            ),
            section=section_count,
        )


class CourseQueryset(models.QuerySet):
    def active(self):
        return self.exclude(status=CourseStatus.archived.name)

    def published(self):
        return self.filter(status=CourseStatus.published.name)

    def archived(self):
        return self.filter(status=CourseStatus.archived.name)

    def viewable(self, user):
        """Returns only those itesm the given user should be able to see"""
        if user == AnonymousUser():
            return self.filter(models.Q(create_user=0))
        """
        if user.is_staff:
            return self.active()
        """
        return self.filter(
            models.Q(status=CourseStatus.published.name) |
            models.Q(create_user=user)
        ).distinct()

    def editable(self, user):
        """Returns only those items the given user should be able to edit"""
        if user == AnonymousUser():
            return self.none()
        if user.is_staff:
            return self.active()
        return self.active().filter(create_user=user)

    def json_repr(self, user=None):
        for instance in self:
            yield instance.json_repr(user=user)


@python_2_unicode_compatible
class Course(TimestampBase):
    """
    Data container for a user-created course
    """

    status = models.CharField(
        max_length=50,
        choices=CourseStatus.as_choices(),
        default=CourseStatus.draft.name,
    )
    create_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="course_create_user"
    )
    update_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="course_update_user"
    )

    title = models.CharField(max_length=200)

    # Previous work with a third party JSON field was unsuccessufl
    sections = models.TextField(default="[]")  # TODO use a proper JSON field

    version = models.IntegerField(editable=False, default=1)

    courses = CourseQueryset.as_manager()
    objects = courses

    def __str__(self):
        return text_type(self.title)

    def save(self, **kwargs):
        if not self.version:
            self.version = 1
        else:
            self.version += 1
        super(Course, self).save(**kwargs)

    def get_absolute_url(self):
        return reverse("courses_edit", kwargs={"pk": self.pk})

    def section_data(self):
        """Returns serialized section data"""
        return json.loads(self.sections)

    def moodle_sections(self):
        """Returns section only data"""
        sections = []
        resource_count = 1

        for index, section in enumerate(self.section_data(), start=1):
            start = resource_count
            end = resource_count + len(section) + 1
            sections.append({"id": index, "sequence": [i for i in range(start, end)]})
            resource_count += len(section)

        return sections

    def resource_files(self):
        """
        Filters activities by resources (files)
        """
        for section in self.section_data():
            for resource in section["resources"]:
                if resource["type"] == "CourseResource":
                    file_data = {}
                    file_data.update(**resource)
                    try:
                        rf = ResourceFile.objects.get(pk=file_data["id"])
                    except ResourceFile.DoesNotExist:
                        logger.error(
                            "ResourceFile missing for export, pk: '{}'".format(
                                file_data["id"]
                            )
                        )
                        continue

                    file_data.update(
                        {
                            "file_path": rf.full_path,
                            "file_sha1": rf.sha1sum(),
                            "file_size": rf.filesize(),
                        }
                    )

                    yield file_data

    def activities_for_export(self):
        # type: () -> (Dict, Dict)
        """
        Returns dictionaries of section and activities content

        Build dictionaries of sections and activities with unique identifiers

        The sections must map the sequence of activities, referencing the activities
        by ID, and the activities must reference their section by ID.

        For this data::

            >>> data = [{
                    "resources": [{
                        "type": "CourseActivity",
                        "description": "Hello world",
                        "title": "First slide"
                    }, {
                        "type": "CourseActivity",
                        "description": "Olé!",
                        "title": "Intermission"
                    }]
                }, {
                    "resources": [{
                        "type": "CourseActivity",
                        "description": "Second section description",
                        "title": "Second section title"
                    }]
                }]

        This should result in data looking like so::

            >>> course = Course(sections=data)
            >>> sections, activities = course.activities_for_export()
            >>> sections
            [{'id': 1, 'sequence': [1, 2]}, {'id': 2, 'sequence': [3]}]

        Returns:
            tuple of dictionaries describing the data

        """
        sections = []
        activities = []
        resource_id = 1

        for section_count, section in enumerate(self.section_data(), start=1):
            section_activities = []
            for activity in section["resources"]:
                activities.append(render_activity(activity, resource_id, section_count))
                section_activities.append(resource_id)
                resource_id += 1
            sections.append({"id": section_count, "sequence": section_activities})

        return sections, activities

    def get_slug(self):
        return slugify(self.title)

    @property
    def oppia_file_name(self):
        """
        Returns the slugified title with a zip extension
        """
        return "{}.zip".format(self.get_slug())

    def oppia_exporter(self):
        return OppiaExport(
            name=self.title, id=self.pk, backup_filename=self.oppia_file_name
        )

    def oppia_backup(self, backup_file=None):
        """
        Returns an archive of the course in zipped Oppia backup format
        """
        sections, activities = self.activities_for_export()
        backup = OppiaExport(self.title, self.pk, sections, activities, self.version)
        return backup.export(backup_file=backup_file)

    @property
    def moodle_file_name(self):
        """
        Returns the slugified title with an mbz extension
        """
        return "{}.mbz".format(slugify(self.title))

    def moodle_backup(self):
        """
        Returns an archive of the course in zipped Moodle backup format

        """
        sections, activities = self.activities_for_export()
        backup = MoodleCourse(
            name=self.title,
            id=self.pk,
            sections=sections,
            activities=activities,
            version=self.version,
            backup_filename=self.moodle_file_name,
        )
        return backup.export()

    def json_repr(self, user=None):
        # type: (Optional[User]) -> OrderedDict
        """JSON-ready representation, useful for templates"""
        course = OrderedDict(
            [
                ("id", self.pk),
                ("title", self.title),
                ("status", self.status),
                ("sections", json.loads(self.sections)),
                ("url", self.get_absolute_url()),
                (
                    "exportRoutes",
                    OrderedDict(
                        [
                            (
                                "moodleExport",
                                reverse(
                                    "courses_moodle_export", kwargs={"pk": self.pk}
                                ),
                            ),
                            (
                                "oppiaExport",
                                reverse("courses_oppia_export", kwargs={"pk": self.pk}),
                            ),
                            (
                                "oppiaPublish",
                                reverse(
                                    "courses_oppia_publish", kwargs={"pk": self.pk}
                                ),
                            ),
                        ]
                    ),
                ),
            ]
        )
        if user:
            course["editable"] = user == self.create_user or user.is_staff
        return course

    @classmethod
    def empty_json_repr(cls):
        return OrderedDict(
            [
                ("id", ""),
                ("title", "New Course"),
                ("status", text_type(CourseStatus.draft)),
            ]
        )


class OppiaPublisherQuerySet(models.QuerySet):
    """QuerySet for OppiaLog"""

    def publish(self, course, user, export_file, **kwargs):
        host = kwargs["host"]
        client = OppiaClient(
            host=host, username=kwargs["username"], password=kwargs["password"]
        )
        tags = kwargs["tags"]
        is_draft = kwargs["is_draft"]
        success, status, message, response = client.publish_course(
            tags, is_draft, export_file
        )
        self.create(
            course=course,
            user=user,
            oppia_host=host,
            status=status,
            success=success,
            response=response,
        )
        return success, status, message


@python_2_unicode_compatible
class OppiaLog(TimestampBase):
    """Logs attempts to publish a course to Oppia"""

    course = models.ForeignKey("Course", related_name="oppia_logs")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="oppia_logs")
    oppia_host = models.URLField()
    status = models.SmallIntegerField(help_text="HTTP status code of the response")
    success = models.BooleanField(default=False)
    response = models.TextField(blank=True)

    objects = OppiaPublisherQuerySet.as_manager()

    def __str__(self):
        return text_type(self.oppia_host)
