"""
Signal receiver function definitions
"""

from __future__ import unicode_literals

import json

from django.dispatch import receiver

from orb.emailer import first_resource, new_resource_submitted, resource_approved, resource_rejected, user_welcome
from orb.lib.search_crawler import is_search_crawler
from orb.models import (Resource, ResourceCriteria, ResourceTracker, ResourceWorkflowTracker, SearchTracker,
                        TagTracker, UserProfile)
from orb.signals import (resource_file_viewed, resource_submitted, resource_url_viewed, resource_viewed,
                         resource_workflow, search, tag_viewed, user_registered)


# TODO add signal silencer option
def create_profile(sender, instance, **kwargs):
    profile, _ = UserProfile.objects.get_or_create(user=instance)


@receiver(user_registered)
def user_registered_callback(sender, **kwargs):
    request = kwargs.get('request')
    user = kwargs.get('user')
    user_welcome(user)
    return


@receiver(resource_viewed)
def resource_viewed_callback(sender, **kwargs):
    request = kwargs.get('request')
    resource = kwargs.get('resource')
    type = kwargs.get('type')
    if is_search_crawler(request.META.get('HTTP_USER_AGENT', 'unknown')):
        return

    if type is None:
        type = ResourceTracker.VIEW

    tracker = ResourceTracker()
    if not request.user.is_anonymous:
        tracker.user = request.user
    tracker.resource = resource
    tracker.ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
    tracker.user_agent = request.META.get('HTTP_USER_AGENT', 'unknown')
    tracker.type = type
    tracker.save()
    return


@receiver(resource_submitted)
def resource_submitted_callback(sender, **kwargs):
    request = kwargs.get('request')
    resource = kwargs.get('instance')
    created = kwargs.get('created')
    if created and resource.is_local():
        new_resource_submitted(request, resource)
    return


@receiver(resource_workflow)
def resource_workflow_callback(sender, **kwargs):
    request = kwargs.get('request')
    resource = kwargs.get('resource')
    status = kwargs.get('status')
    notes = kwargs.get('notes')
    criteria = kwargs.get('criteria')

    email_sent = False
    # if status is pending CRT (i.e new) and owner hasn't submitted before
    # then send email
    if status == Resource.PENDING:
        no_previous_resources = ResourceWorkflowTracker.objects.filter(
            create_user=request.user).count()
        if no_previous_resources == 0:
            first_resource(request.user, resource)
            email_sent = True

    # if approved
    if status == Resource.APPROVED:
        resource_approved(request, resource.create_user, resource)
        email_sent = True

    # if rejected
    if status == Resource.REJECTED:
        resource_rejected(resource.create_user, resource, criteria, notes)
        email_sent = True
        rejection_criteria = ResourceCriteria.objects.filter(
            id__in=criteria).values_list('description', flat=True)
        notes = ", ".join(rejection_criteria) + " : " + notes

    # add a record to workflow tracker
    workflow_tracker = ResourceWorkflowTracker()
    workflow_tracker.resource = resource
    workflow_tracker.create_user = request.user
    workflow_tracker.status = status
    workflow_tracker.owner_email_sent = email_sent
    workflow_tracker.notes = notes
    workflow_tracker.save()

    return


@receiver(resource_url_viewed)
def resource_url_viewed_callback(sender, **kwargs):
    """Tracks each occurance that a resource link is accessed"""
    request = kwargs.pop('request')
    resource_url = kwargs.pop('resource_url')
    _ = kwargs.pop('signal')

    if is_search_crawler(request.META.get('HTTP_USER_AGENT', 'unknown')):
        return

    ResourceTracker.objects.create(
        user=None if request.user.is_anonymous else request.user,
        resource_url=resource_url,
        resource = resource_url.resource,
        ip=request.META.get('REMOTE_ADDR', '0.0.0.0'),
        user_agent=request.META.get('HTTP_USER_AGENT', 'unknown'),
        type=ResourceTracker.VIEW,
        **kwargs
    )
    return


@receiver(resource_file_viewed)
def resource_file_viewed_callback(sender, **kwargs):
    """Tracks each occurance that a resource file is downloaded"""
    request = kwargs.pop('request')
    resource_file = kwargs.pop('resource_file')
    _ = kwargs.pop('signal')

    if is_search_crawler(request.META.get('HTTP_USER_AGENT', 'unknown')):
        return

    ResourceTracker.objects.create(
        user=None if request.user.is_anonymous else request.user,
        resource_file=resource_file,
        resource = resource_file.resource,
        ip=request.META.get('REMOTE_ADDR', '0.0.0.0'),
        user_agent=request.META.get('HTTP_USER_AGENT', 'unknown'),
        type=ResourceTracker.VIEW,
        **kwargs
    )
    return


@receiver(tag_viewed)
def tag_viewed_callback(sender, **kwargs):
    request = kwargs.get('request')
    tag = kwargs.get('tag')
    type = kwargs.get('type', TagTracker.VIEW)
    data = kwargs.get('data', '')

    if is_search_crawler(request.META.get('HTTP_USER_AGENT', 'unknown')):
        return

    tracker = TagTracker()
    if not request.user.is_anonymous:
        tracker.user = request.user
    tracker.tag = tag
    tracker.ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
    tracker.user_agent = request.META.get('HTTP_USER_AGENT', 'unknown')
    tracker.type = type
    tracker.extra_data = data
    tracker.save()
    return


@receiver(search)
def search_callback(sender, **kwargs):
    request = kwargs.get('request')
    query = kwargs.get('query')
    no_results = kwargs.get('no_results')
    type = kwargs.get('type', SearchTracker.SEARCH)
    page = kwargs.get('page', 1)

    if is_search_crawler(request.META.get('HTTP_USER_AGENT', 'unknown')):
        return

    if query is None or query == '':
        return

    extra_data = {
        'page': page
    }
    tracker = SearchTracker()
    if not request.user.is_anonymous:
        tracker.user = request.user
    tracker.query = query
    tracker.no_results = no_results
    tracker.ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
    tracker.user_agent = request.META.get('HTTP_USER_AGENT', 'unknown')
    tracker.type = type
    tracker.extra_data = json.dumps(extra_data)
    tracker.save()
    return
