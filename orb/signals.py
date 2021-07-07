"""
Signal definitions for ORB

Should not contain any other handler or task functions
"""
from __future__ import unicode_literals

import django.dispatch
from django.dispatch import Signal

resource_viewed = Signal(providing_args=["resource", "request", "type"])
resource_workflow = Signal(
    providing_args=["request", "resource", "status", "notes", "criteria"])
resource_url_viewed = Signal(providing_args=["resource_url", "request"])
resource_file_viewed = Signal(providing_args=["resource_file", "request"])
search = Signal(
    providing_args=["query", "no_results", "request", "type", "page"])
tag_viewed = Signal(providing_args=["tag", "request", "type", "data"])
user_registered = Signal(providing_args=["user", "request"])
resource_submitted = Signal(providing_args=["resource", "request"])
resource_rejected = django.dispatch.Signal(providing_args=["resource"])
resource_approved = django.dispatch.Signal(providing_args=["resource"])
