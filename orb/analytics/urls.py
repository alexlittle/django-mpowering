from __future__ import unicode_literals

from django.conf.urls import url

from orb.analytics import views

urlpatterns = [
    url(r'^$', view=views.home_view, name="orb_analytics_home"),
    url(r'^mailinglist/$', view=views.mailing_list_view, name="orb_analytics_mailing_list"),
    url(r'^visitor/$', view=views.visitor_view, name="orb_analytics_visitor"),
    url(r'^visitor/(?P<year>\d+)/(?P<month>\d+)/$', view=views.visitor_view, name="orb_analytics_visitor_month_view"),
    url(r'^tag/(?P<id>\d+)/$', view=views.tag_view, name="orb_analytics_tag"),
    url(r'^tag/(?P<id>\d+)/download/(?P<year>\d+)/(?P<month>\d+)/$', view=views.tag_download, name="orb_analytics_download"),
    url(r'^resource/(?P<id>\d+)/$', view=views.resource_view, name="orb_analytics_resource"),
    url(r'^assets/$', view=views.resource_tracker_stats, name="orb_resource_asset_stats"),
    url(r'^kpi/$', view=views.kpi_view, name="orb_analytics_kpi"),
    url(r'^resource-download/$', view=views.resource_download_view, name="orb_analytics_resource_download"),
]
