
from __future__ import unicode_literals

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from tastypie.authentication import ApiKeyAuthentication

from orb.api.error_codes import *
from orb.models import Resource, ResourceFile


@csrf_exempt
def image_view(request):

    if request.method != 'POST':
        return HttpResponse(status=HTML_METHOD_NOT_ALLOWED)

    auth = ApiKeyAuthentication()
    auth_result = auth.is_authenticated(request)
    if auth_result == False:
        return HttpResponse(status=HTML_UNAUTHORIZED)
    elif auth_result != True:
        return auth_result

    required_params = ['resource_id']

    for r in required_params:
        if r not in request.POST:
            return HttpResponse(status=HTML_BADREQUEST, content='{ "error": "No ' + r + ' provided"}')

    if 'image_file' not in request.FILES:
        return HttpResponse(status=HTML_BADREQUEST, content='{ "error": "No image file provided"}')

    # check owner of resource
    resource_id = request.POST['resource_id']
    try:
        resource = Resource.objects.get(
            create_user=request.user, pk=resource_id)
    except Resource.DoesNotExist:
        return HttpResponse(status=HTML_UNAUTHORIZED)

    # handle file upload
    resource.image = request.FILES['image_file']
    resource.save()

    return HttpResponse(status=HTML_CREATED)


@csrf_exempt
def file_view(request):
    if request.method != 'POST':
        return HttpResponse(status=HTML_METHOD_NOT_ALLOWED)

    auth = ApiKeyAuthentication()
    auth_result = auth.is_authenticated(request)
    if auth_result == False:
        return HttpResponse(status=HTML_UNAUTHORIZED)
    elif auth_result != True:
        return auth_result

    required_params = ['resource_id', 'title', 'description', 'order_by']

    for r in required_params:
        if r not in request.POST:
            return HttpResponse(status=HTML_BADREQUEST, content='{ "error": "No ' + r + ' provided"}')

    if 'resource_file' not in request.FILES:
        return HttpResponse(status=HTML_BADREQUEST, content='{ "error": "No resource file provided"}')

    # check owner of resource
    resource_id = request.POST['resource_id']
    try:
        resource = Resource.objects.get(
            create_user=request.user, pk=resource_id)
    except Resource.DoesNotExist:
        return HttpResponse(status=HTML_UNAUTHORIZED)

    rf = ResourceFile()
    rf.title = request.POST['title']
    rf.resource = resource
    rf.create_user = request.user
    rf.update_user = request.user
    rf.file = request.FILES['resource_file']
    rf.description = request.POST['description']
    rf.order_by = request.POST['order_by']
    rf.save()

    return HttpResponse(status=HTML_CREATED)
