# -*- coding: utf-8 -*-

"""
pytest fixtures
"""
from __future__ import unicode_literals

import pytest
from django.contrib.auth.models import User

from orb.models import Category, Tag, UserProfile
from orb.peers.models import Peer
from orb.resources.tests.factory import resource_factory

pytestmark = pytest.mark.django_db


@pytest.fixture
def testing_user():
    user, _ = User.objects.get_or_create(username="tester")
    user.set_password("password")
    user.save()
    yield user


@pytest.fixture
def testing_profile(testing_user):
    yield UserProfile.objects.create(user=testing_user)


@pytest.fixture()
def import_user():
    user, _ = User.objects.get_or_create(username="importer")
    user.set_password("password")
    user.save()
    yield user


@pytest.fixture
def importer_profile(import_user):
    yield UserProfile.objects.create(user=import_user)


@pytest.fixture
def sample_category():
    category, _ = Category.objects.get_or_create(name="test category")
    yield category


@pytest.fixture
def sample_tag(sample_category, testing_user):
    tag, _ = Tag.objects.get_or_create(name="test tag", defaults={
        "category": sample_category,
        "create_user": testing_user,
        "update_user": testing_user,
    })
    yield tag


@pytest.fixture
def role_category():
    category, _ = Category.objects.get_or_create(name="audience")
    yield category


@pytest.fixture
def role_tag(role_category, testing_user):
    tag, _ = Tag.objects.get_or_create(name="cadre", defaults={
        "category": role_category,
        "create_user": testing_user,
        "update_user": testing_user,
    })
    assert Tag.tags.roles()
    yield tag


@pytest.fixture
def test_resource(testing_user):
    yield resource_factory(
        user=testing_user,
        title="Básica salud del recién nacido",
        description="Básica salud del recién nacido",
    )


@pytest.fixture
def peer_instance():
    yield Peer.peers.create(name="Distant COVID-19 Library", host="http://www.orb.org/")


@pytest.fixture
def remote_resource(import_user, peer_instance):
    """Fixture for a remotely created resource"""
    yield resource_factory(
        user=import_user,
        title="A remote resource",
        description="<p>A remote resource</p>",
        source_peer=peer_instance,
    )
