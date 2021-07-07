from __future__ import unicode_literals

from orb.models import Resource, ResourceURL


def resource_factory(**kwargs):
    user = kwargs.pop("user", None)
    if user:
        kwargs.update({
            "create_user": user,
            "update_user": user,
        })

    defaults = {
        "title": "Test resource",
        "description": "Test resource",
    }
    defaults.update(kwargs)
    return Resource.objects.create(**defaults)


def resource_url_factory(**kwargs):
    user = kwargs.pop("user", None)
    if user:
        kwargs.update({
            "create_user": user,
            "update_user": user,
        })

    defaults = {
        "url": "http://www.example.com",
    }
    defaults.update(kwargs)
    return ResourceURL.objects.create(**defaults)
