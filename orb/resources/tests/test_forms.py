# -*- coding: utf-8 -*-

"""
Tests for ORB resource forms
"""

from __future__ import unicode_literals

import pytest
from django.conf import settings
from django.test import TestCase, override_settings
from hypothesis import given
from hypothesis import strategies as st
from mock import MagicMock

from orb.forms import ResourceStep2Form
from orb.models import Tag
from orb.resources import forms
from orb.tests.utils import clean_and_strip


class ResourceStep2FormTests(TestCase):
    """Tests for the ResourceStep2Form form class"""

    @classmethod
    def setUpClass(cls):
        super(ResourceStep2FormTests, cls).setUpClass()
        cls.uploaded_file = MagicMock()
        cls.uploaded_file.content_type = "application/pdf"
        cls.uploaded_file.size = 100
        cls.uploaded_file._size = 100

    def test_valid_missing_url_file(self):
        """Form should be invalid when missing both file and URL"""
        form = ResourceStep2Form(data={"title": "¡Olé!"})
        self.assertFalse(form.is_valid())

    def test_valid_url(self):
        """Form should be valid with only a URL

        Unicode is used for good measure to test encoding validation
        """
        form = ResourceStep2Form(data={
            "url": "http://www.wvi.org/publication/manual-para-madres-gu%C3%ADas"})
        self.assertTrue(form.is_valid())

    def test_invalid_url(self):
        """Form shoudl reject invalid URLs"""
        form = ResourceStep2Form(data={"url": "htp://example.com/olé"})
        self.assertFalse(form.is_valid())

    def test_valid_file(self):
        """Form should be valid with only a file"""
        form = ResourceStep2Form(files={"file": self.uploaded_file})
        self.assertTrue(form.is_valid())

    @override_settings(TASK_UPLOAD_FILE_MAX_SIZE=90)
    def test_file_exceeds_maxsize(self):
        """Form should be invalid if file size exceeds maxsize"""
        self.assertEqual(settings.TASK_UPLOAD_FILE_MAX_SIZE, 90)
        form = ResourceStep2Form(files={"file": self.uploaded_file})
        self.assertFalse(form.is_valid())

    @override_settings(TASK_UPLOAD_FILE_TYPE_BLACKLIST=['application/pdf'])
    def test_file_invalid_type(self):
        """Form should be invalid if file type is blacklisted"""
        form = ResourceStep2Form(files={"file": self.uploaded_file})
        self.assertFalse(form.is_valid())


@pytest.mark.django_db
@given(
    st.sampled_from(forms.ResourceAccessForm.INTENDED_USE),  # intended_use
    st.booleans(),  # use_intended_use
    st.text(max_size=2000),  # intended_use_other
    st.booleans(),  # use_intended_use_other
    st.integers(min_value=-10, max_value=100000),  # worker_count
    st.booleans(),  # use_worker_count
    st.booleans(),  # use_worker_cadre
)
def test_resource_access_form(role_tag, intended_use, use_intended_use, intended_use_other, use_intended_use_other,
                              worker_count, use_worker_count, use_worker_cadre):
    """Ensure conditional field validitiy"""
    survey_intended_use = intended_use if use_intended_use else ''
    survey_intended_use_other = clean_and_strip(intended_use_other) if use_intended_use_other else ''
    survey_health_worker_count = worker_count if use_worker_count else None
    survey_health_worker_cadre = role_tag.slug if use_worker_cadre else ''

    assert Tag.tags.all().count() > 0
    assert Tag.tags.roles().count() > 0

    data = {
        'survey_intended_use': survey_intended_use,
        'survey_intended_use_other': survey_intended_use_other,
        'survey_health_worker_count': survey_health_worker_count,
        'survey_health_worker_cadre': survey_health_worker_cadre,
    }

    form = forms.ResourceAccessForm(data=data)
    form_validity = True

    if any([
        not survey_intended_use,
        survey_intended_use == 'other' and not survey_intended_use_other,
        survey_intended_use == 'training' and not survey_health_worker_count,
        survey_intended_use == 'training' and not survey_health_worker_cadre,
        survey_intended_use == 'training' and (survey_health_worker_count and survey_health_worker_count < 1),
    ]):
        form_validity = False

    form.is_valid()

    if form_validity != form.is_valid():
        if form.is_valid():
            print(data)
        else:
            print(form.errors)

    assert form_validity == form.is_valid()

    if form_validity:
        if survey_intended_use in ['browsing', 'learning', 'other']:
            assert not form.cleaned_data.get('survey_health_worker_count')
            assert not form.cleaned_data.get('survey_health_worker_cadre')
        if survey_intended_use in ['browsing', 'learning', 'training']:
            assert not form.cleaned_data.get('survey_intended_use_other')
