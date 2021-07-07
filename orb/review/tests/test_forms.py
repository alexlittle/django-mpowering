# -*- coding: utf-8 -*-

"""
Tests for ORB resource forms
"""
from __future__ import unicode_literals

from django.contrib.auth import get_user_model
from django.test import TestCase

from orb.models import Resource, ResourceCriteria, ReviewerRole, UserProfile
from orb.resources.tests.factory import resource_factory
from orb.review.forms import AssignmentForm, ContentReviewForm, ReviewStartForm, StaffReviewForm
from orb.review.models import ContentReview

from .base import ReviewTestCase


class ReviewFormTests(ReviewTestCase):
    """
    Tests for the reviewer's review entry form
    """

    @classmethod
    def setUpClass(cls):
        """
        cls.staff_user - medical
        cls.reviewer - technical

        """
        super(ReviewFormTests, cls).setUpClass()
        cls.criteria_1 = ResourceCriteria.objects.create(description="A", role=cls.medical_role)
        cls.criteria_2 = ResourceCriteria.objects.create(description="B", role=cls.medical_role)
        cls.criteria_3 = ResourceCriteria.objects.create(description="C", role=cls.technical_role)
        cls.criteria_4 = ResourceCriteria.objects.create(description="D", role=cls.technical_role)
        cls.criteria_5 = ResourceCriteria.objects.create(description="E")
        cls.criteria_6 = ResourceCriteria.objects.create(description="F")

    @classmethod
    def tearDownClass(cls):
        super(ReviewFormTests, cls).tearDownClass()

    def test_displayed_criteria(self):
        """Criteria should be based on user role"""
        form = ContentReviewForm(user=self.staff_user)
        self.assertEqual(
            list(form.fields['criteria'].queryset),
            [self.criteria_1, self.criteria_2, self.criteria_5, self.criteria_6],
        )

    def test_reject_without_reason(self):
        """Form should require reason if resource rejected"""
        form = ContentReviewForm(data={'approved': False}, user=self.staff_user)
        self.assertFalse(form.is_valid())

        form = ContentReviewForm(data={'approved': False, 'notes': ''}, user=self.staff_user)
        self.assertFalse(form.is_valid())

    def test_reject_with_reason(self):
        """Form should require reason if resource rejected"""
        form = ContentReviewForm(data={'approved': False, 'notes': 'Bad content!'}, user=self.staff_user)
        self.assertTrue(form.is_valid())

    def test_reject_with_all_criteria(self):
        """It should be possible to reject with all criteria selected"""
        form = ContentReviewForm(data={
            'approved': False,
            'notes': 'Bad content!',
            'criteria': [self.criteria_1.pk, self.criteria_2.pk, self.criteria_5.pk, self.criteria_6.pk],
        }, user=self.staff_user)
        self.assertTrue(form.is_valid())

    def test_approve_with_all_criteria(self):
        """Approval should be valid if all criteria are selected"""
        form = ContentReviewForm(data={
            'approved': True,
            'criteria': [
                c.pk for c in
                ResourceCriteria.criteria.for_roles(*self.staff_user.userprofile.reviewer_roles.all())
            ]
        }, user=self.staff_user)
        form.is_valid()
        self.assertTrue(form.is_valid())

    def test_approve_missing_criteria(self):
        """Approval should not be valid if not all criteria are selected"""
        form = ContentReviewForm(data={
            'approved': True,
            'criteria': [self.criteria_2.pk, self.criteria_5.pk, self.criteria_6.pk],
        }, user=self.staff_user)
        self.assertFalse(form.is_valid())


class AssignmentFormTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super(AssignmentFormTests, cls).setUpClass()

        cls.user_one, _ = get_user_model().objects.get_or_create(username="one")
        cls.user_two, _ = get_user_model().objects.get_or_create(username="two")
        cls.user_three, _ = get_user_model().objects.get_or_create(username="three")
        cls.user_four, _ = get_user_model().objects.get_or_create(username="four")

        cls.medical_role, _ = ReviewerRole.objects.get_or_create(name='medical')
        cls.technical_role, _ = ReviewerRole.objects.get_or_create(name='technical')

        cls.profile_one, _ = UserProfile.objects.get_or_create(user=cls.user_one)
        cls.profile_one.reviewer_roles.add(cls.medical_role)

        cls.profile_two, _ = UserProfile.objects.get_or_create(user=cls.user_two)
        cls.profile_two.reviewer_roles.add(cls.technical_role)

        cls.profile_three, _ = UserProfile.objects.get_or_create(user=cls.user_three)
        cls.profile_three.reviewer_roles.add(cls.technical_role)

        cls.resource = resource_factory(
            user=cls.user_four,
            title="Básica salud del recién nacido",
            description="Básica salud del recién nacido",
        )

    @classmethod
    def tearDownClass(cls):
        super(AssignmentFormTests, cls).tearDownClass()
        get_user_model().objects.all().delete()
        ReviewerRole.objects.all().delete()
        ContentReview.objects.all().delete()

    def test_field_count(self):
        """If no assignments, should have no initial values"""
        form = AssignmentForm(resource=self.resource)
        self.assertEqual(2, len(form.fields))

    def test_initial_values(self):
        """If no assignments, should have no initial values"""
        form = AssignmentForm(resource=self.resource)
        for value in form.initial.values():
            self.assertEqual(value, None)

    def test_has_assignments(self):
        """If assignments, should have initial values"""
        review = ContentReview.reviews.create(
            resource=self.resource,
            reviewer=self.user_one,
            role=self.medical_role,
        )

        form = AssignmentForm(resource=self.resource)
        self.assertEqual(
            {"technical": None, "medical": self.profile_one},
            form.initial,
        )
        ContentReview.reviews.all().delete()

    def test_review_completed(self):
        """Field should not be changable if review completed"""
        ContentReview.reviews.create(
            resource=self.resource,
            reviewer=self.user_two,
            role=self.technical_role,
            status=Resource.APPROVED,
        )

        form = AssignmentForm(resource=self.resource, data={
            'technical': self.profile_three.pk,
        })
        self.assertFalse(form.is_valid())
        ContentReview.reviews.all().delete()

    def test_save_reviews(self):
        """Save should create new assignments"""
        count = ContentReview.reviews.all().count()
        form = AssignmentForm(resource=self.resource, data={
            'medical': self.profile_one.pk,
        })
        self.assertTrue(form.is_valid())
        form.save()
        self.assertEqual(count + 1, ContentReview.reviews.all().count())
        ContentReview.reviews.all().delete()


class StartFormTests(ReviewTestCase):
    """
    The ReviewStartForm takes a resource, a user, and then validates
    that the role selected belongs to the user and that it is
    available for a reivew.
    """
    def test_non_reviewer(self):
        form = ReviewStartForm(data={
            'role': self.technical_role.pk,
        }, resource=self.resource, reviewer=self.nonreviewer)
        self.assertFalse(form.is_valid())

    def test_reviewer_wrong_role(self):
        form = ReviewStartForm(data={
            'role': self.technical_role.pk,
        }, resource=self.resource, reviewer=self.staff_user)
        self.assertFalse(form.is_valid())

    def test_reviewer_matching_role(self):
        form = ReviewStartForm(data={
            'role': self.technical_role.pk,
        }, resource=self.resource, reviewer=self.reviewer)
        self.assertTrue(form.is_valid())

    def test_existing_assignment(self):
        ContentReview.objects.create(
            reviewer=self.reviewer,
            resource=self.resource,
            role=self.technical_role,
        )
        form = ReviewStartForm(data={
            'role': self.technical_role.pk,
        }, resource=self.resource, reviewer=self.reviewer)
        self.assertFalse(form.is_valid())

    def test_create_additional_review(self):
        """If"""
        ContentReview.objects.create(
            reviewer=self.staff_user,
            resource=self.resource,
            role=self.medical_role,
        )
        form = ReviewStartForm(data={
            'role': self.technical_role.pk,
        }, resource=self.resource, reviewer=self.reviewer)
        self.assertTrue(form.is_valid())

    def test_create_content_review(self):
        form = ReviewStartForm(data={
            'role': self.medical_role.pk,
        }, resource=self.resource, reviewer=self.staff_user)
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save())


class StaffReviewFormTests(ReviewTestCase):

    def test_rejection_no_notes(self):
        form = StaffReviewForm(data={
            'approved': False,
        }, resource=self.resource, user=self.staff_user)
        self.assertFalse(form.is_valid())
