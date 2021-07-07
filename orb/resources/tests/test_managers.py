# -*- coding: utf-8 -*-

"""
Tests for ORB resource models
"""
from __future__ import unicode_literals

from django.contrib.auth.models import AnonymousUser, User
from django.test import TestCase

from orb.models import Resource, ResourceURL, ReviewerRole, UserProfile
from orb.resources.tests.factory import resource_factory, resource_url_factory


class ResourceTests(TestCase):
    """Tests for the managers associated with the Resource model.

    Tests are consolidated because the returned ApprovedManager queryset should
    be the same as the queryset for the ResourceManager.approved method. Same
    data same tests.
    """

    @classmethod
    def setUpClass(cls):
        """Returns only resources that were sourced from peer instances"""
        cls.user = User.objects.create(username="tester")
        cls.updater = User.objects.create(username="updater")
        cls.staff = User.objects.create(username="staff", is_staff=True)
        role = ReviewerRole.objects.create(name="Medical")
        cls.crt_user = User.objects.create(username="crt")
        profile = UserProfile.objects.create(user=cls.crt_user)
        profile.reviewer_roles.add(role)

        approved = resource_factory(
            user=cls.user,
            title="Básica salud del recién nacido",
            description="Básica salud del recién nacido",
            status=Resource.APPROVED,
        )
        unapproved_user = resource_factory(
            create_user=cls.user,
            update_user=cls.updater,
            title="Unapproved resource",
            description="Unapproved, owned by user",
        )
        unapproved_staff = resource_factory(
            user=cls.staff,
            title="Staff resource",
            description="Unapproved, owned by staff user",
        )
        archived_resource = resource_factory(
            user=cls.staff,
            title="Archived",
            description="Archived, owned by staff user",
            status=Resource.ARCHIVED,
        )

        resource_url_factory(resource=approved, user=cls.user)
        resource_url_factory(resource=unapproved_user, user=cls.user)

    @classmethod
    def tearDownClass(cls):
        User.objects.all().delete()
        Resource.objects.all().delete()
        ReviewerRole.objects.all().delete()

    # Tests for the ResourceManager

    def test_default_manager(self):
        """Sanity check on defaults"""
        self.assertEqual(Resource.objects.all().count(), 4)

    def test_approved(self):
        self.assertEqual(Resource.objects.approved().count(), 1)

    def test_approved_anon(self):
        """Should be equal to default approved count"""
        self.assertEqual(Resource.objects.approved(user=AnonymousUser()).count(), 1)

    def test_approved_creator(self):
        """Should include resources created by user"""
        self.assertEqual(Resource.objects.approved(user=self.user).count(), 2)

    def test_approved_updater(self):
        """Should include resources updated by user"""
        self.assertEqual(Resource.objects.approved(user=self.updater).count(), 2)

    def test_approved_staff(self):
        """Staff should include all resources regardless of status"""
        self.assertEqual(Resource.objects.approved(user=self.staff).count(), 4)

    def test_approved_reviewer(self):
        """Reviewer should include all resources regardless of status"""
        self.assertEqual(Resource.objects.approved(user=self.crt_user).count(), 4)

    # Tests for the ApprovalManager

    def test_approval_manager(self):
        self.assertEqual(Resource.objects.approved().all().count(), 1)

    def test_approved_owner(self):
        """Should include resources created by user"""
        self.assertEqual(Resource.objects.approved(user=self.user).count(), 2)

    # Tests for ResourceURL

    def test_approved_urls(self):
        """Only one resource URL should be returned for anon user"""
        self.assertEqual(ResourceURL.objects.approved(user=AnonymousUser()).count(), 1)

    def test_staff_urls(self):
        """All ResourceURLs should be returned for staff user"""
        self.assertEqual(ResourceURL.objects.approved(user=self.staff).count(), 2)
