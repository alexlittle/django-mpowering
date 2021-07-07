# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest

from orb.models import ResourceTag, Tag, TagTracker
from orb.resources.tests.factory import resource_factory
from orb.tags.tests.factory import tag_factory


@pytest.mark.django_db
def test_merge_overlap(testing_user):
    """Tests merge with resources shared and not shared between tags"""
    winner_tag = tag_factory(user=testing_user)
    loser_tag = tag_factory(user=testing_user)

    shared_resource = resource_factory(user=testing_user)
    other_resource = resource_factory(user=testing_user)

    # Can't use add on m2m using defined intermediary model
    ResourceTag.objects.create(tag=winner_tag, resource=shared_resource, create_user=testing_user)
    ResourceTag.objects.create(tag=loser_tag, resource=shared_resource, create_user=testing_user)
    ResourceTag.objects.create(tag=loser_tag, resource=other_resource, create_user=testing_user)

    TagTracker.objects.create(user=testing_user, tag=winner_tag, extra_data="1")
    TagTracker.objects.create(user=testing_user, tag=loser_tag, extra_data="2")
    TagTracker.objects.create(user=testing_user, tag=loser_tag, extra_data="3")

    # Quick sanity check
    assert shared_resource.tags.all().count() == 2
    assert other_resource.tags.all().count() == 1
    assert winner_tag.tracker.all().count() == 1

    winner_tag.merge(loser_tag)

    assert shared_resource.tags.all().count() == 1
    assert Tag.tags.all().count() == 1
    assert winner_tag.tracker.all().count() == 3
