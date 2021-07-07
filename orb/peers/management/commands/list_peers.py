"""
Management command to list COVID-19 Library peer data

Usage:

    $ django-admin.py list_peers

      [1] Malawi COVID-19 Library, https://www.malawi-orb.org
      [2] COVID-19 Library Pakistan, https://www.orb.pk

"""

from __future__ import unicode_literals

from django.core.management.base import BaseCommand

from orb.peers.models import Peer


class Command(BaseCommand):

    def handle(self, *args, **options):
        summary = Peer.peers.summary()
        if not summary:
            print("No peers have been registered.")

        if summary.get("queryable"):
            print("\nQueryable peers\n")
            for peer in summary["queryable"]:
                print("[{}] {}, {}".format(peer.pk, peer.name, peer.host))

        if summary.get("inactive") or summary.get("unqueryable"):
            print("\nUnqueryable peers (will not be synced)\n")
            for peer in summary.get("inactive", []):
                print("[{}] {}, {} - inactive".format(peer.pk, peer.name, peer.host))
            for peer in summary.get("unqueryable", []):
                print("[{}] {}, {} - missing credentials".format(peer.pk, peer.name, peer.host))
