"""
Management command to query peer COVID-19 Library instances for updated content and
add those resources or update if they were sourced remotely.

Usage:

    django-admin.py sync_peer_resources

This will sync for all active peers.

Optionally select one or more peers by primary key:

    django-admin.py sync_peer_resources 2 5

The primary keys can be listed using the list_peers command.

"""

from __future__ import unicode_literals

from django.core.management.base import BaseCommand

from orb.peers.models import Peer


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('peer_ids', nargs='*', type=int)

    def handle(self, *args, **options):
        peer_ids = options.get('peer_ids')

        peers = Peer.peers.queryable()
        if peer_ids:
            peers = peers.filter(pk__in=peer_ids)

        for peer in peers:
            peer.sync_resources(writer=self.stdout.write)
