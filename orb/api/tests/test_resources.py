# -*- coding: utf-8 -*-

"""
Unit tests for API resources

Run these tests with pytest!

These tests can run without building the entire request cycle or requiring
authentication.

Fixtures are loaded by pytest using root level conftest.py from fixtures module

"""

from __future__ import unicode_literals

import pytest
from django.contrib.auth.models import User
from django.test.client import RequestFactory

from orb.api.resources import ResourceResource, TagResource
from orb.models import Category, Resource, Tag
from orb.resources.tests.factory import resource_factory

pytestmark = pytest.mark.django_db


def get_request():
    factory = RequestFactory()
    request = factory.request()
    return request


def get_resource_data(obj, resource_class, request=None):
    """
    Builds the dehydrated data for a tastypie.Resource

    Performs much the same job as Resource.get_detail

    Args:
        obj: a model instance
        resource_class: tastyepie.Resource class to use
        request: HTTP request object

    Returns:
        dictionary of the data to be returned.

        The return data *may* contain other bundles in the case that the
        API resource includes nested data.

    """
    if not request:
        request = get_request()

    api_resource = resource_class()
    bundle = api_resource.build_bundle(obj=obj, request=request)
    bundle = api_resource.full_dehydrate(bundle)
    return bundle.data


class TestOrbResource(object):
    """
    Tests against the data returned for orb.Resources
    """

    def test_peer_absent(self, test_resource):
        """Ensure source_peer is never in data"""
        resource_data = get_resource_data(test_resource, ResourceResource)
        assert 'source_peer' not in resource_data

    def test_base_languages(self, test_resource):
        resource_data = get_resource_data(test_resource, ResourceResource)
        assert resource_data['languages'] == ['en']

    def test_additional_languages(self, test_resource, mocker):
        mocker.patch.object(test_resource, 'available_languages', return_value=['en', 'es'])
        resource_data = get_resource_data(test_resource, ResourceResource)
        assert resource_data['languages'] == ['en', 'es']

    @pytest.mark.skip("We're down to one language")
    def test_language_fields(self, test_resource, mocker):
        mocker.patch.object(test_resource, 'title_es','Español')
        mocker.patch.object(test_resource, 'title_pt_br','português')
        mocker.patch.object(test_resource, 'description_es','Español description')
        mocker.patch.object(test_resource, 'description_pt_br','português description')

        resource_data = get_resource_data(test_resource, ResourceResource)
        assert sorted(resource_data['languages']) == ['en', 'es', 'pt-br']
        for field in ['title_en', 'title_es', 'title_pt_br', 'description_en', 'description_es', 'description_pt_br']:
            assert field in resource_data
