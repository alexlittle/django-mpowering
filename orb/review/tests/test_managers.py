# -*- coding: utf-8 -*-

"""
Tests for orb.review managers and querysets
"""
from __future__ import unicode_literals

from datetime import date, timedelta

from django.test import TestCase
from freezegun import freeze_time

from orb.models import Resource, ResourceCriteria, ReviewerRole
from orb.resources.tests.factory import resource_factory
from orb.review.models import ContentReview
from orb.review.tests.base import ReviewTestCase


class ReviewQuerysetTests(ReviewTestCase):
    """

    There are three resources, two roles, and two users.

    medical::reviewer
    technical::staff_user


    - the first resource has two reviews, one accepted and one rejected
    - the second resource has two reviews, one accepted and one pending
    - the third reosurce has one pending review that is overdue

    """

    @classmethod
    def setUpClass(cls):
        super(ReviewQuerysetTests, cls).setUpClass()
        cls.resource_two = resource_factory(
            user=cls.nonreviewer,
            title="Second review",
            description="Básica salud del recién nacido",
        )
        cls.resource_three = resource_factory(
            user=cls.nonreviewer,
            title="Third réview",
            description="Básica salud del recién nacido",
        )

        ContentReview.objects.create(
            role=cls.medical_role,
            reviewer=cls.staff_user,
            resource=cls.resource,
            status=Resource.APPROVED,
        )
        ContentReview.objects.create(
            role=cls.technical_role,
            reviewer=cls.reviewer,
            resource=cls.resource,
            status=Resource.REJECTED,
        )

        ContentReview.objects.create(
            role=cls.medical_role,
            reviewer=cls.staff_user,
            resource=cls.resource_two,
            status=Resource.APPROVED,
        )
        ContentReview.objects.create(
            role=cls.technical_role,
            reviewer=cls.reviewer,
            resource=cls.resource_two,
            status=Resource.PENDING,
        )

        with freeze_time(date.today() - timedelta(days=15)):
            cls.overdue = ContentReview.objects.create(
                role=cls.technical_role,
                reviewer=cls.reviewer,
                resource=cls.resource_three,
                status=Resource.PENDING,
            )

    def test_pending_qs(self):
        """Returns only reviews that are pending"""
        self.assertEqual(
            ContentReview.reviews.pending().count(),
            2,
        )

    def test_complete_qs(self):
        """Returns only reviews that are approved or rejected"""
        self.assertEqual(
            ContentReview.reviews.complete().count(),
            3,
        )

    def test_overdue_qs(self):
        """Returns only reviews not updated in set time"""
        self.assertEqual(
            ContentReview.reviews.overdue().count(),
            1,
        )

    def test_for_user_qs(self):
        """Returns any reviews for user"""


class ReviewCriteriaQuerysetTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super(ReviewCriteriaQuerysetTests, cls).setUpClass()
        cls.role_a = ReviewerRole.objects.create(name="test A")
        cls.role_b = ReviewerRole.objects.create(name="test B")
        cls.resource_1 = ResourceCriteria.objects.create(description="a", role=cls.role_a)
        cls.resource_2 = ResourceCriteria.objects.create(description="b", role=cls.role_a)
        cls.resource_3 = ResourceCriteria.objects.create(description="c", role=cls.role_b)
        cls.resource_4 = ResourceCriteria.objects.create(description="d")

    @classmethod
    def tearDownClass(cls):
        super(ReviewCriteriaQuerysetTests, cls).tearDownClass()
        ReviewerRole.objects.all().delete()
        ResourceCriteria.objects.all().delete()

    def test_general_criteria(self):
        self.assertEqual(
            [self.resource_4],
            list(ResourceCriteria.criteria.general()),
        )

    def test_specified_criteria(self):
        self.assertEqual(
            [self.resource_1, self.resource_2, self.resource_4],
            list(ResourceCriteria.criteria.for_role(self.role_a)),
        )

    def test_for_roles(self):
        self.assertEqual(
            [self.resource_1, self.resource_2, self.resource_4],
            list(ResourceCriteria.criteria.for_roles(self.role_a)),
        )
