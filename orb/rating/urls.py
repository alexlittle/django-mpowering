from __future__ import unicode_literals

from django.conf.urls import url

from orb.rating import views

urlpatterns = [
    url(r'^$', views.resource_rate_view, name="orb_rate"),
]
