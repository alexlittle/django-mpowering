from __future__ import unicode_literals

from django.contrib.syndication.views import Feed
from django.shortcuts import get_object_or_404

from orb.models import Resource, Tag


class LatestTagEntries(Feed):
    description_template = 'feeds/resource.html'
    link = "/"

    def get_object(self, request, tag_slug):
        return get_object_or_404(Tag, slug=tag_slug)

    def title(self, obj):
        return "'%s' COVID-19 Library resources" % obj.name

    def description(self, obj):
        return "Resources recently tagged with  %s" % obj.name

    def items(self, obj):
        return Resource.objects.filter(status=Resource.APPROVED, resourcetag__tag=obj).order_by('-create_date')[:20]

    def item_pubdate(self, item):
        return item.create_date

    def item_updateddate(self, item):
        return item.update_date


class LatestEntries(Feed):
    description_template = 'feeds/resource.html'
    title = "COVID-19 Library latest resources"
    link = "/"
    description = "Latest resources added to COVID-19 Library."

    def items(self):
        return Resource.objects.filter(status=Resource.APPROVED).order_by('-update_date')[:20]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.description
