from __future__ import unicode_literals

from django.conf.urls import url

from orb import views
from orb.resources.views import ResourceFileView, ResourceURLView

urlpatterns = [
    url(r'^create/1/$', views.resource_create_step1_view, name="orb_resource_create"),
    url(r'^create/2/(?P<id>\d+)/$', views.resource_create_step2_view, name="orb_resource_create2"),
    url(r'^create/(?P<id>\d+)/thanks/$', views.resource_create_thanks_view, name="orb_resource_create_thanks"),
    url(r'^view/(?P<resource_slug>\w[\w/-]*)$', views.resource_view, name="orb_resource"),
    url(r'^(?P<id>\d+)$', views.resource_permalink_view, name="orb_resource_permalink"),
    url(r'^create/(?P<id>\d+)/link/(?P<url_id>\d+)/delete/$', views.resource_create_url_delete_view, name="orb_resource_create_delete_url"),
    url(r'^create/(?P<id>\d+)/file/(?P<file_id>\d+)/delete/$', views.resource_create_file_delete_view, name="orb_resource_create_delete_file"),
    url(r'^link/(?P<id>\d+)/$', ResourceURLView.as_view(), name="orb_resource_view_link"),
    url(r'^file/(?P<id>\d+)/$', ResourceFileView.as_view(), name="orb_resource_view_file"),
    url(r'^edit/1/(?P<resource_id>\d+)/$', views.resource_edit_view, name="orb_resource_edit"),
    url(r'^edit/2/(?P<resource_id>\d+)/$', views.resource_edit_step2_view, name="orb_resource_edit2"),
    url(r'^edit/(?P<id>\d+)/link/(?P<url_id>\d+)/delete/$', views.resource_edit_url_delete_view, name="orb_resource_edit_delete_url"),
    url(r'^edit/(?P<id>\d+)/file/(?P<file_id>\d+)/delete/$', views.resource_edit_file_delete_view, name="orb_resource_edit_delete_file"),
    url(r'^edit/(?P<id>\d+)/thanks/$', views.resource_edit_thanks_view, name="orb_resource_edit_thanks"),

    url(r'^approve/(?P<id>\d+)/$', views.resource_approve_view, name="orb_resource_approve"),
    url(r'^pending_mep/(?P<id>\d+)/$', views.resource_pending_mep_view, name="orb_resource_pending_mep"),
    url(r'^reject/(?P<id>\d+)/$', views.resource_reject_view, name="orb_resource_reject"),
    url(r'^reject/(?P<id>\d+)/sent/$', views.resource_reject_sent_view, name="orb_resource_reject_sent"),

    url(r'^guidelines/$', views.resource_guidelines_view, name="orb_guidelines"),
]
