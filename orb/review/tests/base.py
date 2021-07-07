# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.test import TestCase

from orb.models import ResourceCriteria, ReviewerRole, UserProfile
from orb.resources.tests.factory import resource_factory
from orb.review.models import ContentReview


class ReviewTestCase(TestCase):
    """
    Base class for setting up common data for testing resource review related views
    """

    @classmethod
    def setUpClass(cls):
        super(ReviewTestCase, cls).setUpClass()

        cls.medical_role, _ = ReviewerRole.objects.get_or_create(name='medical')
        cls.technical_role, _ = ReviewerRole.objects.get_or_create(name='technical')

        cls.staff_user, _ = User.objects.get_or_create(
            username="staff", is_staff=True, email="staff@acme.org")
        cls.reviewer, _ = User.objects.get_or_create(
            username="reviewer", email="reviewer@acme.org")
        cls.nonreviewer, _ = User.objects.get_or_create(
            username="nonreviewer", email="nonreviewer@acme.org")

        cls.profile_one, _ = UserProfile.objects.get_or_create(user=cls.staff_user)
        cls.profile_one.reviewer_roles.add(cls.medical_role)
        cls.profile_two, _ = UserProfile.objects.get_or_create(user=cls.reviewer)
        cls.profile_two.reviewer_roles.add(cls.technical_role)

        cls.resource = resource_factory(
            user=cls.nonreviewer,
            title="Básica salud del recién nacido",
            description="Básica salud del recién nacido",
        )

    @classmethod
    def tearDownClass(cls):
        super(ReviewTestCase, cls).tearDownClass()
        User.objects.all().delete()
        ContentReview.objects.all().delete()
        ReviewerRole.objects.all().delete()
        ResourceCriteria.objects.all().delete()
