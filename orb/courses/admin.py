from __future__ import unicode_literals

from django.contrib import admin

from orb.courses import forms, models


@admin.register(models.Course)
class CourseAdmin(admin.ModelAdmin):
    form = forms.CourseAdminForm
    list_display = ["title", "status", "create_user"]


@admin.register(models.OppiaLog)
class OppiaLogAdmin(admin.ModelAdmin):
    list_display = ["create_date", "oppia_host", "user", "status", "success"]
    list_filter = ["success", "status"]
