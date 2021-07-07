"""
Management command for issuing a reminder to content reviews

This is just an interface to the remind_reviewers function in the
tasks module.

The command should be run once per day.
"""

from __future__ import unicode_literals

from django.core.management.base import BaseCommand

from orb.review.tasks import remind_reviewers


class Command(BaseCommand):
    help = 'Checks for pending reviews and sends a reminder to the reviewer'

    def handle(self, *args, **options):
        remind_reviewers()
