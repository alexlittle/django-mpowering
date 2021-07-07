"""Tests for user registration"""

from __future__ import unicode_literals

import uuid

from django.contrib.auth.models import User
from django.urls import reverse
from django.test import TestCase
from django.test.client import Client
from tastypie.models import ApiKey

from orb.models import UserProfile


class ProfilePageTest(TestCase):
    fixtures = ['user.json', 'orb.json']

    @classmethod
    def setUpClass(cls):
        super(ProfilePageTest, cls).setUpClass()
        standard_user = User.objects.get(username="standarduser")
        api_key, _ = ApiKey.objects.get_or_create(user=standard_user, defaults={"key": str(uuid.uuid4())})

    def test_profile_register(self):
        response = self.client.get(reverse('profile_register'))
        self.assertEqual(response.status_code, 200)

    def test_profile_login(self):
        response = self.client.get(reverse('profile_login'))
        self.assertEqual(response.status_code, 200)

    def test_profile_edit(self):
        response = self.client.get(reverse('my_profile_edit'))
        # should redirect to login page if not logged in
        self.assertEqual(response.status_code, 302)

    def test_login_to_profile_edit(self):
        self.client.login(username='standarduser', password='password')
        response = self.client.get(reverse('my_profile_edit'))
        self.assertEqual(response.status_code, 200)
        self.client.logout()

        response = self.client.get(reverse('profile_register_thanks'))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('profile_logout'))
        self.assertEqual(response.status_code, 200)

    def test_profile_reset(self):
        response = self.client.get(reverse('profile_reset'))
        self.assertEqual(response.status_code, 200)

    def test_profile_reset_sent(self):
        response = self.client.get(reverse('profile_reset_sent'))
        self.assertEqual(response.status_code, 200)


class RegisterTest(TestCase):
    fixtures = ['user.json', 'orb.json']
    new_user_data = {
        'email': 'newuser@example.org',
        'password': 'secret',
        'password_again': 'secret',
        'first_name': 'demo',
        'last_name': 'user',
        'gender': 'none',
        'age_range': 'none',
        'mailing': 1,
        'terms': 1,
        'role_other': 'programmer',
        'role': '0',
        'organisation': 'My Organisation',
        'allow_survey': True,
    }

    def setUp(self):
        self.client = Client()

    def test_register(self):
        no_users_start = User.objects.all().count()
        no_keys_start = ApiKey.objects.all().count()
        no_profiles_start = UserProfile.objects.all().count()

        response = self.client.post(reverse('profile_register'), self.new_user_data)
        self.assertEqual(response.status_code, 302)

        no_users_end = User.objects.all().count()
        no_keys_end = ApiKey.objects.all().count()
        no_profiles_end = UserProfile.objects.all().count()
        self.assertEqual(no_users_start + 1, no_users_end)
        self.assertEqual(no_keys_start + 1, no_keys_end)
        self.assertEqual(no_profiles_start + 1, no_profiles_end)

    def test_register_with_no_data(self):
        response = self.client.post('/profile/register/', {})
        self.assertEqual(response.status_code, 200)

    def test_register_with_missing_data(self):
        no_users_start = User.objects.all().count()
        no_keys_start = ApiKey.objects.all().count()
        no_profiles_start = UserProfile.objects.all().count()

        response = self.client.post('/profile/register/', {})
        self.assertEqual(response.status_code, 200)

        no_users_end = User.objects.all().count()
        no_keys_end = ApiKey.objects.all().count()
        no_profiles_end = UserProfile.objects.all().count()
        self.assertEqual(no_users_start, no_users_end)
        self.assertEqual(no_keys_start, no_keys_end)
        self.assertEqual(no_profiles_start, no_profiles_end)

    def test_login(self):
        response = self.client.post('/profile/login/', {'username': 'newuser@example.org', 'password': 'secret'})
        self.assertEqual(response.status_code, 200)


class PasswordUpdateTest(TestCase):
    fixtures = ['user.json', 'orb.json']

    @classmethod
    def setUpClass(cls):
        super(PasswordUpdateTest, cls).setUpClass()
        standard_user = User.objects.get(username="standarduser")
        api_key, _ = ApiKey.objects.get_or_create(user=standard_user, defaults={"key": str(uuid.uuid4())})

    def test_update_password(self):
        new_password = '123456'
        self.client.login(username='standarduser', password='password')
        data = {'password': new_password, 'password_again': new_password}
        response = self.client.post(reverse('my_profile_edit'), data)
        self.assertEqual(response.status_code, 200)
        self.client.logout()
        self.client.login(username='standarduser', password=new_password)
