"""
Tests for orb.tags.managers.
"""

from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.test import TestCase

from orb.models import Resource, ResourceTag, Tag
from orb.resources.tests.factory import resource_factory
from orb.tags.tests.factory import tag_factory


class FixtureBase(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.user = User.objects.create(username="McTester")
        resource = resource_factory(user=cls.user, status='approved')
        second_resource= resource_factory(user=cls.user, status='pending')
        used_tag = tag_factory(user=cls.user)
        second_tag = tag_factory(user=cls.user)
        unused_tag = tag_factory(user=cls.user)  # noqa
        non_public_tag = tag_factory(user=cls.user, published=False)
        ResourceTag.objects.create(create_user=cls.user, tag=used_tag, resource=resource)
        ResourceTag.objects.create(create_user=cls.user, tag=used_tag, resource=second_resource)
        ResourceTag.objects.create(create_user=cls.user, tag=second_tag, resource=second_resource)
        ResourceTag.objects.create(create_user=cls.user, tag=non_public_tag, resource=second_resource)

    @classmethod
    def tearDownClass(cls):
        ResourceTag.objects.all().delete()
        Resource.objects.all().delete()
        Tag.objects.all().delete()
        User.objects.all().delete()


class ActiveManagerTests(FixtureBase):
    """
    Tests for the active manager class.

    The active manager only returns tags with associated resources
    """
    def test_default_manager(self):
        self.assertEqual(Tag.tags.all().count(), 4)

    def test_active_manager(self):
        self.assertEqual(Tag.tags.public().active().count(), 2)

    def test_approved_method(self):
        """Approved method only returns tags with approved resources"""
        self.assertEqual(Tag.tags.approved().count(), 1)


class ResourceTagManagerTests(FixtureBase):
    """
    Tests for the ResourceTagManager
    """

    def test_default_queryset(self):
        self.assertEqual(ResourceTag.objects.all().count(), 4)

    def test_approved_method(self):
        """Approved method only returns tags with approved resources"""
        self.assertEqual(ResourceTag.objects.approved().count(), 1)
        self.assertEqual(ResourceTag.objects.approved(self.user).count(), 4)
