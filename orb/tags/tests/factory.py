from __future__ import unicode_literals

import uuid

from orb.models import Category, Tag


def category_factory(**kwargs):
    defaults = {
        "name": "Test category",
    }
    defaults.update(kwargs)
    return Category.objects.create(**defaults)


def tag_factory(**kwargs):
    user = kwargs.pop("user", None)
    if user:
        kwargs.update({
            "create_user": user,
            "update_user": user,
        })

    defaults = {
        "category": category_factory(),
        "name": str(uuid.uuid4()),
    }
    defaults.update(kwargs)
    return Tag.objects.create(**defaults)
