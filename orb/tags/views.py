from __future__ import unicode_literals

from django.db.models import Count, Max, Min
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render

from orb.models import Resource, Tag, TagTracker
from orb.signals import tag_viewed


def text_tag_list(request, **filters):
    """
    Returns a text list of cateogry names, newline separated
    """
    content = "\n".join([tag.name for tag in Tag.tags.filter(**filters)])
    return HttpResponse(content=content, content_type="text/plain; charset=utf-8")


def simple_language_list(request):
    """Returns language tags"""
    return text_tag_list(request, category__slug="language")


def simple_geography_list(request):
    """Returns geography tags"""
    return text_tag_list(request, category__slug="geography")


def simple_orgs_list(request):
    """Returns organisation tags"""
    return text_tag_list(request, category__slug="organisation")


def simple_tags_list(request):
    """Returns tags from outside of the ORB taxonomy"""
    return text_tag_list(request, category__slug="other")


def tag_cloud_view(request):

    tags = Tag.objects.filter(resourcetag__resource__status=Resource.APPROVED).annotate(
        dcount=Count('resourcetag__resource')).order_by('name')
    max = tags.aggregate(max=Max('dcount'))
    min = tags.aggregate(min=Min('dcount'))
    diff = max['max'] - min['min']
    return render(request, 'orb/tag_cloud.html', {'tags': tags, 'diff': diff})


def tag_link_view(request, id):
    tag = get_object_or_404(Tag, pk=id)

    tag_viewed.send(sender=tag, tag=tag, request=request,
                    data=tag.external_url, type=TagTracker.VIEW_URL)
    return HttpResponseRedirect(tag.external_url)
