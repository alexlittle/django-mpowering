from __future__ import unicode_literals

from django.contrib import admin

from .models import Peer, PeerQueryLog


@admin.register(Peer)
class PeerAdmin(admin.ModelAdmin):
    list_filter = ['active']
    list_display = ['name', 'host', 'is_queryable']


@admin.register(PeerQueryLog)
class PeerQueryLogAdmin(admin.ModelAdmin):
    list_filter = ['peer']
    list_display = ['peer', 'created', 'new_resources', 'skipped_local_resources', 'updated_resources']
    readonly_fields = ['peer', 'created', 'finished', 'filtered_date', 'new_resources',
                       'skipped_local_resources', 'updated_resources', 'unchanged_resources']

    def has_delete_permission(self, request, obj=None):
        return False
