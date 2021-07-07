# -*- coding: utf-8 -*-

import unittest

import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from django.test import TestCase
from django.test.client import Client

from orb.models import Resource, ResourceTracker, Tag, TagOwner, TagTracker
from orb.tests.utils import login_client

FAST_TESTS = True


@pytest.mark.django_db
def test_advanced_search_view(client):
    response = client.get(reverse('orb_search_advanced_results') + "?q=tset")
    assert response.status_code == 200


class SiteTest(TestCase):
    fixtures = ['user.json', 'orb.json']

    def setUp(self):
        self.client = Client()

    def test_pages(self):
        url_names = [
            'orb_home', 'orb_about', 'orb_how_to', 'orb_partners',
            'orb_upload_instructions', 'orb_terms', 'orb_tag_cloud', 'orb_resource_create',
            'orb_guidelines', 'orb_search', 'orb_search_advanced', 'orb_opensearch',
        ]
        for url_name in url_names:
            self.assertEqual(self.client.get(reverse(url_name)).status_code, 200)

    def test_tags(self):

        tags = Tag.objects.all()
        if FAST_TESTS:
            tags = tags[:1]

        for t in tags:

            # Anon user (not logged in)
            tracker_count_start = TagTracker.objects.all().count()
            response = self.client.get(reverse('orb_tags', args=[t.slug]))
            self.assertEqual(response.status_code, 200)
            tracker_count_end = TagTracker.objects.all().count()
            self.assertEqual(tracker_count_start + 1, tracker_count_end)

            # Standard user
            with login_client(self, username='standarduser', password='password'):
                tracker_count_start = TagTracker.objects.all().count()
                response = self.client.get(reverse('orb_tags', args=[t.slug]))
                self.assertEqual(response.status_code, 200)
                tracker_count_end = TagTracker.objects.all().count()
                self.assertEqual(tracker_count_start + 1, tracker_count_end)

            # api user
            with login_client(self, username='apiuser', password='password'):
                tracker_count_start = TagTracker.objects.all().count()
                response = self.client.get(reverse('orb_tags', args=[t.slug]))
                self.assertEqual(response.status_code, 200)
                tracker_count_end = TagTracker.objects.all().count()
                self.assertEqual(tracker_count_start + 1, tracker_count_end)

            # superuser
            with login_client(self, username='superuser', password='password'):
                tracker_count_start = TagTracker.objects.all().count()
                response = self.client.get(reverse('orb_tags', args=[t.slug]))
                self.assertEqual(response.status_code, 200)
                tracker_count_end = TagTracker.objects.all().count()
                self.assertEqual(tracker_count_start + 1, tracker_count_end)

            # staffuser
            with login_client(self, username='staffuser', password='password'):
                tracker_count_start = TagTracker.objects.all().count()
                response = self.client.get(reverse('orb_tags', args=[t.slug]))
                self.assertEqual(response.status_code, 200)
                tracker_count_end = TagTracker.objects.all().count()
                self.assertEqual(tracker_count_start + 1, tracker_count_end)

            # orgowner
            with login_client(self, username='orgowner', password='password'):
                tracker_count_start = TagTracker.objects.all().count()
                response = self.client.get(reverse('orb_tags', args=[t.slug]))
                self.assertEqual(response.status_code, 200)
                tracker_count_end = TagTracker.objects.all().count()
                self.assertEqual(tracker_count_start + 1, tracker_count_end)

    def test_resources_approved(self):

        approved_resources = Resource.objects.filter(status=Resource.APPROVED)
        if FAST_TESTS:
            approved_resources = approved_resources[:1]

        for r in approved_resources:

            # Anon user (not logged in)
            tracker_count_start = ResourceTracker.objects.all().count()
            response = self.client.get(reverse('orb_resource', args=[r.slug]))
            self.assertEqual(response.status_code, 200)
            tracker_count_end = ResourceTracker.objects.all().count()
            self.assertEqual(tracker_count_start + 1, tracker_count_end)

            tracker_count_start = ResourceTracker.objects.all().count()
            response = self.client.get(
                reverse('orb_resource_permalink', args=[r.id]))
            self.assertEqual(response.status_code, 200)
            tracker_count_end = ResourceTracker.objects.all().count()
            self.assertEqual(tracker_count_start + 1, tracker_count_end)

            # Standard user
            with login_client(self, username='standarduser', password='password'):
                tracker_count_start = ResourceTracker.objects.all().count()
                response = self.client.get(reverse('orb_resource', args=[r.slug]))
                self.assertEqual(response.status_code, 200)
                tracker_count_end = ResourceTracker.objects.all().count()
                self.assertEqual(tracker_count_start + 1, tracker_count_end)

                tracker_count_start = ResourceTracker.objects.all().count()
                response = self.client.get(
                    reverse('orb_resource_permalink', args=[r.id]))
                self.assertEqual(response.status_code, 200)
                tracker_count_end = ResourceTracker.objects.all().count()
                self.assertEqual(tracker_count_start + 1, tracker_count_end)

            # api user
            with login_client(self, username='apiuser', password='password'):
                tracker_count_start = ResourceTracker.objects.all().count()
                response = self.client.get(reverse('orb_resource', args=[r.slug]))
                self.assertEqual(response.status_code, 200)
                tracker_count_end = ResourceTracker.objects.all().count()
                self.assertEqual(tracker_count_start + 1, tracker_count_end)

                tracker_count_start = ResourceTracker.objects.all().count()
                response = self.client.get(
                    reverse('orb_resource_permalink', args=[r.id]))
                self.assertEqual(response.status_code, 200)
                tracker_count_end = ResourceTracker.objects.all().count()
                self.assertEqual(tracker_count_start + 1, tracker_count_end)

            # superuser
            with login_client(self, username='superuser', password='password'):
                tracker_count_start = ResourceTracker.objects.all().count()
                response = self.client.get(reverse('orb_resource', args=[r.slug]))
                self.assertEqual(response.status_code, 200)
                tracker_count_end = ResourceTracker.objects.all().count()
                self.assertEqual(tracker_count_start + 1, tracker_count_end)

                tracker_count_start = ResourceTracker.objects.all().count()
                response = self.client.get(
                    reverse('orb_resource_permalink', args=[r.id]))
                self.assertEqual(response.status_code, 200)
                tracker_count_end = ResourceTracker.objects.all().count()
                self.assertEqual(tracker_count_start + 1, tracker_count_end)

            # staffuser
            with login_client(self, username='staffuser', password='password'):
                tracker_count_start = ResourceTracker.objects.all().count()
                response = self.client.get(reverse('orb_resource', args=[r.slug]))
                self.assertEqual(response.status_code, 200)
                tracker_count_end = ResourceTracker.objects.all().count()
                self.assertEqual(tracker_count_start + 1, tracker_count_end)

                tracker_count_start = ResourceTracker.objects.all().count()
                response = self.client.get(
                    reverse('orb_resource_permalink', args=[r.id]))
                self.assertEqual(response.status_code, 200)
                tracker_count_end = ResourceTracker.objects.all().count()
                self.assertEqual(tracker_count_start + 1, tracker_count_end)

            # orgowner
            with login_client(self, username='orgowner', password='password'):
                tracker_count_start = ResourceTracker.objects.all().count()
                response = self.client.get(reverse('orb_resource', args=[r.slug]))
                self.assertEqual(response.status_code, 200)
                tracker_count_end = ResourceTracker.objects.all().count()
                self.assertEqual(tracker_count_start + 1, tracker_count_end)

                tracker_count_start = ResourceTracker.objects.all().count()
                response = self.client.get(
                    reverse('orb_resource_permalink', args=[r.id]))
                self.assertEqual(response.status_code, 200)
                tracker_count_end = ResourceTracker.objects.all().count()
                self.assertEqual(tracker_count_start + 1, tracker_count_end)

    def test_resources_pending(self):
        pending_resources = Resource.objects.filter(status=Resource.PENDING)

        if FAST_TESTS:
            pending_resources = pending_resources[:1]

        for r in pending_resources:

            # Anon user (not logged in)
            tracker_count_start = ResourceTracker.objects.all().count()
            response = self.client.get(reverse('orb_resource', args=[r.slug]))
            self.assertEqual(response.status_code, 404)
            tracker_count_end = ResourceTracker.objects.all().count()
            self.assertEqual(tracker_count_start, tracker_count_end)

            tracker_count_start = ResourceTracker.objects.all().count()
            response = self.client.get(
                reverse('orb_resource_permalink', args=[r.id]))
            self.assertEqual(response.status_code, 404)
            tracker_count_end = ResourceTracker.objects.all().count()
            self.assertEqual(tracker_count_start, tracker_count_end)

            # Standard user
            with login_client(self, username='standarduser', password='password'):
                self.user = User.objects.get(username='standarduser')
                tracker_count_start = ResourceTracker.objects.all().count()
                response = self.client.get(reverse('orb_resource', args=[r.slug]))
                if r.create_user == self.user or r.update_user == self.user:
                    self.assertEqual(response.status_code, 200)
                    tracker_count_end = ResourceTracker.objects.all().count()
                    self.assertEqual(tracker_count_start + 1, tracker_count_end)
                else:
                    self.assertEqual(response.status_code, 404)
                    tracker_count_end = ResourceTracker.objects.all().count()
                    self.assertEqual(tracker_count_start, tracker_count_end)

                tracker_count_start = ResourceTracker.objects.all().count()
                response = self.client.get(
                    reverse('orb_resource_permalink', args=[r.id]))
                if r.create_user == self.user or r.update_user == self.user:
                    self.assertEqual(response.status_code, 200)
                    tracker_count_end = ResourceTracker.objects.all().count()
                    self.assertEqual(tracker_count_start + 1, tracker_count_end)
                else:
                    self.assertEqual(response.status_code, 404)
                    tracker_count_end = ResourceTracker.objects.all().count()
                    self.assertEqual(tracker_count_start, tracker_count_end)

            # api user
            with login_client(self, username='apiuser', password='password'):
                self.user = User.objects.get(username='apiuser')
                tracker_count_start = ResourceTracker.objects.all().count()
                response = self.client.get(reverse('orb_resource', args=[r.slug]))
                if r.create_user == self.user or r.update_user == self.user:
                    self.assertEqual(response.status_code, 200)
                    tracker_count_end = ResourceTracker.objects.all().count()
                    self.assertEqual(tracker_count_start + 1, tracker_count_end)
                else:
                    self.assertEqual(response.status_code, 404)
                    tracker_count_end = ResourceTracker.objects.all().count()
                    self.assertEqual(tracker_count_start, tracker_count_end)

                tracker_count_start = ResourceTracker.objects.all().count()
                response = self.client.get(
                    reverse('orb_resource_permalink', args=[r.id]))
                if r.create_user == self.user or r.update_user == self.user:
                    self.assertEqual(response.status_code, 200)
                    tracker_count_end = ResourceTracker.objects.all().count()
                    self.assertEqual(tracker_count_start + 1, tracker_count_end)
                else:
                    self.assertEqual(response.status_code, 404)
                    tracker_count_end = ResourceTracker.objects.all().count()
                    self.assertEqual(tracker_count_start, tracker_count_end)

            # superuser
            with login_client(self, username='superuser', password='password'):
                tracker_count_start = ResourceTracker.objects.all().count()
                response = self.client.get(reverse('orb_resource', args=[r.slug]))
                self.assertEqual(response.status_code, 200)
                tracker_count_end = ResourceTracker.objects.all().count()
                self.assertEqual(tracker_count_start + 1, tracker_count_end)

                tracker_count_start = ResourceTracker.objects.all().count()
                response = self.client.get(
                    reverse('orb_resource_permalink', args=[r.id]))
                self.assertEqual(response.status_code, 200)
                tracker_count_end = ResourceTracker.objects.all().count()
                self.assertEqual(tracker_count_start + 1, tracker_count_end)

            # staffuser
            with login_client(self, username='staffuser', password='password'):
                tracker_count_start = ResourceTracker.objects.all().count()
                response = self.client.get(reverse('orb_resource', args=[r.slug]))
                self.assertEqual(response.status_code, 200)
                tracker_count_end = ResourceTracker.objects.all().count()
                self.assertEqual(tracker_count_start + 1, tracker_count_end)

                tracker_count_start = ResourceTracker.objects.all().count()
                response = self.client.get(
                    reverse('orb_resource_permalink', args=[r.id]))
                self.assertEqual(response.status_code, 200)
                tracker_count_end = ResourceTracker.objects.all().count()
                self.assertEqual(tracker_count_start + 1, tracker_count_end)

            # orgowner
            with login_client(self, username='orgowner', password='password'):
                self.user = User.objects.get(username='orgowner')
                tracker_count_start = ResourceTracker.objects.all().count()
                response = self.client.get(reverse('orb_resource', args=[r.slug]))
                if r.create_user == self.user or r.update_user == self.user:
                    self.assertEqual(response.status_code, 200)
                    tracker_count_end = ResourceTracker.objects.all().count()
                    self.assertEqual(tracker_count_start + 1, tracker_count_end)
                else:
                    self.assertEqual(response.status_code, 404)
                    tracker_count_end = ResourceTracker.objects.all().count()
                    self.assertEqual(tracker_count_start, tracker_count_end)

                tracker_count_start = ResourceTracker.objects.all().count()
                response = self.client.get(
                    reverse('orb_resource_permalink', args=[r.id]))
                if r.create_user == self.user or r.update_user == self.user:
                    self.assertEqual(response.status_code, 200)
                    tracker_count_end = ResourceTracker.objects.all().count()
                    self.assertEqual(tracker_count_start + 1, tracker_count_end)
                else:
                    self.assertEqual(response.status_code, 404)
                    tracker_count_end = ResourceTracker.objects.all().count()
                    self.assertEqual(tracker_count_start, tracker_count_end)

    def test_resources_rejected(self):

        rejected_resources = Resource.objects.filter(status=Resource.REJECTED)

        if FAST_TESTS:
            rejected_resources = rejected_resources[:1]

        for r in rejected_resources:

            # Anon user (not logged in)
            response = self.client.get(reverse('orb_resource', args=[r.slug]))
            self.assertEqual(response.status_code, 404)

            response = self.client.get(
                reverse('orb_resource_permalink', args=[r.id]))
            self.assertEqual(response.status_code, 404)

            # Standard user
            with login_client(self, username='standarduser', password='password'):
                self.user = User.objects.get(username='standarduser')
                response = self.client.get(reverse('orb_resource', args=[r.slug]))
                if r.create_user == self.user or r.update_user == self.user:
                    self.assertEqual(response.status_code, 200)
                else:
                    self.assertEqual(response.status_code, 404)

                response = self.client.get(
                    reverse('orb_resource_permalink', args=[r.id]))
                if r.create_user == self.user or r.update_user == self.user:
                    self.assertEqual(response.status_code, 200)
                else:
                    self.assertEqual(response.status_code, 404)

            # api user
            with login_client(self, username='apiuser', password='password'):
                self.user = User.objects.get(username='apiuser')
                response = self.client.get(reverse('orb_resource', args=[r.slug]))
                if r.create_user == self.user or r.update_user == self.user:
                    self.assertEqual(response.status_code, 200)
                else:
                    self.assertEqual(response.status_code, 404)

                response = self.client.get(
                    reverse('orb_resource_permalink', args=[r.id]))
                if r.create_user == self.user or r.update_user == self.user:
                    self.assertEqual(response.status_code, 200)
                else:
                    self.assertEqual(response.status_code, 404)

            # superuser
            with login_client(self, username='superuser', password='password'):
                response = self.client.get(reverse('orb_resource', args=[r.slug]))
                self.assertEqual(response.status_code, 200)

                response = self.client.get(
                    reverse('orb_resource_permalink', args=[r.id]))
                self.assertEqual(response.status_code, 200)

            # staffuser
            with login_client(self, username='staffuser', password='password'):
                response = self.client.get(reverse('orb_resource', args=[r.slug]))
                self.assertEqual(response.status_code, 200)

                response = self.client.get(
                    reverse('orb_resource_permalink', args=[r.id]))
                self.assertEqual(response.status_code, 200)

            # orgowner
            with login_client(self, username='orgowner', password='password'):
                self.user = User.objects.get(username='orgowner')
                response = self.client.get(reverse('orb_resource', args=[r.slug]))
                if r.create_user == self.user or r.update_user == self.user:
                    self.assertEqual(response.status_code, 200)
                else:
                    self.assertEqual(response.status_code, 404)

                response = self.client.get(
                    reverse('orb_resource_permalink', args=[r.id]))
                if r.create_user == self.user or r.update_user == self.user:
                    self.assertEqual(response.status_code, 200)
                else:
                    self.assertEqual(response.status_code, 404)

        def test_tag_link(self):
            tag_links = Tag.objects.all().exclude(external_url=None).exclude(external_url='')


class AnalyticsPageTest(TestCase):
    fixtures = ['user.json', 'orb.json']

    def test_anon_analytics_home(self):
        """User should be redirected to login page"""
        response = self.client.get(reverse('orb_analytics_home'))
        self.assertEqual(response.status_code, 302)

    @unittest.skip("deprecated")
    def test_anon_analytics_map(self):
        response = self.client.get(reverse('orb_analytics_map'))
        self.assertEqual(response.status_code, 302)

    @login_client(username='standarduser', password='password')
    def test_standard_user_analytics_home(self):
        response = self.client.get(reverse('orb_analytics_home'))
        self.assertEqual(response.status_code, 403)

    @unittest.skip("deprecated")
    @login_client(username='standarduser', password='password')
    def test_standard_user_analytics_map(self):
        response = self.client.get(reverse('orb_analytics_map'))
        self.assertEqual(response.status_code, 403)

    @login_client(username='apiuser', password='password')
    def test_api_user_analytics_home(self):
        response = self.client.get(reverse('orb_analytics_home'))
        self.assertEqual(response.status_code, 403)

    @unittest.skip("deprecated")
    @login_client(username='apiuser', password='password')
    def test_api_user_analytics_map(self):
        response = self.client.get(reverse('orb_analytics_map'))
        self.assertEqual(response.status_code, 403)

    @login_client(username='superuser', password='password')
    def test_superuser_analytics_home(self):
        response = self.client.get(reverse('orb_analytics_home'))
        self.assertEqual(response.status_code, 200)

    @unittest.skip("deprecated")
    @login_client(username='superuser', password='password')
    def test_superuser_analytics_map(self):
        response = self.client.get(reverse('orb_analytics_map'))
        self.assertEqual(response.status_code, 200)

    @login_client(username='staffuser', password='password')
    def test_staff_user_analytics_home(self):
        response = self.client.get(reverse('orb_analytics_home'))
        self.assertEqual(response.status_code, 200)

    @unittest.skip("deprecated")
    @login_client(username='staffuser', password='password')
    def test_staff_user_analytics_map(self):
        response = self.client.get(reverse('orb_analytics_map'))
        self.assertEqual(response.status_code, 200)

    def test_org_owner_analytics_home(self):
        self.client.login(username='orgowner', password='password')
        response = self.client.get(reverse('orb_analytics_home'))
        self.assertEqual(response.status_code, 403)
        self.client.logout()

    @unittest.skip("deprecated")
    @login_client(username='orgowner', password='password')
    def test_org_owner_analytics_map(self):
        response = self.client.get(reverse('orb_analytics_map'))
        self.assertEqual(response.status_code, 403)

    def test_tags(self):

        tags = Tag.objects.all()
        if FAST_TESTS:
            tags = tags[:1]

        for t in tags:
            # for anon user
            response = self.client.get(
                reverse('orb_analytics_tag', args=[t.id]))
            self.assertEqual(response.status_code, 401)

            # Standard user
            self.client.login(username='standarduser', password='password')
            response = self.client.get(
                reverse('orb_analytics_tag', args=[t.id]))
            self.assertEqual(response.status_code, 401)
            self.client.logout()

            # api user
            self.client.login(username='apiuser', password='password')
            response = self.client.get(
                reverse('orb_analytics_tag', args=[t.id]))
            self.assertEqual(response.status_code, 401)
            self.client.logout()

            # superuser
            self.client.login(username='superuser', password='password')
            response = self.client.get(
                reverse('orb_analytics_tag', args=[t.id]))
            self.assertEqual(response.status_code, 200)
            self.client.logout()

            # staffuser
            self.client.login(username='staffuser', password='password')
            response = self.client.get(
                reverse('orb_analytics_tag', args=[t.id]))
            self.assertEqual(response.status_code, 200)
            self.client.logout()

            # orgowner
            self.client.login(username='orgowner', password='password')
            self.user = User.objects.get(username='orgowner')
            tag_owner = TagOwner.objects.filter(tag=t, user=self.user).count()
            response = self.client.get(
                reverse('orb_analytics_tag', args=[t.id]))
            if tag_owner > 0:
                self.assertEqual(response.status_code, 200)
            else:
                self.assertEqual(response.status_code, 401)
            self.client.logout()
