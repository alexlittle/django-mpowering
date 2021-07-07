"""
Oppia backup-format export for courses

"""
from __future__ import unicode_literals

import zipfile
from StringIO import StringIO

from django.template.loader import render_to_string
from lxml import etree
from pathlib2 import Path

from orb.courses.export import CourseExport, format_page_as_markdown

module_base = Path(__file__).parent  # Directory in which this file lives


class OppiaExport(CourseExport):
    """
    Builds structure for exporting to an Oppia compatible format

    It starts from a base zip file that contains the common folders
    and files in an Oppia export.

    For each resource (file): write it to resources/file-name.
    The metadata goes in module.xml

    We track order of sections and order of activities in sectiosn

    everythign has a digest.


    """

    default_filename = "orb-course.zip"

    def __init__(self, *args, **kwargs):
        super(OppiaExport, self).__init__(*args, **kwargs)

        for section in self.sections:
            for activity in section["activities"]:
                if activity["type"] == "page":
                    activity["html"] = self.page_filename(activity)

    def validate_backup_filename(self):
        if not self.backup_filename.endswith(".zip"):
            raise ValueError("Oppia backup file names must end with the .zip extension")

    def format_page(self, activity):
        return render_to_string(
            "orb/courses/oppia_page.html",
            {"content": format_page_as_markdown(activity)},
        ).encode("utf8")

    def page_filename(self, activity):
        return "{}_{}_{}.html".format(
            activity["section"], activity["digest"][-5:], "en"
        )

    def page_filename_fullpath(self, activity):
        return "{}/{}".format(self.slug, self.page_filename(activity))

    def write_pages(self, backup_file):
        for course_resource in self.pages():
            page_html = self.format_page(course_resource)
            backup_file.writestr(
                self.page_filename_fullpath(course_resource), page_html
            )

    def write_resources(self, backup_file):
        for course_resource in self.resources():
            with open(course_resource["file_path"], "rb") as rf:
                backup_file.writestr(
                    "{}/resources/{}".format(self.slug, course_resource["file_name"]),
                    rf.read(),
                )

    def module_xml(self, context):
        """Validates and returns the module.xml file contents"""

        oppia_xml = render_to_string(
            str(
                module_base.joinpath(
                    "templates/orb/courses/oppia_module.xml"
                ).absolute()
            ),
            context,
        ).encode("utf8")
        schema_source = etree.parse(
            str(module_base.joinpath("oppia-schema.xsd").absolute())
        )
        oppia_schema = etree.XMLSchema(schema_source)
        oppia_xml_tree = etree.fromstring(oppia_xml)
        oppia_schema.assertValid(oppia_xml_tree)
        return oppia_xml

    def module_context(self):
        return dict(
            shortname=self.name,
            title=self.name,
            versionid=1,
            oppia_server="",
            sections=self.sections,
        )

    def export(self, backup_file=None):
        """Performs the full backup"""
        if not backup_file:
            backup_file = StringIO()

        base_export_path = module_base.joinpath("ORB_Course")

        with zipfile.ZipFile(
            backup_file, "a", compression=zipfile.ZIP_DEFLATED
        ) as updated_backup_file:

            for file_path in base_export_path.glob("**/*.*"):
                updated_backup_file.write(
                    str(file_path.absolute()),
                    arcname="{}/{}".format(
                        self.slug, str(file_path.relative_to(base_export_path))
                    ),
                )

            updated_backup_file.writestr(
                "{}/module.xml".format(self.slug),
                self.module_xml(self.module_context()),
            )
            self.write_pages(updated_backup_file)
            self.write_resources(updated_backup_file)

        backup_file.seek(0)
        return backup_file
