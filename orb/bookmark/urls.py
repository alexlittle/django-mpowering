from __future__ import unicode_literals

from django.conf.urls import url

from orb.bookmark import views

urlpatterns = [
    url(r'^$', views.resource_bookmark_view, name="orb_bookmark"),
    url(r'^remove/(?P<resource_id>\d+)/$', views.resource_bookmark_remove_view, name="orb_bookmark_remove"),
]
