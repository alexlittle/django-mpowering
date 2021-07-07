"""
This is a debugging command designed to test emails on the system
"""

from __future__ import unicode_literals

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from orb.models import Resource
from orb.review import tasks
from orb.review.models import ContentReview


class Command(BaseCommand):
    help = 'Checks for pending reviews and sends a reminder to the reviewer'

    def handle(self, *args, **options):
        if settings.EMAIL_BACKEND != 'django.core.mail.backends.console.EmailBackend':
            # Guard against accidentally sending out emails
            raise CommandError("You are using the '{}' email backend."
                               "This command only runs using the console.EmailBackend.".format(settings.EMAIL_BACKEND))

        resources_with_titles = Resource.objects.filter(title__gt="")
        task_names = {
            'review_assignment': (tasks.send_review_assignment_email, ContentReview.reviews.all().first),
            'review_reminder': (tasks.send_review_reminder_email, ContentReview.reviews.all().first),
            'resource_approved': (tasks.send_resource_approved_email, resources_with_titles.first),
            'resource_rejected': (tasks.send_resource_rejected_email,
                                  resources_with_titles.filter(status="rejected").first),
            'review_complete': (tasks.send_review_complete_email, resources_with_titles.first,
                                [], {'verdict': Resource.APPROVED}),
        }

        for arg in args:
            try:
                function, get_object = task_names[arg]
            except ValueError:
                try:
                    function, get_object, args, kwargs = task_names[arg]
                except ValueError:
                    raise CommandError("Ooops: {}".format(exc))
                else:
                    function(get_object(), *args, **kwargs)
            else:
                function(get_object())
