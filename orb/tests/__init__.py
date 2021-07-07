"""
Integration level tests for cross-app functionality
"""
from __future__ import unicode_literals


from tastypie.test import ResourceTestCaseMixin
from django.test import TestCase


class ResourceTestCase(ResourceTestCaseMixin, TestCase):
    """
    Replaces deprecated tastypie.test.ResourceTestCase

    Simplifies replacement
    """
