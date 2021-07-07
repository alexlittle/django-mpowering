"""
Models for the ORB content sharing network
"""
from __future__ import unicode_literals

import logging

from django.db import models
from django.db.models import Q
from django.utils.encoding import python_2_unicode_compatible
from django.utils.functional import cached_property
from django.utils.timezone import now
from orb_api.api import OrbClient

from orb.peers.tasks import send_peer_sync_notification_email

logger = logging.getLogger('orb')


class PeersQuerySet(models.QuerySet):

    def summary(self):
        """
        Returns data useful for summarizing available peers

        Performance is largely irrelevant, even with hundreds of
        rows this is little data and run briefly from management
        commands
        """
        if not self:
            return {}
        return {
            "inactive": self.inactive(),
            "queryable": self.queryable(),
            "unqueryable": self.active().unqueryable(),
        }

    def active(self):
        return self.filter(active=True)

    def inactive(self):
        return self.filter(active=False)

    def queryable(self):
        """Returns only peers which can be queried by API"""
        return self.active().filter(api_user__isnull=False, api_key__isnull=False)

    def unqueryable(self):
        """Returns only peers which cannot be queried by API"""
        return self.filter(Q(active=False) | Q(api_user__isnull=True) | Q(api_key__isnull=True))


@python_2_unicode_compatible
class Peer(models.Model):
    """
    A peer ORB node
    """
    name = models.CharField(max_length=100)
    host = models.URLField()
    active = models.BooleanField(default=True)
    api_user = models.CharField(max_length=100, blank=True, null=True)
    api_key = models.CharField(max_length=100, blank=True, null=True)

    peers = PeersQuerySet.as_manager()
    objects = peers

    def __str__(self):
        return self.name

    def is_queryable(self):
        return bool(self.api_key and self.api_user)
    is_queryable.description = "Can the peer be queried?"

    @cached_property
    def client(self):
        return OrbClient(self.host, self.api_user, self.api_key, sleep=1)

    def sync_resources(self, writer=None):
        """
        Interface method to query and sync resources from the peer

        Args:
            writer: optional output writing function

        Returns:
            dictionary of results

        """
        from orb.models import Resource
        log_entry = self.logs.create()
        # Does resource exist locally?
        # If yes - do update?
        # If it was here but was rejected, make it pending
        # If no, create

        def default_writer(value):
            print(value)

        resource_counts = {
            'new_resources': 0,
            'skipped_local_resources': 0,
            'updated_resources': 0,
            'unchanged_resources': 0,
        }

        if writer is None:
            writer = default_writer

        try:
            last_update = self.logs.latest().finished
        except PeerQueryLog.DoesNotExist:
            last_update = None

        filters = {} if last_update is None else {'updated__gte': last_update}

        total_count, resource_list = self.client.list_resources(**filters)

        for count, initial_api_resource in enumerate(resource_list, start=1):

            if initial_api_resource.get('status', '') != Resource.APPROVED:
                writer("Skipping '{}' because it is '{}'".format(
                    initial_api_resource.get('title', ''),
                    initial_api_resource.get('status', ''),
                ))
                continue

            api_resource = self.client.get_resource_by_id(initial_api_resource['id'])

            try:
                local_resource = Resource.resources.get(guid=api_resource['guid'])
            except Resource.DoesNotExist:
                Resource.create_from_api(api_resource, peer=self)
                resource_counts['new_resources'] += 1
                writer("Created a new resource: {}".format(api_resource['title']))
            else:
                if local_resource.is_local():
                    resource_counts['skipped_local_resources'] += 1
                else:
                    was_updated = local_resource.update_from_api(api_resource)
                    if was_updated:
                        resource_counts['updated_resources'] += 1
                    else:
                        resource_counts['unchanged_resources'] += 1

        log_entry.finish(filtered_date=last_update, **resource_counts)

        if resource_counts['new_resources'] or resource_counts['updated_resources']:
            send_peer_sync_notification_email(self, **resource_counts)

        return resource_counts


@python_2_unicode_compatible
class PeerQueryLog(models.Model):
    """
    Model to log when a peer is queried for update and when the update finishes
    """

    created = models.DateTimeField(editable=False, default=now)
    finished = models.DateTimeField(null=True, blank=True, editable=False)
    peer = models.ForeignKey('Peer', related_name='logs',
                             on_delete=models.CASCADE,
                             )
    filtered_date = models.DateTimeField(blank=True, null=True)
    new_resources = models.PositiveIntegerField(null=True)
    skipped_local_resources = models.PositiveIntegerField(null=True)
    updated_resources = models.PositiveIntegerField(null=True)
    unchanged_resources = models.PositiveIntegerField(null=True)

    entries = models.Manager()
    objects = entries

    class Meta:
        get_latest_by = 'finished'

    def __str__(self):
        return "{} - {}".format(self.peer, self.created)

    def finish(self, filtered_date=None, new_resources=0, skipped_local_resources=0,
               updated_resources=0, unchanged_resources=0):
        """
        Interface for updating the completion (finished) time

        Saves the model instance
        """
        self.filtered_date = filtered_date
        self.new_resources = new_resources
        self.skipped_local_resources = skipped_local_resources
        self.updated_resources = updated_resources
        self.unchanged_resources = unchanged_resources
        self.finished = now()
        self.save()
