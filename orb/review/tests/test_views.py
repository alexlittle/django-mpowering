# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import mock
from django.core.exceptions import PermissionDenied
from django.urls import resolve, reverse
from django.http import Http404
from django.test import TestCase

from orb.models import UserProfile
from orb.review import views
from orb.review.models import ContentReview
from orb.review.tests.base import ReviewTestCase
from orb.tests.utils import mocked_model, request_factory


class ReviewListTests(ReviewTestCase):
    """
    Tests for the view showing pending reviews
    """

    def test_url(self):
        url = reverse("orb_pending_resources")
        resolution = resolve(url)
        self.assertEqual(resolution.func, views.resource_review_list)

    def test_anon_users_only(self):
        """Anon users should be redirected"""
        request = request_factory()
        response = views.resource_review_list(request)
        self.assertEqual(response.status_code, 302)

    def test_regular_users(self):
        """Non-reviewers should not be permitted"""
        mock_profile = mocked_model(UserProfile)
        mock_profile.is_reviewer = False
        request = request_factory(user=self.nonreviewer, userprofile=mock_profile)
        self.assertRaises(
            PermissionDenied,
            views.resource_review_list,
            request,
        )

    def test_reviewer_users(self):
        """Reviewer users should be able to see the page"""
        request = request_factory(user=self.reviewer)
        response = views.resource_review_list(request)
        self.assertEqual(response.status_code, 200)


class ReviewViewTests(ReviewTestCase):
    """
    Tests for the view showing an individual review/review form
    """
    @classmethod
    def setUpClass(cls):
        super(ReviewViewTests, cls).setUpClass()
        cls.review = ContentReview.objects.create(
            resource=cls.resource,
            reviewer=cls.reviewer,
            role=cls.medical_role,
        )

    def test_url(self):
        reverse("orb_resource_review",
                kwargs={'resource_id': 123, 'review_id': 123})

    def test_anonymous_user(self):
        """Anon users should not be permitted to view this"""
        request = request_factory()
        response = views.review_resource(request, 123, 123)
        self.assertEqual(response.status_code, 302)

    def test_missing_review(self):
        """A 404 should be raised for a reviewer if Resource is missing"""
        mock_profile = mocked_model(UserProfile)
        mock_profile.is_reviewer = True
        request = request_factory(user=self.reviewer, userprofile=mock_profile)
        self.assertRaises(
            Http404,
            views.review_resource,
            request,
            123,
            123,
        )

    def test_unassigned_content_reviewer(self):
        """An unassigned content review should not be able to access the view"""
        mock_profile = mocked_model(UserProfile)
        mock_profile.is_reviewer = True
        request = request_factory(user=self.nonreviewer, userprofile=mock_profile)
        self.assertRaises(
            PermissionDenied,
            views.review_resource,
            request,
            self.resource.pk,
            self.review.pk,
        )

    def test_assigned_content_review(self):
        """The assigned content review should be able to access the view"""
        mock_profile = mocked_model(UserProfile)
        mock_profile.is_reviewer = True
        request = request_factory(user=self.reviewer, userprofile=mock_profile)
        response = views.review_resource(request, self.resource.pk, self.review.pk)
        self.assertEqual(response.status_code, 200)


class RejectReviewTests(ReviewTestCase):
    """Tests for the reject_review view"""

    @classmethod
    def setUpClass(cls):
        super(RejectReviewTests, cls).setUpClass()
        cls.review = ContentReview.objects.create(
            resource=cls.resource,
            reviewer=cls.reviewer,
            role=cls.medical_role,
        )

    def test_url(self):
        reverse("orb_reject_resource",
                kwargs={'resource_id': 123, 'review_id': 123})

    def test_anonymous_user(self):
        """Anon users should not be permitted to view this"""
        request = request_factory()
        response = views.reject_resource(request, 123, 123)
        self.assertEqual(response.status_code, 302)

    def test_missing_review(self):
        """A 404 should be raised for a reviewer if Resource is missing"""
        mock_profile = mocked_model(UserProfile)
        mock_profile.is_reviewer = True
        request = request_factory(user=self.reviewer, userprofile=mock_profile)
        self.assertRaises(
            Http404,
            views.reject_resource,
            request,
            123,
            123,
        )

    def test_unassigned_content_reviewer(self):
        """An unassigned content review should not be able to access the view"""
        mock_profile = mocked_model(UserProfile)
        mock_profile.is_reviewer = True
        request = request_factory(user=self.nonreviewer, userprofile=mock_profile)
        self.assertRaises(
            PermissionDenied,
            views.reject_resource,
            request,
            self.resource.pk,
            self.review.pk,
        )

    def test_assigned_content_reviewer(self):
        """The assigned content review should be able to access the view"""
        mock_profile = mocked_model(UserProfile)
        mock_profile.is_reviewer = True
        request = request_factory(user=self.reviewer, userprofile=mock_profile)
        response = views.reject_resource(request, self.resource.pk, self.review.pk)
        self.assertEqual(response.status_code, 200)

    @mock.patch('orb.review.views.messages')
    def test_previously_rejected_content(self, messages):
        """Should redirect if content has already been rejected"""
        self.review.status = 'rejected'
        self.review.save()

        mock_profile = mocked_model(UserProfile)
        mock_profile.is_reviewer = True
        request = request_factory(user=self.reviewer, userprofile=mock_profile)
        response = views.reject_resource(request, self.resource.pk, self.review.pk)
        self.assertEqual(response.status_code, 302)


class CreateAssignmentTests(ReviewTestCase):

    def test_url(self):
        """Review assignment URL should be configured"""
        reverse("orb_assign_review", kwargs={'resource_id': 123})

    def test_anonymous_user(self):
        """Anon users should not be permitted to view this"""
        request = request_factory()
        response = views.assign_review(request, 123)
        self.assertEqual(response.status_code, 302)

    def test_staff_user(self):
        """A staff user should be allowed"""
        mock_profile = mocked_model(UserProfile)
        mock_profile.is_reviewer = False
        request = request_factory(user=self.staff_user, userprofile=mock_profile)
        response = views.assign_review(request, self.resource.pk)
        self.assertEqual(response.status_code, 200)

    def test_nonstaff_no_role(self):
        """A user w/o matching role should no be allowed to access"""

    def test_nonstaff_has_role(self):
        """A user with matching role should be allowed to access"""

    def test_missing_review(self):
        """A 404 should be raised for a staff user if Resource is missing"""
        mock_profile = mocked_model(UserProfile)
        mock_profile.is_reviewer = True
        request = request_factory(user=self.staff_user, userprofile=mock_profile)
        self.assertRaises(
            Http404,
            views.assign_review,
            request,
            12313,
        )

    def test_existing_assignment(self):
        """Assignment should fail if existing assignment for same role"""


class UpdateAssignmentTests(TestCase):

    def test_url(self):
        """Review assignment URL should be configured"""

    def test_anonymous_user(self):
        """Anon users should not be permitted to view this"""

    def test_staff_user(self):
        """A staff user should be allowed"""

    def test_missing_review(self):
        """A 404 should be raised for a staff user if Resource is missing"""

    def test_existing_assignment(self):
        """Assignment should fail if existing assignment for same role"""
