# -*- coding: utf-8 -*-

"""
Courseware display and management views

Course data is stored and transferred as JSON
"""

from __future__ import unicode_literals

import json
import logging

from django import http
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views import generic
from django.views.decorators.csrf import csrf_exempt
from six import text_type

from orb import mixins
from orb.courses import forms, models

logger = logging.getLogger(__name__)


def response_messages(key):
    messages = {
        "error_saving": _("There was an error trying to save your course"),
        "json_error": _("JSON decoding error"),
        "permission_error": _("You do not have permission to edit this course"),
        "same": _("Your changes have been saved."),
        models.CourseStatus.published.name: _("Your course is now public."),
        models.CourseStatus.draft.name: _("Your course is now in draft status."),
        models.CourseStatus.archived.name: _("Your course has been removed."),
    }
    try:
        return text_type(messages.get(key))
    except KeyError:
        logger.error("No such message key '{}'".format(key))
        return key


def course_save_message(original_status, updated_status):
    # type: (str, str) -> str
    """Returns a message suitable for saving a course"""
    status = "same" if original_status == updated_status else updated_status
    return response_messages(status)


class CoursesListView(generic.ListView):
    template_name = "orb/courses/course_list.html"
    context_object_name = "courses"

    def get_queryset(self):
        return models.Course.courses.viewable(self.request.user).order_by("-id")

    def get_context_data(self, **kwargs):
        context = super(CoursesListView, self).get_context_data(**kwargs)
        context["courses_json"] = json.dumps(
            list(self.get_queryset().json_repr(self.request.user))
        )
        return context


class CourseCreateView(mixins.LoginRequiredMixin, generic.CreateView):
    """
    View for creating a new course
    """

    model = models.Course
    fields = "__all__"
    template_name = "orb/courses/course_form.html"

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(CourseCreateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CourseCreateView, self).get_context_data(**kwargs)
        context.update({"course_json": json.dumps(models.Course.empty_json_repr())})
        return context

    def post(self, request, *args, **kwargs):
        """
        Handles a JSON request to save the course data

        Args:
            request:
            *args:
            **kwargs:

        Returns:

        """
        try:
            data = json.loads(request.body)
        except ValueError as e:
            logger.debug(e)
            return http.JsonResponse({"errors": _("JSON decoding error")}, status=400)

        form_data = {"sections": json.dumps(data["sections"]), "title": data["title"]}
        form = forms.CourseForm(user=request.user, data=form_data)

        if form.is_valid():
            course = form.save()  # Any checks against resource keys should happen here
            return http.JsonResponse(
                {
                    "course_id": course.id,
                    "course_status": course.status,
                    "status": "ok",
                    "url": course.get_absolute_url(),
                    "message": course_save_message(course.status, course.status),
                },
                status=201,
            )

        else:
            # form.errors is a dictionary with field names for keys and
            # the values of each is a list of errors in string format
            return http.JsonResponse(
                {
                    "message": response_messages("error_saving"),
                    "status": "error",
                    "errors": form.errors,
                },
                status=400,
            )


class CourseView(generic.DetailView):
    """
    View for displaying and editing a course

    The GET method is based entirely on rendered template HTML

    The POST method is entirely AJAX/JSON based
    """

    base_queryset = models.Course.courses.active()
    template_name = "orb/courses/course_form.html"

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(CourseView, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return self.base_queryset.viewable(self.request.user)

    def user_can_edit(self, user):
        """Checks if the user has the right to edit this course"""
        # return user.is_staff or user == self.object.create_user
        return self.base_queryset.editable(user).filter(pk=self.object.pk).exists()

    def get_context_data(self, **kwargs):
        context = super(CourseView, self).get_context_data(**kwargs)
        context.update(
            {
                "can_edit": self.user_can_edit(self.request.user),
                "course_json": json.dumps(
                    self.get_object().json_repr(self.request.user)
                ),
            }
        )
        return context

    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        """
        Handles a JSON request to save the course data
        """
        self.object = self.get_object()
        original_status = self.object.status

        if not self.user_can_edit(request.user):
            return http.JsonResponse(
                {
                    "message": response_messages("permission_error"),
                    "status": "error",
                    "errors": response_messages("permission_error"),
                },
                status=403,
            )

        try:
            data = json.loads(request.body)
        except ValueError as e:
            logger.debug(e)
            return http.JsonResponse(
                {
                    "message": response_messages("json_error"),
                    "status": "error",
                    "errors": response_messages("json_error"),
                },
                status=400,
            )

        form_data = {
            "sections": json.dumps(data["sections"]),
            "title": data["title"],
            "status": data["status"],
        }
        form = forms.CourseForm(data=form_data, instance=self.object, user=request.user)

        if form.is_valid():
            course = form.save()  # Any checks against resource keys should happen here
            return http.JsonResponse(
                {
                    "course_id": course.id,
                    "course_status": course.status,
                    "status": "ok",
                    "message": course_save_message(original_status, course.status),
                }
            )

        else:
            # form.errors is a dictionary with field names for keys and
            # the values of each is a list of errors in string format
            return http.JsonResponse(
                {
                    "message": response_messages("error_saving"),
                    "status": "error",
                    "errors": form.errors,
                },
                status=400,
            )


class MoodleExportView(generic.DetailView):
    """
    Exports a course to a Moodle backup format
    """

    queryset = models.Course.courses.active()
    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        response = HttpResponse(content_type="application/vnd.moodle.backup")
        response["Content-Disposition"] = (
            "attachment; filename=%s" % self.object.moodle_file_name
        )
        response.content = self.object.moodle_backup()
        return response


class OppiaExportView(generic.DetailView):
    """
    Exports a course to a Oppia backup format
    """

    queryset = models.Course.courses.active()
    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        response = HttpResponse(content_type="application/zip")
        response["Content-Disposition"] = (
            "attachment; filename=%s" % self.object.oppia_file_name
        )
        response.content = self.object.oppia_backup()
        return response


class OppiaPublishView(generic.DetailView, generic.FormView):
    form_class = forms.OppiaPublishForm
    template_name = "orb/courses/publish_to_oppia.html"
    queryset = models.Course.courses.active()

    def form_valid(self, form):
        """"""
        self.object = self.get_object()
        content = self.object.oppia_backup()
        success, status, message = models.OppiaLog.objects.publish(
            self.object, self.request.user, content, **form.cleaned_data
        )
        if success:
            messages.success(self.request, message)
            return redirect(self.object.get_absolute_url())
        else:
            messages.error(self.request, message)
            return self.form_invalid(form)
