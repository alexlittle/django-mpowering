# -*- coding: utf-8 -*-

"""
Exports a course to Moodle format

Incoming course content is expected to look like this:

    [{
        "resources": [{
            "type": "CourseActivity",
            "description": "Hello world",
            "title": "Funky town"
        }, {
            "type": "CourseActivity",
            "description": "The end",
            "title": "Good bye"
        }]
    }, {
        "resources": [{
            "type": "CourseActivity",
            "description": "Second section description",
            "title": "Second section title"
        }]
    }]

The MoodleCourse class is used to export to a Moodle backup format

"""
from __future__ import unicode_literals

import hashlib
import sys
import time
from StringIO import StringIO
from typing import Dict  # noqa
from typing import List  # noqa
from zipfile import ZipFile

from dicttoxml import dicttoxml
from django.template.loader import render_to_string
from django.utils.functional import cached_property
from django.utils.html import escape
from django.utils.safestring import SafeText  # noqa

from orb.courses.export import CourseExport, format_page_as_markdown, sequenced_string


class MoodleCourse(CourseExport):
    """
    Represents a Moodle course
    """

    encoding_string = '<?xml version="1.0" encoding="UTF-8" ?>'
    default_filename = "orb-course.mbz"

    def __init__(self, name, id, sections=None, activities=None, **kwargs):
        """

        Args:
            name: name of the course
            id: given ID in the system
            content: all course content in a list by sections
            **kwargs:
        """
        super(MoodleCourse, self).__init__(
            name, id, sections=sections, activities=activities, **kwargs
        )

        # Add an empty 'general' section
        self.sections.insert(0, {"id": 1, "sequence": []})
        self.hashed_site_identifier = kwargs.pop("hashed_site_identifier", "")  # md5

    def validate_backup_filename(self):
        if not self.backup_filename.endswith(".mbz"):
            raise ValueError(
                "Moodle backup file names must end with the .mbz extension"
            )

    def files_xml(self):
        """
          <file id="279691">
    <contenthash>c7ee6c50edffc243138420eed2f8e94ce84478a8</contenthash>
    <contextid>39751</contextid>
    <component>course</component>
    <filearea>summary</filearea>
    <itemid>0</itemid>
    <filepath>/</filepath>
    <filename>anc.small.png</filename>
    <userid>2</userid>
    <filesize>9043</filesize>
    <mimetype>image/png</mimetype>
    <status>0</status>
    <timecreated>1405527815</timecreated>
    <timemodified>1405527822</timemodified>
    <source>anc.small.png</source>
    <author>Alex Little</author>
    <license>allrightsreserved</license>
    <sortorder>0</sortorder>
    <repositorytype>$@NULL@$</repositorytype>
    <repositoryid>$@NULL@$</repositoryid>
    <reference>$@NULL@$</reference>
  </file>
        """
        wrapper = """<?xml version="1.0" encoding="UTF-8"?><files>{}</files>"""
        inner = "".join(
            [
                """
          <file id="{id}">
    <contenthash>{sha}</contenthash>
    <contextid>{contextid}</contextid>
    <component>mod_resource</component>
    <filearea>content</filearea>
    <itemid>0</itemid>
    <filepath>/</filepath>
    <filename>{filename}</filename>
    <userid>2</userid>
    <filesize>{size}</filesize>
    <mimetype>{mimetype}</mimetype>
    <status>0</status>
    <timecreated>{created}</timecreated>
    <timemodified>{modified}</timemodified>
    <source>{filename}</source>
    <author>{author}</author>
    <license>{license}</license>
    <sortorder>0</sortorder>
    <repositorytype>$@NULL@$</repositorytype>
    <repositoryid>$@NULL@$</repositoryid>
    <reference>$@NULL@$</reference>
  </file>""".format(
                    id=f["id"],
                    contextid=f["id"],
                    author=f["author"],
                    sha=f["file_sha"],
                    size=f["file_size"],
                    filename=f["file_name"],
                    mimetype=f["file_mimetype"],
                    created=f["created"],
                    modified=f["modified"],
                    license=f["license"],
                )
                for f in self.resources()
            ]
        )
        return wrapper.format(inner)

    def convert_xml(self, keys, pretty=False):
        if isinstance(keys, str) or isinstance(keys, unicode):
            keys = {keys: None}

        result = self.encoding_string + dicttoxml(keys, attr_type=False, root=False)
        return result

    @property
    def original_wwwroot(self):
        return "http://moodle.digital-campus.org"

    @property
    def original_course_startdate(self):
        # type: () -> str
        """Returns a datetime in epoch seconds"""
        return "1500332400"

    @property
    def original_course_enddate(self):
        # type: () -> str
        """Returns a datetime in epoch seconds"""
        return "1538697600"

    @property
    def original_course_contextid(self):
        # TODO I have no idea how this is different than course ID
        return "39293"

    @property
    def original_system_contextid(self):
        return "1"

    @cached_property
    def backup_id(self):
        # type: () -> str
        """Returns a 'unique' md5 hash to identify the backup

        Nothing about this must describe the backup contents. Moodle's calculation is:

            Current epoch time + type + id + format + interactive + mode + userid + operation
            should be unique enough. Add one random part at the end

        """
        return hashlib.md5(
            self.name + self.original_wwwroot + self.backup_date
        ).hexdigest()

    def moodle_activities(self):
        # type: () -> List[Dict[str, str]]
        """
        Builds a list of activities for the XML export

            [
                {
                    "moduleid": "37328",
                    "sectionid": "5585",
                    "modulename": "page",
                    "title": "My page title",
                    "directory": "activities/page_37328",
                },
                {
                    "moduleid": "37330",
                    "sectionid": "5585",
                    "modulename": "resource",
                    "title": "Dog body shaming",
                    "directory": "activities/resource_37330",
                },
                {
                    "moduleid": "37329",
                    "sectionid": "5586",
                    "modulename": "url",
                    "title": "Gollum",
                    "directory": "activities/url_37329",
                },
            ]

        Returns:
            Directory and identification information for each course activity

        """
        return [
            {
                "moduleid": str(activity["id"]),
                "sectionid": str(activity["section"]),
                "modulename": activity["type"],
                "title": activity["intro"],
                "directory": "activities/{}_{}".format(
                    activity["type"], activity["id"]
                ),
            }
            for activity in self.activities
        ]

    def moodle_sections(self):
        """Returns a dictionary of section data

        Example::

            {
                "section": [{
                    "sectionid": "5585",
                    "title": "1",
                    "directory": "sections/section_5585"
                }, {
                    "sectionid": "5586",
                    "title": "2",
                    "directory": "sections/section_5586"
                }]
            }

        """
        return [
            {
                "sectionid": str(section["id"]),
                "title": str(section["id"]),
                "directory": "sections/section_{}".format(section["id"]),
            }
            for section in self.sections
        ]

    def moodle_settings(self):
        """Returns the base course/moodle settings

        As-is this is a set of default settings extracted from a limited Moodle export.
        """
        return [
            {"level": "root", "name": "filename", "value": self.backup_filename},
            {"level": "root", "name": "imscc11", "value": "0"},
            {"level": "root", "name": "users", "value": "0"},
            {"level": "root", "name": "anonymize", "value": "0"},
            {"level": "root", "name": "role_assignments", "value": "0"},
            {"level": "root", "name": "activities", "value": "1"},
            {"level": "root", "name": "blocks", "value": "0"},
            {"level": "root", "name": "filters", "value": "0"},
            {"level": "root", "name": "comments", "value": "0"},
            {"level": "root", "name": "badges", "value": "0"},
            {"level": "root", "name": "calendarevents", "value": "0"},
            {"level": "root", "name": "userscompletion", "value": "0"},
            {"level": "root", "name": "logs", "value": "0"},
            {"level": "root", "name": "grade_histories", "value": "0"},
            {"level": "root", "name": "questionbank", "value": "0"},
            {"level": "root", "name": "groups", "value": "0"},
            {"level": "root", "name": "competencies", "value": "0"},
        ]

    def course_settings(self):
        """Returns settings specific to course content"""
        settings_data = []
        for section in self.sections:
            settings_data += [
                {
                    "level": "section",
                    "section": "section_{}".format(section["id"]),
                    "name": "section_{}_included".format(section["id"]),
                    "value": "1",
                },
                {
                    "level": "section",
                    "section": "section_{}".format(section["id"]),
                    "name": "section_{}_userinfo".format(section["id"]),
                    "value": "0",
                },
            ]

        for activity in self.activities:
            settings_data += [
                {
                    "level": "activity",
                    "activity": "{}_{}".format(activity["type"], activity["id"]),
                    "name": "{}_{}_included".format(activity["type"], activity["id"]),
                    "value": "1",
                },
                {
                    "level": "activity",
                    "activity": "{}_{}".format(activity["type"], activity["id"]),
                    "name": "{}_{}_userinfo".format(activity["type"], activity["id"]),
                    "value": "0",
                },
            ]

        return settings_data

    def moodle_backup(self, context):
        # type: (dict) -> SafeText
        """Renders the primary moodle_backup.xml file"""
        return render_to_string("orb/courses/moodle_backup.xml", context).encode("utf8")

    def moodle_backup_context(self):

        """Returns the moodle_backup.xml file"""
        return {
            "information": {
                "name": self.backup_filename,
                "moodle_version": "2017051501.02",
                "moodle_release": "3.3.1+ (Build: 20170720)",
                "backup_version": "2017051500",
                "backup_release": "3.3",
                "backup_date": self.backup_date,
                "mnet_remoteusers": "0",
                "include_files": "1",
                "include_file_references_to_external_content": "0",  # TODO
                "original_wwwroot": self.original_wwwroot,
                "original_site_identifier_hash": self.hashed_site_identifier,
                "original_course_id": self.courseid,
                "original_course_format": "topics",
                "original_course_fullname": self.name,
                "original_course_shortname": self.name,
                "original_course_startdate": self.original_course_startdate,
                "original_course_enddate": self.original_course_enddate,
                "original_course_contextid": self.original_course_contextid,
                "original_system_contextid": self.original_system_contextid,
            },
            "details": {
                "detail": {
                    "backup_id": self.backup_id,
                    "type": "course",
                    "format": "moodle2",
                    "interactive": "1",
                    "mode": "10",
                    "execution": "1",
                    "executiontime": "0",
                }
            },
            "contents": {
                "activities": {"activity": self.moodle_activities()},
                "sections": {"section": self.moodle_sections()},
                "course": {
                    "courseid": self.courseid,
                    "title": self.name,
                    "directory": "course",
                },
            },
            "settings": {"setting": self.moodle_settings() + self.course_settings()},
        }

    def course_xml(self):
        return """<?xml version="1.0" encoding="UTF-8"?>
<course id="414" contextid="39293">
  <shortname>Fun Course</shortname>
  <fullname>My Awesome Fun Course</fullname>
  <idnumber></idnumber>
  <summary>&lt;p&gt;Some descriptive text&lt;/p&gt;</summary>
  <summaryformat>1</summaryformat>
  <format>topics</format>
  <showgrades>1</showgrades>
  <newsitems>5</newsitems>
  <startdate>1500332400</startdate>
  <enddate>0</enddate>
  <marker>0</marker>
  <maxbytes>0</maxbytes>
  <legacyfiles>0</legacyfiles>
  <showreports>0</showreports>
  <visible>1</visible>
  <groupmode>0</groupmode>
  <groupmodeforce>0</groupmodeforce>
  <defaultgroupingid>0</defaultgroupingid>
  <lang></lang>
  <theme></theme>
  <timecreated>1500307572</timecreated>
  <timemodified>1500307662</timemodified>
  <requested>0</requested>
  <enablecompletion>0</enablecompletion>
  <completionnotify>0</completionnotify>
  <hiddensections>0</hiddensections>
  <coursedisplay>0</coursedisplay>
  <category id="50">
    <name>CHA</name>
    <description></description>
  </category>
  <tags>
  </tags>
</course>"""

    def resource_xml(self, activity):
        """Returns

        Uses string formatting b/c dicttoxml doesn't support attributes
        """
        return """<?xml version="1.0" encoding="UTF-8"?>
<activity id="{id}" moduleid="{moduleid}" modulename="resource" contextid="{contextid}">
  <resource id="{id}">
    <name>{name}</name>
    <intro></intro>
    <introformat>1</introformat>
    <tobemigrated>0</tobemigrated>
    <legacyfiles>0</legacyfiles>
    <legacyfileslast>$@NULL@$</legacyfileslast>
    <display>0</display>
    <displayoptions>a:1:{{s:10:"printintro";i:1;}}</displayoptions>
    <filterfiles>0</filterfiles>
    <revision>1</revision>
    <timemodified>{timestamp}</timemodified>
  </resource>
</activity>""".format(
            id=activity["id"],
            moduleid=activity["id"],
            contextid=activity["id"],
            name=activity["intro"],
            timestamp="{}".format(int(time.time())),
        )

    def page_xml(self, activity):
        """Returns

        Uses string formatting b/c dicttoxml doesn't support attributes
        """
        return """<?xml version="1.0" encoding="UTF-8"?>
<activity id="{id}" moduleid="{moduleid}" modulename="page" contextid="{contextid}">
  <page id="{id}">
    <name>{name}</name>
    <intro>{intro_html}</intro>
    <introformat>1</introformat>
    <content>{content_html}</content>
    <contentformat>1</contentformat>
    <legacyfiles>0</legacyfiles>
    <legacyfileslast>$@NULL@$</legacyfileslast>
    <display>5</display>
    <displayoptions>a:2:{{s:12:"printheading";s:1:"1";s:10:"printintro";s:1:"0";}}</displayoptions>
    <revision>1</revision>
    <timemodified>{timestamp}</timemodified>
  </page>
</activity>""".format(
            id=activity["id"],
            moduleid=activity["id"],
            contextid=activity["id"],
            name=activity["intro"],
            intro_html=activity["intro"],
            content_html=escape(format_page_as_markdown(activity)),
            timestamp="{}".format(int(time.time())),
        )

    def activity_xml(self, activity):
        return (
            self.resource_xml(activity)
            if activity["type"] == "resource"
            else self.page_xml(activity)
        )

    def activity_module_xml(self, activity):
        return """<?xml version="1.0" encoding="UTF-8"?>
<module id="{moduleid}" version="{versionid}">
  <modulename>{activity_type}</modulename>
  <sectionid>{sectionid}</sectionid>
  <sectionnumber>{sectionnum}</sectionnumber>
  <idnumber></idnumber>
  <added>1500307814</added>
  <score>0</score>
  <indent>0</indent>
  <visible>1</visible>
  <visibleoncoursepage>1</visibleoncoursepage>
  <visibleold>1</visibleold>
  <groupmode>0</groupmode>
  <groupingid>0</groupingid>
  <completion>0</completion>
  <completiongradeitemnumber>$@NULL@$</completiongradeitemnumber>
  <completionview>0</completionview>
  <completionexpected>0</completionexpected>
  <availability>$@NULL@$</availability>
  <showdescription>0</showdescription>
  <tags>
  </tags>
</module>""".format(
            activity_type=activity["type"],
            moduleid=activity["id"],
            sectionid=activity["section"],
            sectionnum=activity["section"],
            versionid=2017051500,
        )

    def section_xml(self, section):
        """Uses string formatting b/c dicttoxml doesn't support attributes"""
        return """<?xml version="1.0" encoding="UTF-8"?>
<section id="{id}">
  <number>{id}</number>
  <name>{id}</name>
  <summary></summary>
  <summaryformat>1</summaryformat>
  <sequence>{sequence}</sequence>
  <visible>1</visible>
  <availabilityjson>$@NULL@$</availabilityjson>
</section>""".format(
            id=section["id"], sequence=sequenced_string(section["sequence"])
        )

    def course_enrollments(self):
        return """<?xml version="1.0" encoding="UTF-8"?>
<enrolments>
  <enrols>
    <enrol id="1369">
      <enrol>manual</enrol>
      <status>0</status>
      <name>$@NULL@$</name>
      <enrolperiod>0</enrolperiod>
      <enrolstartdate>0</enrolstartdate>
      <enrolenddate>0</enrolenddate>
      <expirynotify>0</expirynotify>
      <expirythreshold>86400</expirythreshold>
      <notifyall>0</notifyall>
      <password>$@NULL@$</password>
      <cost>$@NULL@$</cost>
      <currency>$@NULL@$</currency>
      <roleid>5</roleid>
      <customint1>$@NULL@$</customint1>
      <customint2>$@NULL@$</customint2>
      <customint3>$@NULL@$</customint3>
      <customint4>$@NULL@$</customint4>
      <customint5>$@NULL@$</customint5>
      <customint6>$@NULL@$</customint6>
      <customint7>$@NULL@$</customint7>
      <customint8>$@NULL@$</customint8>
      <customchar1>$@NULL@$</customchar1>
      <customchar2>$@NULL@$</customchar2>
      <customchar3>$@NULL@$</customchar3>
      <customdec1>$@NULL@$</customdec1>
      <customdec2>$@NULL@$</customdec2>
      <customtext1>$@NULL@$</customtext1>
      <customtext2>$@NULL@$</customtext2>
      <customtext3>$@NULL@$</customtext3>
      <customtext4>$@NULL@$</customtext4>
      <timecreated>1500307572</timecreated>
      <timemodified>1500307572</timemodified>
      <user_enrolments>
      </user_enrolments>
    </enrol>
    <enrol id="1370">
      <enrol>guest</enrol>
      <status>0</status>
      <name>$@NULL@$</name>
      <enrolperiod>0</enrolperiod>
      <enrolstartdate>0</enrolstartdate>
      <enrolenddate>0</enrolenddate>
      <expirynotify>0</expirynotify>
      <expirythreshold>0</expirythreshold>
      <notifyall>0</notifyall>
      <password></password>
      <cost>$@NULL@$</cost>
      <currency>$@NULL@$</currency>
      <roleid>0</roleid>
      <customint1>$@NULL@$</customint1>
      <customint2>$@NULL@$</customint2>
      <customint3>$@NULL@$</customint3>
      <customint4>$@NULL@$</customint4>
      <customint5>$@NULL@$</customint5>
      <customint6>$@NULL@$</customint6>
      <customint7>$@NULL@$</customint7>
      <customint8>$@NULL@$</customint8>
      <customchar1>$@NULL@$</customchar1>
      <customchar2>$@NULL@$</customchar2>
      <customchar3>$@NULL@$</customchar3>
      <customdec1>$@NULL@$</customdec1>
      <customdec2>$@NULL@$</customdec2>
      <customtext1>$@NULL@$</customtext1>
      <customtext2>$@NULL@$</customtext2>
      <customtext3>$@NULL@$</customtext3>
      <customtext4>$@NULL@$</customtext4>
      <timecreated>1500307572</timecreated>
      <timemodified>1500307572</timemodified>
      <user_enrolments>
      </user_enrolments>
    </enrol>
    <enrol id="1371">
      <enrol>self</enrol>
      <status>0</status>
      <name>$@NULL@$</name>
      <enrolperiod>0</enrolperiod>
      <enrolstartdate>0</enrolstartdate>
      <enrolenddate>0</enrolenddate>
      <expirynotify>0</expirynotify>
      <expirythreshold>86400</expirythreshold>
      <notifyall>0</notifyall>
      <password>$@NULL@$</password>
      <cost>$@NULL@$</cost>
      <currency>$@NULL@$</currency>
      <roleid>5</roleid>
      <customint1>0</customint1>
      <customint2>10368000</customint2>
      <customint3>0</customint3>
      <customint4>0</customint4>
      <customint5>0</customint5>
      <customint6>1</customint6>
      <customint7>$@NULL@$</customint7>
      <customint8>$@NULL@$</customint8>
      <customchar1>$@NULL@$</customchar1>
      <customchar2>$@NULL@$</customchar2>
      <customchar3>$@NULL@$</customchar3>
      <customdec1>$@NULL@$</customdec1>
      <customdec2>$@NULL@$</customdec2>
      <customtext1>$@NULL@$</customtext1>
      <customtext2>$@NULL@$</customtext2>
      <customtext3>$@NULL@$</customtext3>
      <customtext4>$@NULL@$</customtext4>
      <timecreated>1500307572</timecreated>
      <timemodified>1500307572</timemodified>
      <user_enrolments>
      </user_enrolments>
    </enrol>
  </enrols>
</enrolments>"""

    def roles_xml(self):
        return """<?xml version="1.0" encoding="UTF-8"?>
<roles_definition>
  <role id="5">
    <name>Student</name>
    <shortname>student</shortname>
    <nameincourse>$@NULL@$</nameincourse>
    <description>Students generally have fewer privileges within a course.</description>
    <sortorder>4</sortorder>
    <archetype>student</archetype>
  </role>
</roles_definition>"""

    def gradebook_xml(self):
        return """<?xml version="1.0" encoding="UTF-8"?>
<gradebook>
  <attributes>
  </attributes>
  <grade_categories>
  </grade_categories>
  <grade_items>
  </grade_items>
  <grade_letters>
  </grade_letters>
  <grade_settings>
    <grade_setting id="">
      <name>minmaxtouse</name>
      <value>1</value>
    </grade_setting>
  </grade_settings>
</gradebook>"""

    def activity_inforef_xml(self, activity):
        """Returns the inforef.xml content for an activity"""
        if activity["type"] == "resource":
            return self.convert_xml(
                {"inforef": {"fileref": {"file": {"id": activity["id"]}}}}
            )
        return self.convert_xml("inforef")

    def export(self):
        """
        Generates a Moodle export

        The Moodle backup file is a zipped archive of *top-level* components
        using the `mbz` extension.
        """

        backup_file = StringIO()

        with ZipFile(backup_file, "w") as moodle_backup:

            moodle_backup.writestr(
                "completion.xml", self.convert_xml("course_completion")
            )
            moodle_backup.writestr("files.xml", self.files_xml())
            # moodle_backup.writestr('completion.xml', self.convert_xml('course_completion'))

            moodle_backup.writestr(
                "grade_history.xml",
                self.convert_xml({"grade_history": {"grade_grades": None}}),
            )
            moodle_backup.writestr("gradebook.xml", self.gradebook_xml())
            moodle_backup.writestr(
                "groups.xml", self.convert_xml({"groups": {"groupings": None}})
            )
            moodle_backup.writestr("moodle_backup.log", "")
            moodle_backup.writestr(
                "moodle_backup.xml", self.moodle_backup(self.moodle_backup_context())
            )
            moodle_backup.writestr(
                "outcomes.xml", self.convert_xml("outcomes_definition")
            )
            moodle_backup.writestr(
                "questions.xml", self.convert_xml("question_categories")
            )
            moodle_backup.writestr("roles.xml", self.roles_xml())
            moodle_backup.writestr("scales.xml", self.convert_xml("scales_definition"))

            moodle_backup.writestr("course/course.xml", self.course_xml()),
            moodle_backup.writestr(
                "course/completiondefaults.xml",
                self.convert_xml("course_completion_defaults"),
            )
            moodle_backup.writestr(
                "course/roles.xml",
                self.convert_xml(
                    {"roles": {"role_overrides": None, "role_assignments": None}}
                ),
            )
            moodle_backup.writestr(
                "course/inforef.xml",
                self.convert_xml({"inforef": {"roleref": {"role": 5}}}),
            )

            for course_resource in self.resources():
                with open(course_resource["file_path"], "rb") as rf:
                    moodle_backup.writestr(course_resource["export_path"], rf.read())

            for section in self.sections:
                moodle_backup.writestr(
                    "sections/section_{id}/inforef.xml".format(id=section["id"]),
                    self.convert_xml("inforef"),
                )
                moodle_backup.writestr(
                    "sections/section_{id}/section.xml".format(id=section["id"]),
                    self.section_xml(section),
                )

            for activity in self.activities:
                # [x] grade_history
                # [x] grades
                # [x] inforef
                # [ ] module
                # [ ] page
                # [x] roles
                moodle_backup.writestr(
                    "activities/{type}_{id}/inforef.xml".format(
                        type=activity["type"], id=activity["id"]
                    ),
                    self.activity_inforef_xml(activity),
                )

                moodle_backup.writestr(
                    "activities/{type}_{id}/{type}.xml".format(
                        type=activity["type"], id=activity["id"]
                    ),
                    self.activity_xml(activity),
                )

                moodle_backup.writestr(
                    "activities/{type}_{id}/module.xml".format(
                        type=activity["type"], id=activity["id"]
                    ),
                    self.activity_module_xml(activity),
                )

                moodle_backup.writestr(
                    "activities/{type}_{id}/roles.xml".format(
                        type=activity["type"], id=activity["id"]
                    ),
                    """<?xml version="1.0" encoding="UTF-8"?>
<roles>
  <role_overrides>
  </role_overrides>
  <role_assignments>
  </role_assignments>
</roles>""",
                ),
                moodle_backup.writestr(
                    "activities/{type}_{id}/grade_history.xml".format(
                        type=activity["type"], id=activity["id"]
                    ),
                    """<?xml version="1.0" encoding="UTF-8"?>
<grade_history>
  <grade_grades>
  </grade_grades>
</grade_history>""",
                ),
                moodle_backup.writestr(
                    "activities/{type}_{id}/grades.xml".format(
                        type=activity["type"], id=activity["id"]
                    ),
                    """<?xml version="1.0" encoding="UTF-8"?>
<activity_gradebook>
  <grade_items>
  </grade_items>
  <grade_letters>
  </grade_letters>
</activity_gradebook>""",
                ),

        backup_file.seek(0)
        return backup_file


if __name__ == "__main__":
    course = MoodleCourse("My test", 45)
    sys.stdout.write(course.export().getvalue())
