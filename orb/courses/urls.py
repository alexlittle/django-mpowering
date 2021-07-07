from __future__ import unicode_literals

from django.conf.urls import url

from orb.courses import views

urlpatterns = [
    url(r"^$", view=views.CoursesListView.as_view(), name="courses_list"),
    url(r"^new/$", view=views.CourseCreateView.as_view(), name="courses_create"),
    url(r"^(?P<pk>\d+)/$", view=views.CourseView.as_view(), name="courses_edit"),
    url(
        r"^(?P<pk>\d+)\.mbz$",
        view=views.MoodleExportView.as_view(),
        name="courses_moodle_export",
    ),
    url(
        r"^(?P<pk>\d+)\.zip$",
        view=views.OppiaExportView.as_view(),
        name="courses_oppia_export",
    ),
    url(
        r"^(?P<pk>\d+)/publish/$",
        view=views.OppiaPublishView.as_view(),
        name="courses_oppia_publish",
    ),
]
