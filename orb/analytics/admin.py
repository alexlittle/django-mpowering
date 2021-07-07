from __future__ import unicode_literals

from django.contrib import admin

from orb.analytics.models import UserLocationVisualization

# Register your models here.


class UserLocationVisualizationAdmin(admin.ModelAdmin):
    list_display = ('ip', 'hits', 'country_code', 'region')

admin.site.register(UserLocationVisualization, UserLocationVisualizationAdmin)
