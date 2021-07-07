# -*- coding: utf-8 -*-

"""
Tests for ORB tag views
"""
from __future__ import unicode_literals

import pytest


@pytest.mark.skip("Fixture problems when run in full test suite")
@pytest.mark.django_db
def test_tag_view_loads(client, sample_tag):
    response = client.get(sample_tag.get_absolute_url())
    assert response.status_code == 200


@pytest.mark.skip("Fixture problems when run in full test suite")
@pytest.mark.django_db
def test_loads_with_ordering(client, sample_tag):
    url = "{}?order=-create_date".format(sample_tag.get_absolute_url())
    response = client.get(url)
    assert response.status_code == 200


@pytest.mark.skip("Fixture problems when run in full test suite")
@pytest.mark.regression_test
@pytest.mark.django_db
def test_loads_with_bad_value(client, sample_tag):
    url = "{}?order=discount".format(sample_tag.get_absolute_url())
    response = client.get(url)
    assert response.status_code == 200
