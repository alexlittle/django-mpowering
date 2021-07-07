# -*- coding: utf-8 -*-

"""
Tests for the courses app
"""

from __future__ import unicode_literals

import json

import pytest
from django.contrib.auth.models import AnonymousUser
from django.urls import reverse

from orb.courses import forms, models
from orb.tests.utils import login_client


@pytest.fixture
def course(testing_user):
    """Returns a published course"""
    return models.Course.courses.create(
        create_user=testing_user,
        update_user=testing_user,
        title="My first course",
        status=models.CourseStatus.published,
    )


@pytest.fixture
def draft_course(testing_user):
    """Returns a draft course"""
    return models.Course.courses.create(
        create_user=testing_user,
        update_user=testing_user,
        title="Draft course",
        status=models.CourseStatus.draft,
    )


@pytest.fixture
def archived_course(testing_user):
    """Returns an archived course"""
    return models.Course.courses.create(
        create_user=testing_user,
        update_user=testing_user,
        title="Archived course",
        status=models.CourseStatus.archived,
    )


form_test_data = [
    (None, "", None, "", None, False),
    ("", "", None, "", True, False),
    ("", "", "", "health", True, False),
    ("http://orb.com", "", "", "dogs,cats", False, False),
    ("http://orb.com", "hey", "", "dogs, cats", True, False),
    ("http://orb.com", "", "kjaksd", "hey,okay", True, False),
    ("http://orb.com", "", "kjaksd", "hey, okay", True, False),
    ("http://", "kjsakdj", "kjaksd", "hey,okay", False, False),
    ("", "kjsakdj", "kjaksd", "kjd", True, False),
    ("http://orb.com", "kjsakdj", "kjaksd", "health, videos", False, True),
    ("http://orb.com", "kjsakdj", "kjaksd", "health, videos", True, True),
    ("http://orb.com", "kjsakdj", "kjaksd", "health, videos", None, True),
    ("http://orb.com", "kjsakdj", "kjaksd", "    ", True, False),
]


@pytest.mark.parametrize(
    "host,username,password,tags,is_draft,expected", form_test_data
)
def test_form_validation(host, username, password, tags, is_draft, expected):
    form = forms.OppiaPublishForm(
        data={
            "host": host,
            "username": username,
            "password": password,
            "tags": tags,
            "is_draft": is_draft,
        }
    )
    assert form.is_valid() == expected
    assert form.cleaned_data["is_draft"] == bool(is_draft)


tag_test_data = [
    ("", False),
    (", ,,, ,,", False),
    (", ,,kjakdj, ,,", True),
    ("Hey", True),
]


@pytest.mark.parametrize("tags,expected", tag_test_data)
def test_tags_cleaning(tags, expected):
    form = forms.OppiaPublishForm(
        data={
            "host": "https://www.orb.org",
            "username": "bob",
            "password": "kjaskdjdk1k11jska",
            "tags": tags,
            "is_draft": False,
        }
    )
    assert form.is_valid() == expected


@pytest.mark.django_db
def test_course_versioning(draft_course):
    """Ensure course versions increment"""
    version = draft_course.version
    draft_course.save()
    assert draft_course.version == version + 1
    draft_course.save()
    assert draft_course.version == version + 2


@pytest.mark.django_db
def test_editable_queryset(
    course, draft_course, archived_course, testing_user, import_user, admin_user
):
    assert [course, draft_course] == list(models.Course.courses.editable(testing_user))
    assert [course, draft_course] == list(models.Course.courses.editable(admin_user))
    assert [] == list(models.Course.courses.editable(import_user))
    assert [] == list(models.Course.courses.editable(AnonymousUser()))


@pytest.mark.django_db
def test_viewable_queryset(
    course, draft_course, archived_course, testing_user, import_user, admin_user
):
    assert [course, draft_course] == list(models.Course.courses.viewable(testing_user))
    assert [course, draft_course] == list(models.Course.courses.viewable(admin_user))
    assert [course] == list(models.Course.courses.viewable(import_user))
    assert [course] == list(models.Course.courses.viewable(AnonymousUser()))


@pytest.mark.django_db
def test_anon_users(client):
    response = client.get(reverse("courses_list"))
    assert response.status_code == 200


def test_authd_users(admin_client):
    response = admin_client.get(reverse("courses_list"))
    assert response.status_code == 200


def test_form_valid_json_data():
    form = forms.CourseForm(data={"sections": "[]", "title": "Hello World"})
    assert form.is_valid()


def test_form_invalid_json_data():
    form = forms.CourseForm(data={"sections": "jakdj", "title": "Hello World"})
    assert not form.is_valid()


def test_save_course_form(admin_user, testing_user):
    form = forms.CourseForm(
        user=admin_user, data={"sections": "[]", "title": "Hello World"}
    )
    assert form.is_valid()
    course = form.save()

    assert course.create_user == course.update_user == admin_user

    form = forms.CourseForm(
        user=testing_user,
        data={"sections": "[]", "title": "Hello World"},
        instance=course,
    )
    assert form.is_valid()
    course = form.save()
    assert course.create_user == admin_user
    assert course.update_user == testing_user


@pytest.mark.django_db
def test_admin_can_edit_course(course, admin_client, rf):
    response = admin_client.get(reverse("courses_edit", kwargs={"pk": course.pk}))
    assert response.status_code == 200

    response = admin_client.post(
        reverse("courses_edit", kwargs={"pk": course.pk}),
        data=json.dumps(
            {
                "sections": "[]",
                "title": "Hello",
                "status": models.CourseStatus.draft.label,
            }
        ),
        content_type="application/json",
    )
    assert response.status_code == 200


@pytest.mark.django_db
def test_owner_can_edit_course(testing_profile, client, course):
    with login_client(client, username="tester", password="password"):
        response = client.get(reverse("courses_edit", kwargs={"pk": course.pk}))
        assert response.status_code == 200

        response = client.post(
            reverse("courses_edit", kwargs={"pk": course.pk}),
            json.dumps({"sections": "[]", "title": "Hello"}),
            content_type="application/json",
        )
        assert response.status_code == 200


@pytest.mark.django_db
def test_non_owner_cannot_edit_course(importer_profile, client, course):
    with login_client(client, username="importer", password="password"):
        response = client.get(reverse("courses_edit", kwargs={"pk": course.pk}))
        assert response.status_code == 200

        response = client.post(
            reverse("courses_edit", kwargs={"pk": course.pk}),
            json.dumps({"sections": "[]", "title": "Hello"}),
            content_type="application/json",
        )
        assert response.status_code == 403


def test_moodle_name():
    course = models.Course(title="Thé Best Course")
    assert course.moodle_file_name == "the-best-course.mbz"


def test_section_data():
    data = [
        {
            "resources": [
                {
                    "type": "CourseActivity",
                    "description": "Hello world",
                    "title": "First slide",
                },
                {
                    "type": "CourseActivity",
                    "description": "Olé!",
                    "title": "Intermission",
                },
            ]
        },
        {
            "resources": [
                {
                    "type": "CourseActivity",
                    "description": "Second section description",
                    "title": "Second section title",
                }
            ]
        },
    ]
    course = models.Course(sections=json.dumps(data))
    assert course.section_data() == data


def test_moodle_activities():
    data = [
        {
            "resources": [
                {
                    "type": "CourseActivity",
                    "description": "Hello world",
                    "title": "First slide",
                },
                {
                    "type": "CourseActivity",
                    "description": "Olé!",
                    "title": "Intermission",
                },
            ]
        },
        {
            "resources": [
                {
                    "type": "CourseActivity",
                    "description": "Second section description",
                    "title": "Second section title",
                }
            ]
        },
    ]
    course = models.Course(sections=json.dumps(data))
    sections, activities = course.activities_for_export()

    assert sections == [{"id": 1, "sequence": [1, 2]}, {"id": 2, "sequence": [3]}]

    assert activities == [
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
    ]
