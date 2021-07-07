from __future__ import unicode_literals

import urllib2

from django.shortcuts import render

from orb.models import ResourceURL


def check_urls_view(request):
    urls = ResourceURL.objects.all()
    output = []
    for u in urls:
        response = urllib2.Request(u.url)
        url = urlOpener.open(response)

    return render(request, 'orb/manage/urls.html', {'urls': urls})
