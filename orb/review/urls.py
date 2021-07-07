from __future__ import unicode_literals

from django.conf.urls import url

from orb.review.views import (assign_review, delete_resource, reject_resource, resource_review_list, review_resource,
                              staff_review, start_assignment, user_review_list)

urlpatterns = [
    url(r'^$', view=resource_review_list, name="orb_pending_resources"),
    url(r'^my-reviews/$', view=user_review_list, name="orb_user_reviews"),
    url(r'^(?P<resource_id>\d+)/$',
        view=staff_review, name="orb_staff_review"),
    url(r'^(?P<resource_id>\d+)/start/$',
        view=start_assignment, name="orb_start_review"),
    url(r'^(?P<resource_id>\d+)/assignment/$',
        view=assign_review, name="orb_assign_review"),
    url(r'^(?P<resource_id>\d+)/delete/$',
        view=delete_resource, name="orb_delete_resource"),
    url(r'^(?P<resource_id>\d+)/assignment/(?P<review_id>\d+)/$',
        view=review_resource, name="orb_resource_review"),
    url(r'^(?P<resource_id>\d+)/assignment/(?P<review_id>\d+)/reject/$',
        view=reject_resource, name="orb_reject_resource"),
]
