# -*- coding: utf-8 -*-

"""
Tests for the courses app
"""

from __future__ import unicode_literals

import pytest

from orb.courses.export import format_page_as_markdown
from orb.courses.moodle_export import MoodleCourse


@pytest.fixture
def empty_course():
    yield MoodleCourse("Empty Course", 7, backup_filename="empty.mbz")


@pytest.fixture
def short_course():
    yield MoodleCourse(
        "Short course",
        9,
        sections=[{"id": 1, "sequence": [1, 2]}, {"id": 2, "sequence": [3]}],
        activities=[
            {
                "id": 1,
                "type": "page",
                "intro": "First slide",
                "content": "Hello world",
                "section": 1,
            },
            {
                "id": 2,
                "type": "page",
                "intro": "Intermission",
                "content": "Olé!",
                "section": 1,
            },
            {
                "id": 3,
                "type": "page",
                "intro": "Second section title",
                "content": "Second section description",
                "section": 2,
            },
        ],
    )


def test_backup_id(empty_course):
    assert isinstance(empty_course.backup_id, str)
    assert len(empty_course.backup_id) == 32


def test_backup_filename(empty_course, short_course):
    # specified
    assert empty_course.backup_filename == "empty.mbz"

    # default
    assert short_course.backup_filename == "orb-course.mbz"

    # Wrong extension
    with pytest.raises(ValueError):
        MoodleCourse("Error Course", 7, backup_filename="empty.zip")


def test_moodle_sections(short_course):
    assert short_course.moodle_sections() == [
        {"sectionid": "1", "title": "1", "directory": "sections/section_1"},
        {"sectionid": "2", "title": "2", "directory": "sections/section_2"},
        {"sectionid": "3", "title": "3", "directory": "sections/section_3"},
    ]


def test_moodle_activities(short_course):
    """Should build a list of dictionaries"""
    assert short_course.moodle_activities() == [
        {
            "moduleid": "1",
            "sectionid": "2",
            "modulename": "page",
            "title": "First slide",
            "directory": "activities/page_1",
        },
        {
            "moduleid": "2",
            "sectionid": "2",
            "modulename": "page",
            "title": "Intermission",
            "directory": "activities/page_2",
        },
        {
            "moduleid": "3",
            "sectionid": "3",
            "modulename": "page",
            "title": "Second section title",
            "directory": "activities/page_3",
        },
    ]


def test_course_settings(short_course):
    def settings_sorter(setting):
        return setting["name"]

    expected = [
        {
            "level": "section",
            "section": "section_1",
            "name": "section_1_included",
            "value": "1",
        },
        {
            "level": "section",
            "section": "section_1",
            "name": "section_1_userinfo",
            "value": "0",
        },
        {
            "level": "section",
            "section": "section_2",
            "name": "section_2_included",
            "value": "1",
        },
        {
            "level": "section",
            "section": "section_2",
            "name": "section_2_userinfo",
            "value": "0",
        },
        {
            "level": "activity",
            "activity": "page_1",
            "name": "page_1_included",
            "value": "1",
        },
        {
            "level": "activity",
            "activity": "page_1",
            "name": "page_1_userinfo",
            "value": "0",
        },
        {
            "level": "activity",
            "activity": "page_2",
            "name": "page_2_included",
            "value": "1",
        },
        {
            "level": "activity",
            "activity": "page_2",
            "name": "page_2_userinfo",
            "value": "0",
        },
        {
            "level": "section",
            "section": "section_3",
            "name": "section_3_included",
            "value": "1",
        },
        {
            "level": "section",
            "section": "section_3",
            "name": "section_3_userinfo",
            "value": "0",
        },
        {
            "level": "activity",
            "activity": "page_3",
            "name": "page_3_included",
            "value": "1",
        },
        {
            "level": "activity",
            "activity": "page_3",
            "name": "page_3_userinfo",
            "value": "0",
        },
    ]

    results = short_course.course_settings()

    assert len(results) == len(expected)

    assert sorted(results, key=settings_sorter) == sorted(expected, key=settings_sorter)


def test_page_activity_formatting():
    """Should render as HTML"""
    activity = {
        "id": 1,
        "type": "page",
        "intro": "First slide",
        "content": "Hello world!\n\nFoo bar.",
        "section": 1,
    }
    expected = """<h1>First slide</h1>\n<p>Hello world!</p>\n<p>Foo bar.</p>"""
    result = format_page_as_markdown(activity).strip()
    assert expected == result
