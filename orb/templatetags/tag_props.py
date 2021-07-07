from __future__ import unicode_literals

from django import template

from orb.models import TagProperty

register = template.Library()


@register.filter(name='tag_property')
def tag_property(tag, name):
    try:
        tp = TagProperty.objects.filter(tag=tag, name=name)
        return tp[0].value
    except IndexError:
        return None
