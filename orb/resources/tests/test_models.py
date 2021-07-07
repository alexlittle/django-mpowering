# -*- coding: utf-8 -*-

"""
Tests for ORB resource models

Fixtures are loaded by pytest using root level conftest.py from fixtures module
"""

from __future__ import unicode_literals

import json
import os
import uuid
from copy import deepcopy
from datetime import datetime

import mock
import pytest
import six
from dateutil.relativedelta import relativedelta

from orb.models import Resource, ResourceFile, ResourceURL, get_import_user
from orb.resources.tests.factory import resource_factory

pytestmark = pytest.mark.django_db


@pytest.fixture(scope="module")
def api_data():
    dirname = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(dirname, "resource_from_api.json"), "r") as json_file:
        file_data = json_file.read()
    yield json.loads(file_data)


@pytest.fixture(scope="module")
def languages_api_data():
    dirname = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(dirname, "resource_from_api_diff_languages.json"), "r") as json_file:
        file_data = json_file.read()
    yield json.loads(file_data)


class TestResource(object):

    def test_guid(self, test_resource):
        assert test_resource.guid is not None

    def test_absolute_url(self, test_resource):
        """URL is returned with slug"""
        assert test_resource.get_absolute_url() == "/resource/view/basica-salud-del-recien-nacido"

    def test_unicode_display(self, test_resource):
        """Unicode value of title is returned"""
        assert six.text_type(test_resource) == "Básica salud del recién nacido"

    def test_non_latin_slugification(self, admin_user):
        """Non-latin characters should be transliterated"""
        test_user = admin_user
        cyrillic_resource= resource_factory(
            user=test_user,
            title="Санкт-Петербург Питоны",  # Saint Petersburg Pythons
            description="Some resource",
        )
        assert cyrillic_resource.slug == "sankt-peterburg-pitony"

        chinese_resource= resource_factory(
            user=test_user,
            title="北京蟒蛇",  # Beijing Pythons
            description="Some resource",
        )
        assert chinese_resource.slug == "bei-jing-mang-she"

    def test_unique_slugification(self, admin_user):
        """Unique slug is generated for new resources"""
        test_user = admin_user
        original = resource_factory(
            user=test_user,
            title="Básica salud del recién nacido",
            description="Básica salud del recién nacido",
        )
        duplicate = resource_factory(
            user=test_user,
            title="Básica salud del recién nacido",
            description="Básica salud del recién nacido",
        )
        assert original.slug == "basica-salud-del-recien-nacido"
        assert original.slug != duplicate.slug
        assert duplicate.slug == "basica-salud-del-recien-nacido-2"

    def test_languages(self, test_resource, settings):
        """Instance method should return list of available languages"""
        settings.LANGUAGES = [
            ('en','English'),
            # ('es','Español'),
            # ('pt-br','Português'),
        ]
        test_resource.title_en = "Hey"
        # test_resource.title_pt_br = "Hey"
        test_resource.description_en = "Hey"
        # test_resource.description_pt_br = "Hey"
        # test_resource.title_es = "hola"
        # assert test_resource.available_languages() == ["en", "pt-br"]
        assert test_resource.available_languages() == ["en"]


class TestResourceURL(object):

    def test_unicode_display(self):
        """Unicode value of URL is returned"""
        assert six.text_type(ResourceURL(url="http://www.example.com/niños")) == "http://www.example.com/niños"


class TestResourceFile(object):

    @pytest.mark.parametrize("extension,mimetype", [
        ("pdf", "application/pdf"),
        ("mp4", "video/mp4"),
        ("mbz", "application/octet-stream"),
        ("zip", "application/zip"),
        ("docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
        ("png", "image/png"),
        ("ppt", "application/vnd.ms-powerpoint"),
        ("jpg", "image/jpeg"),
        ("pptx", "application/vnd.openxmlformats-officedocument.presentationml.presentation"),

        # TODO(bennylope) this is failing only in CI
        # ("m4v", "video/x-m4v"),

        ("mov", "video/quicktime"),
        ("wmv", "video/x-ms-wmv"),
        ("zzz", "application/octet-stream"),
    ])
    def test_mimetype(self, extension, mimetype, mocker):
        """"""
        mocked_extension = mocker.patch('orb.models.ResourceFile.file_extension', new_callable=mock.PropertyMock)
        mocked_extension.return_value = extension
        r = ResourceFile()
        assert r.mimetype == mimetype


class TestResourceLocality(object):

    def test_local_resource(self, test_resource):
        assert test_resource.is_local()

    def test_downloaded_resource(self, test_resource, peer_instance):
        """A source peer should mark a resource as not local"""
        test_resource.source_peer = peer_instance
        assert not test_resource.is_local()

    def test_sourced_resource(self, test_resource, peer_instance):
        """Both a source name and host should mark a resource as not local"""
        test_resource.source_name = "Another ORB"
        test_resource.source_host = "http://www.yahoo.com"
        test_resource.source_peer = peer_instance
        assert not test_resource.is_local()


class TestUpdateFromAPI(object):
    """
    The update_from_api instance method.
    """

    def test_local_is_source(self, test_resource, api_data):
        """Raises ValueError if the local copy is the source

        Protects local copy from being accidentally overwritten.
        """
        test_data = deepcopy(api_data)
        test_resource.guid = test_data['guid']
        test_resource.is_local = lambda: True

        with pytest.raises(LookupError):
            test_resource.update_from_api(test_data)

    def test_update_missing_resource(self, test_resource, api_data):
        """Raises LookupError if the GUIDs don't match

        Protects local copy from being accidentally overwritten.
        """
        test_data = deepcopy(api_data)
        test_resource.guid = str(uuid.uuid4())

        with pytest.raises(LookupError):
            test_resource.update_from_api(test_data)

    def test_doesnt_need_updating(self, test_resource, api_data):
        """Returns False if the api_data modification <= local creation"""
        test_data = deepcopy(api_data)
        test_data['update_date'] = "{}".format(datetime(2010, 1, 1))
        test_resource.guid = test_data['guid']
        test_resource.is_local = lambda: False
        assert test_resource.update_from_api(test_data) is False

    @pytest.mark.skip("This test can be run independently but fails in the suite due to fixture key issues")
    def test_update_resource_data(self, remote_resource, api_data):
        test_data = deepcopy(api_data)
        test_data['update_date'] = datetime.now() + relativedelta(days=1)  # make this in the future
        test_data['title'] = 'My test Resource'
        test_data['title_en'] = 'My test Resource'
        test_data['description'] = 'Just another test resource'
        test_data['description_en'] = 'Just another test resource'
        remote_resource.guid = test_data['guid']

        assert remote_resource.update_from_api(test_data) is True

        assert remote_resource.title == 'My test Resource'
        assert remote_resource.description == 'Just another test resource'


class TestResourceFromAPI(object):
    """
    The create_from_api class method for each respective thing.

    Ultimately we want a single entry point, function or method, that
    takes the dictionary of data and returns

    - Tests when languages do not match (e.g. incoming language is not present)
    """
    def test_sanity(self, api_data):
        """Verify what we're getting from the fixture"""
        assert "Dosing Guidelines Poster" == api_data['title']

    def test_returns_resource(self, api_data):
        """Creates the orb.Resource and associated content"""
        test_data = deepcopy(api_data)
        result = Resource.create_from_api(test_data)

        assert isinstance(result, Resource)
        assert result.guid == "db557aca-f190-45d5-8988-d574bd21cdcf"
        assert result.create_user == get_import_user()
        # assert result.create_date.date == date(2015, 5, 18)
        assert result.description == "<p>Dosing Guidelines Poster</p>"
        assert result.description_en == "<p>Dosing Guidelines Poster</p>"
        # assert result.description_es == "<p>Pautas de dosificación</p>"
        # assert result.description_pt_br == "<p>Diretrizes de dosagem</p>"
        assert result.source_url == "http://www.cool-org.org/resource/view/dosing-guidelines-poster"

        assert not result.resourcefile_set.all().exists()
        assert result.resourceurl_set.all().count() == 3  # 1 source URL and 2 source files

        assert result.resourcetag_set.all().count() == 2

    @pytest.mark.xfail(strict=True)
    def test_language_mismatch(self, languages_api_data):
        """Creates the orb.Resource using only languages available locally

        Also should match near-enough languages, e.g. pt and pt-br
        """
        test_data = deepcopy(languages_api_data)
        result = Resource.create_from_api(test_data)

        assert isinstance(result, Resource)
        assert result.guid == "db557aca-f190-45d5-8988-d574bd21cdcf"
        assert result.create_user == get_import_user()
        # assert result.create_date.date == date(2015, 5, 18)
        assert result.description == "<p>Dosing Guidelines Poster</p>"
        assert result.description_en == "<p>Dosing Guidelines Poster</p>"
        assert result.description_pt == ""
        assert result.source_url == "http://www.cool-org.org/resource/view/dosing-guidelines-poster"

        assert not result.resourcefile_set.all().exists()
        assert result.resourceurl_set.all().count() == 3  # 1 source URL and 2 source files



def test_get_importer_user():
    importer = get_import_user()
    assert not importer.has_usable_password()
    assert not importer.is_active
    assert not importer.is_staff
    assert not importer.is_superuser
