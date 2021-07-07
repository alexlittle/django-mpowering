from __future__ import unicode_literals

from django.conf.urls import url
from django.contrib.auth.views import LogoutView
from django.views.generic import TemplateView
from django.views.i18n import set_language

from orb.profiles import views

urlpatterns = [
    url(r'^register/$', view=views.RegistrationView.as_view(), name="profile_register"),
    url(r'^register/thanks/$', TemplateView.as_view(template_name="orb/thanks.html"), name="profile_register_thanks"),
    url(r'^login/$', views.login_view, name="profile_login"),
    url(r'^logout/$', LogoutView.as_view(template_name='orb/logout.html'), name="profile_logout"),
    url(r'^setlang/$', set_language, name="profile_set_language"),
    url(r'^reset/$', views.reset, name="profile_reset"),
    url(r'^reset/sent/$', TemplateView.as_view(template_name="orb/profile/reset-sent.html"), name="profile_reset_sent"),
    url(r'^view/(?P<id>\d+)/$', views.view_profile, name="profile_view"),
    url(r'^edit/$', views.edit, name="my_profile_edit"),
    url(r'^view/$', views.view_my_profile, name="my_profile_view"),
    url(r'^view/bookmarks/$', views.view_my_bookmarks, name="my_bookmarks_view"),
    url(r'^view/ratings/$', views.view_my_ratings, name="my_ratings_view"),
    url(r'^export/$', views.export_data, name="profile_export_data"),
    url(r'^delete/$', views.delete_account, name="profile_delete_account"),
    url(r'^delete/complete/$', views.delete_account_complete, name="profile_delete_account_complete"),
]
