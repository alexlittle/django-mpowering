"""
Management command to add a superuser with CLI args including UserProfile

This should only be used to programmatically create superusers with *initial*
passwords, to be changed after creation.

Usage:

    django-admin.py add_super_user --email="someone@hello.com" --password="COOLPASSWORD"

"""

from __future__ import unicode_literals

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.core.management import call_command

from orb.models import UserProfile


class Command(BaseCommand):

    help = (
        "Creates a new superuser; without arguments calls the default "
        "Django createsuperuser command and then creates an initial UserProfile"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            dest='email',
            help='Email address',
            required=False,
        )
        parser.add_argument(
            '--password',
            dest='password',
            help='Initial password',
            required=False,
        )

    def handle(self, *args, **options):

        username = options.get('email')
        password = options.get('password')

        if username and password:
            try:
                user = get_user_model().objects.get(username=username)
            except get_user_model().DoesNotExist:
                user = get_user_model().objects.create_superuser(
                    username,
                    password=password,
                    email=options.get('email'),
                )
                UserProfile.objects.create(user=user)
                self.stdout.write("Create new user '{}'".format(username))
            else:
                self.stdout.write("Found existing user '{}'".format(username))
        else:
            call_command("createsuperuser")
            user = get_user_model().objects.all().order_by("-id").first()

        UserProfile.objects.create(user=user)
