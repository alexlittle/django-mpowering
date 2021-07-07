# -*- coding: utf-8 -*-

"""
Tests for COVID-19 Library resource models
"""

from __future__ import unicode_literals

import pytest
from six import text_type

from orb.peers.models import Peer


class TestPeerModel(object):
    """
    Tests for the primary Peer model
    """
    def test_string_representation(self):
        peer = Peer(name="Another ORB", host="http://www.yahoo.mx")
        assert text_type(peer) == "Another ORB"


@pytest.mark.django_db
class TestPeerQuerysets(object):

    def test_active_peers(self):
        Peer.peers.create(name="Second ORB", host="http://www.yahoo.mx")
        Peer.peers.create(name="Third ORB", host="http://www.yahoo.ca", active=False)
        assert "Second ORB" == Peer.peers.active().get().name

    def test_queryable(self):
        assert not Peer.peers.queryable()
        Peer.peers.create(name="API ORB", host="http://www.yahoo.de", active=True, api_user="bob", api_key="1")
        assert Peer.peers.queryable().count() == 1


@pytest.mark.django_db
class TestLoggingQuerysets(object):

    def test_log(self):
        peer = Peer.peers.create(name="Sécond ORB", host="http://www.yahoo.mx")
        update_log = peer.logs.create()
        update_log.finish()
        assert update_log.finished > update_log.created
