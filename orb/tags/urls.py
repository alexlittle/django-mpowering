from __future__ import unicode_literals

from django.conf.urls import url

from orb.tags import views

urlpatterns = [
    url(r'^link/(?P<id>\d+)/$', views.tag_link_view, name="orb_tag_view_link"),
    url(r'^cloud/$', views.tag_cloud_view, name="orb_tag_cloud"),
    url(r'^languages\.txt$', views.simple_language_list, name="orb_simple_language_list"),
    url(r'^geography\.txt$', views.simple_geography_list, name="orb_simple_geography_list"),
    url(r'^organisations\.txt$', views.simple_orgs_list, name="orb_simple_orgs_list"),
    url(r'^other\.txt$', views.simple_tags_list, name="orb_simple_tags_list"),
]
