"""
A Django-specific layer around the ORB API client
"""

from __future__ import unicode_literals

from orb_api import OrbClient


class ORMClient(OrbClient):
    """

    """
    def __init__(self, peer):
        """
        Initialize the client

        Args:
            peer: an orb.Peer instance

        """
        super(ORMClient, self).__init__(peer.host, peer.api_user, peer.api_key, sleep=1)

    def query_resources(self):
        """

        Returns:

        """
