# -*- coding: utf-8 -*-

"""
Tests for ORB resource views
"""
from __future__ import unicode_literals

import pytest
from django.utils import translation

from orb.models import Tag
from orb.views import resource_add_free_text_tags


@pytest.mark.django_db
def test_default_language_duplicate_tags(sample_category, testing_user, test_resource):
    """
    Duplicate tags should not be added based on duplicate name across current language to default

    This should result in no errors

    """
    t = Tag.tags.create(
        name="My Fun Test",
        category=sample_category,
        create_user=testing_user,
        update_user=testing_user,
    )

    tag_text = "My Fun Test"

    resource_add_free_text_tags(test_resource, tag_text, testing_user, t.category.slug)
    assert Tag.tags.all().count() == 1

    translation.activate("es")

    resource_add_free_text_tags(test_resource, tag_text, testing_user, t.category.slug)
    assert Tag.tags.all().count() == 1

    Tag.tags.all().delete()
    translation.deactivate()


@pytest.mark.skip("We're down to one language")
@pytest.mark.django_db
def test_other_language_duplicate_tags(sample_category, testing_user, test_resource):
    t = Tag.tags.create(
        name="Child",
        category=sample_category,
        create_user=testing_user,
        update_user=testing_user,
    )

    assert Tag.tags.all().count() == 1

    translation.activate("es")

    tag_text = "Child"
    resource_add_free_text_tags(test_resource, tag_text, testing_user, t.category.slug)
    assert Tag.tags.all().count() == 1

    tag_text = "Niño"
    resource_add_free_text_tags(test_resource, tag_text, testing_user, t.category.slug)
    assert Tag.tags.all().count() == 1

    Tag.tags.all().delete()

    translation.deactivate()
