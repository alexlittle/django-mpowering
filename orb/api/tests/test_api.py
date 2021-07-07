"""
API Resource specific tests for the COVID-19 Library API
"""
from __future__ import unicode_literals

import uuid

import pytest
from django.contrib.auth.models import User
from tastypie.models import ApiKey

from orb.models import SearchTracker
from orb.tests import ResourceTestCase
from orb.tests.utils import login_client


class ApiTestFixture(object):

    @classmethod
    def setUpClass(cls):

        super(ApiTestFixture, cls).setUpClass()

        standard_user = User.objects.get(username='standarduser')
        api_key, _ = ApiKey.objects.get_or_create(user=standard_user, defaults={"key": str(uuid.uuid4())})

        cls.standard_user = {
            'username': standard_user.username,
            'api_key': api_key.key,
        }

        api_user = User.objects.get(username='apiuser')
        api_key, _ = ApiKey.objects.get_or_create(user=api_user, defaults={"key": str(uuid.uuid4())})
        cls.api_user = {
            'username': api_user.username,
            'api_key': api_key.key,
        }

        super_user = User.objects.get(username='superuser')
        api_key, _ = ApiKey.objects.get_or_create(user=super_user, defaults={"key": str(uuid.uuid4())})
        cls.super_user = {
            'username': super_user.username,
            'api_key': api_key.key,
        }

        staff_user = User.objects.get(username='staffuser')
        api_key, _ = ApiKey.objects.get_or_create(user=staff_user, defaults={"key": str(uuid.uuid4())})
        cls.staff_user = {
            'username': staff_user.username,
            'api_key': api_key.key,
        }

        orgowner_user = User.objects.get(username='orgowner')
        api_key, _ = ApiKey.objects.get_or_create(user=orgowner_user, defaults={"key": str(uuid.uuid4())})
        cls.orgowner_user = {
            'username': orgowner_user.username,
            'api_key': api_key.key,
        }

        cls.user_set = [cls.api_user, cls.standard_user,
                        cls.super_user, cls.staff_user, cls.orgowner_user]


class SearchResourceTest(ApiTestFixture, ResourceTestCase):
    fixtures = ['user.json', 'orb.json']

    def setUp(self):
        super(SearchResourceTest, self).setUp()
        self.url = '/api/v1/resource/search/'

    # check post not allowed
    def test_post_invalid(self):
        self.assertHttpMethodNotAllowed(
            self.api_client.post(self.url, format='json', data={}))

    # check unauthorized
    def test_unauthorized(self):
        data = {
            'username': 'user',
            'api_key': '1234',
        }
        self.assertHttpUnauthorized(self.api_client.get(
            self.url, format='json', data=data))

    def test_session_authorized(self):
        with login_client(self, username='standarduser', password='password'):
            data = {'q': 'medical'}
            tracker_count_start = SearchTracker.objects.all().count()
            resp = self.client.get(self.url, format='json', data=data)
            self.assertHttpOK(resp)
            self.assertValidJSON(resp.content)
            tracker_count_end = SearchTracker.objects.all().count()
            self.assertEqual(tracker_count_start + 1, tracker_count_end)

    def test_authorized(self):
        for u in self.user_set:
            data = u
            data['q'] = 'medical'
            tracker_count_start = SearchTracker.objects.all().count()
            resp = self.api_client.get(self.url, format='json', data=data)
            self.assertHttpOK(resp)
            self.assertValidJSON(resp.content)
            tracker_count_end = SearchTracker.objects.all().count()
            self.assertEqual(tracker_count_start + 1, tracker_count_end)

    @pytest.mark.skip(reason="Requires Solr setup which is highly desirable but an unnecessary blocker")
    @pytest.mark.solr
    def test_search_results(self):
        for u in self.user_set:
            data = u
            data['q'] = 'medical'
            tracker_count_start = SearchTracker.objects.all().count()
            resp = self.api_client.get(self.url, format='json', data=data)
            self.assertHttpOK(resp)
            self.assertValidJSON(resp.content)
            self.assertEqual(len(self.deserialize(resp)['objects']), 1)
            tracker_count_end = SearchTracker.objects.all().count()
            self.assertEqual(tracker_count_start + 1, tracker_count_end)



class ResourceResourceTest(ApiTestFixture, ResourceTestCase):
    fixtures = ['user.json', 'orb.json']

    def setUp(self):
        super(ResourceResourceTest, self).setUp()
        self.url = '/api/v1/resource/'

    # check get allowed for valid user
    def test_get_valid(self):
        for u in self.user_set:
            resp = self.api_client.get(self.url, format='json', data=u)
            self.assertHttpOK(resp)
            self.assertValidJSON(resp.content)

    def test_get_not_valid(self):
        self.assertHttpUnauthorized(
            self.api_client.get(self.url, format='json', data={}))

    # check post not allowed for invalid user
    def test_post_invalid(self):
        for u in [self.standard_user, self.super_user, self.staff_user, self.orgowner_user]:
            resp = self.api_client.post(self.url, format='json', data=u)
            self.assertHttpUnauthorized(resp)

    # check put not allowed
    def test_put_invalid(self):
        for u in [self.standard_user, self.super_user, self.staff_user, self.orgowner_user]:
            resp = self.api_client.put(self.url, format='json', data=u)
            self.assertHttpUnauthorized(resp)

    # check delete not allowed
    def test_delete_invalid(self):
        for u in self.user_set:
            resp = self.api_client.delete(self.url, format='json', data=u)
            self.assertHttpMethodNotAllowed(resp)

    def test_get_approved_resource(self):
        approved_resource_url = self.url + str(5) + "/"
        for u in self.user_set:
            resp = self.api_client.get(
                approved_resource_url, format='json', data=u)
            self.assertHttpOK(resp)
            self.assertValidJSON(resp.content)
            self.assertEqual(len(self.deserialize(resp)['tags']), 11)

    def test_get_unapproved_resource(self):
        unapproved_resource_url = self.url + str(125) + "/"
        user_assertions = [(self.api_user, 404),
                    (self.standard_user, 404),
                    (self.super_user, 200),
                    (self.staff_user, 200),
                    (self.orgowner_user, 404)]

        for user_assertion in user_assertions:
            resp = self.api_client.get(
                unapproved_resource_url, format='json', data=user_assertion[0])
            self.assertEqual(resp.status_code, user_assertion[1])
            if resp.status_code < 400:
                self.assertValidJSON(resp.content)

    def test_get_unknown_resource(self):
        unknown_resource_url = self.url + str(12345) + "/"
        for u in self.user_set:
            resp = self.api_client.get(
                unknown_resource_url, format='json', data=u)
            self.assertHttpNotFound(resp)

    def test_post_resource(self):
        resource = {
            'title': "my new title",
            'description': "<p>some description or other here</p>",
            'study_time_number': 15,
            'study_time_unit': 'days'
        }
        auth = self.create_apikey(
            self.api_user['username'], self.api_user['api_key'])
        resp = self.api_client.post(
            self.url, format='json', data=resource, authentication=auth)
        self.assertHttpCreated(resp)
        self.assertValidJSON(resp.content)

        # try posting the same resource again and should get 400 message and a
        # pk of the original object
        resp = self.api_client.post(
            self.url, format='json', data=resource, authentication=auth)
        self.assertHttpBadRequest(resp)
        self.deserialize(resp)

    def test_change_status(self):
        resource = {
            'title': "my new title",
            'description': "<p>some description or other here</p>",
            'study_time_number': 15,
            'study_time_unit': 'days',
            'status': 'approved'
        }
        auth = self.create_apikey(
            self.api_user['username'], self.api_user['api_key'])
        resp = self.api_client.post(
            self.url, format='json', data=resource, authentication=auth)
        self.assertHttpCreated(resp)
        self.assertValidJSON(resp.content)
        self.assertEqual(self.deserialize(resp)['status'], 'pending')


# Tag API
class TagResourceTest(ApiTestFixture, ResourceTestCase):
    fixtures = ['user.json', 'orb.json']

    def setUp(self):
        super(TagResourceTest, self).setUp()
        self.url = '/api/v1/tag/'

    # check get allowed for valid user
    def test_get_valid(self):
        for u in self.user_set:
            resp = self.api_client.get(self.url, format='json', data=u)
            self.assertHttpOK(resp)
            self.assertValidJSON(resp.content)

    def test_get_not_valid(self):
        self.assertHttpUnauthorized(
            self.api_client.get(self.url, format='json', data={}))

    # check post not allowed for invalid user
    def test_post_invalid(self):
        for u in [self.standard_user, self.super_user, self.staff_user, self.orgowner_user]:
            resp = self.api_client.post(self.url, format='json', data=u)
            self.assertHttpUnauthorized(resp)

    # check put not allowed
    def test_put_invalid(self):
        for u in self.user_set:
            resp = self.api_client.put(self.url, format='json', data=u)
            self.assertHttpMethodNotAllowed(resp)

    # check delete not allowed
    def test_delete_invalid(self):
        for u in self.user_set:
            resp = self.api_client.delete(self.url, format='json', data=u)
            self.assertHttpMethodNotAllowed(resp)

    def test_get_existing_tag(self):
        for u in self.user_set:
            data = u
            data['name'] = "Digital Campus"
            resp = self.api_client.get(self.url, format='json', data=data)
            self.assertHttpOK(resp)
            self.assertValidJSON(resp.content)
            self.assertEqual(len(self.deserialize(resp)['objects']), 1)

    def test_get_unknown_tag(self):
        for u in self.user_set:
            data = u
            data['name'] = "Some other tag"
            resp = self.api_client.get(self.url, format='json', data=data)
            self.assertHttpOK(resp)
            self.assertValidJSON(resp.content)
            self.assertEqual(len(self.deserialize(resp)['objects']), 0)

    def test_post_empty_tag(self):
        data = {}
        data['name'] = ''
        auth = self.create_apikey(
            self.api_user['username'], self.api_user['api_key'])
        resp = self.api_client.post(
            self.url, format='json', data=data, authentication=auth)
        self.assertHttpBadRequest(resp)

        for u in [self.standard_user, self.super_user, self.staff_user, self.orgowner_user]:
            data = {}
            data['name'] = ''
            auth = self.create_apikey(u['username'], u['api_key'])
            resp = self.api_client.post(
                self.url, format='json', data=data, authentication=auth)
            self.assertHttpBadRequest(resp)

    def test_post_tag(self):
        data = {}
        data['name'] = 'my new tag'

        auth = self.create_apikey(
            self.api_user['username'], self.api_user['api_key'])
        resp = self.api_client.post(
            self.url, format='json', data=data, authentication=auth)
        self.assertHttpCreated(resp)
        self.assertValidJSON(resp.content)

        for u in [self.standard_user, self.super_user, self.staff_user, self.orgowner_user]:
            data = {}
            data['name'] = 'my new tag'
            auth = self.create_apikey(u['username'], u['api_key'])
            resp = self.api_client.post(
                self.url, format='json', data=data, authentication=auth)
            self.assertHttpBadRequest(resp)

# ResourceTag API


class ResourceTagResourceTest(ResourceTestCase):
    fixtures = ['user.json', 'orb.json']

    def setUp(self):
        super(ResourceTagResourceTest, self).setUp()
        self.url = '/api/v1/resourcetag/'


# ResourceFile API
class ResourceFileTest(ResourceTestCase):
    fixtures = ['user.json', 'orb.json']

    def setUp(self):
        super(ResourceFileTest, self).setUp()
        self.url = '/api/v1/resourcefile/'



class ResourceURLTest(ResourceTestCase):
    fixtures = ['user.json', 'orb.json']

    def setUp(self):
        super(ResourceURLTest, self).setUp()
        self.url = '/api/v1/resourceurl/'
