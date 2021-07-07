"""
Management command to add a peer to the local list of peers.

The command will return exit code 0 if added OR the peer already exists, and
1 for any other error.

Usage:

    django-admin.py add_peer https://some.host.org --user=username --key=APIKEY --name=SomeHost

"""

from __future__ import unicode_literals

from django.core.management.base import BaseCommand
from django.core.validators import URLValidator, ValidationError

from orb.peers.models import Peer


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('host')
        parser.add_argument(
            '--name',
            dest='name',
            help='Name of the peer',
            required=True,
        )
        parser.add_argument(
            '--user',
            dest='user',
            help='API username',
            required=True,
        )
        parser.add_argument(
            '--key',
            dest='key',
            help='API key',
            required=True,
        )

    def handle(self, *args, **options):
        host = options.get('host')

        try:
            URLValidator()(host)
        except ValidationError as err:
            self.stderr.write("The host name '{}' is not a valid host URL".format(host))
            exit(1)

        peer, created = Peer.objects.get_or_create(host=host, defaults={
            'name': options.get('name'),
            'api_user': options.get('user'),
            'api_key': options.get('key'),
        })

        if not created:
            self.stdout.write("Found existing peer for '{}', not updating".format(host))
        else:
            self.stdout.write("Created new peer '{}'".format(peer))
