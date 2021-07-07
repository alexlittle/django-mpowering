# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest

from orb.templatetags.translation_tags import translated_fields


@pytest.mark.django_db
def test_translated_fields_tag(test_resource, settings):
    settings.LANGUAGES = [
        ('en','English'),
        # ('es','Español'),
        # ('pt-br','Português'),
    ]
    test_resource.title_en = "Hey"
    # test_resource.title_pt_br = "Ei"
    test_resource.description_en = "Hey"
    # test_resource.description_pt_br = "Ei"
    # test_resource.title_es = "hola"

    # assert set(translated_fields(test_resource, "title")) == {"Hey", "Ei", "hola"}
    # assert set(translated_fields(test_resource, "description")) == {"Hey", "Ei"}
    assert set(translated_fields(test_resource, "title")) == {"Hey"}
    assert set(translated_fields(test_resource, "description")) == {"Hey"}
