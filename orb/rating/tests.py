from __future__ import unicode_literals

from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.urls import reverse
from django.test import TestCase

from orb.models import Resource, ResourceRating
from orb.tests.utils import login_client


class RatingTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super(RatingTest, cls).setUpClass()
        cls.rating_user = User.objects.create_user(
            username="rating_user",
            email="rater@example.com",
            password="password",
        )
        cls.other_user = get_user_model().objects.create_user(
            username="other_user",
            email="other@example.com",
            password="password",
        )
        cls.resource = Resource.objects.create(
            title="Test resource",
            description="Test description",
            create_user=cls.rating_user,
            update_user=cls.rating_user,
        )

    @classmethod
    def tearDownClass(cls):
        User.objects.all().delete()

    @login_client(username='rating_user', password='password')
    def test_get_requests(self):
        """check can't do a get request"""
        response = self.client.get(reverse('orb_rate'))
        self.assertEqual(response.status_code, 405)

    def test_anon_users(self):
        """check anon user can't post"""
        rating = {'resource': self.resource.pk, 'rating': 5}
        response = self.client.post(reverse('orb_rate'), rating)
        self.assertEqual(response.status_code, 302)

    @login_client(username='rating_user', password='password')
    def test_missing_data(self):
        """check both resource and rating are required"""
        for rating in [{'resource': self.resource.pk}, {}, None]:
            response = self.client.post(reverse('orb_rate'), rating)
            self.assertEqual(response.status_code, 400)

    @login_client(username='rating_user', password='password')
    def test_missing_resource(self):
        """check invalid resource"""
        rating = {'resource': 5555, 'rating': 5}
        response = self.client.post(reverse('orb_rate'), rating)
        self.assertEqual(response.status_code, 400)

    @login_client(username='rating_user', password='password')
    def test_invalid_score(self):
        """check invalid rating score"""
        for rating in [{'resource': self.resource.pk, 'rating': 6},
                        {'resource': self.resource.pk, 'rating': 0},
                        {'resource': self.resource.pk, 'rating': -1}]:
            response = self.client.post(reverse('orb_rate'), rating)
            self.assertEqual(response.status_code, 400)

    @login_client(username='rating_user', password='password')
    def test_rating_updated(self):
        """check rating gets updated rather than as new"""
        rating = {'resource': self.resource.pk, 'rating': 3}
        ratings_count_start = ResourceRating.objects.all().count()

        response = self.client.post(reverse('orb_rate'), rating)
        self.assertEqual(response.status_code, 200)
        ratings_count_end = ResourceRating.objects.all().count()
        self.assertEqual(ratings_count_start + 1, ratings_count_end)

        self.assertEqual(
            3,
            ResourceRating.objects.get(user=self.rating_user, resource=self.resource).rating,
        )

        rating = {'resource': self.resource.pk, 'rating': 5}
        ratings_count_start = ResourceRating.objects.all().count()
        response = self.client.post(reverse('orb_rate'), rating)
        ratings_count_end = ResourceRating.objects.all().count()
        self.assertEqual(ratings_count_start, ratings_count_end)

        self.assertEqual(
            5,
            ResourceRating.objects.get(user=self.rating_user, resource=self.resource).rating,
        )
