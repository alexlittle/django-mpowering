from __future__ import unicode_literals

import re

from django.conf.urls import url
from django.core.paginator import InvalidPage, Paginator
from django.urls import reverse
from django.http.response import Http404
from django.utils.html import strip_tags
from haystack.query import SearchQuerySet
from tastypie import fields
from tastypie.authentication import ApiKeyAuthentication, MultiAuthentication, SessionAuthentication
from tastypie.constants import ALL
from tastypie.exceptions import Unauthorized
from tastypie.resources import ModelResource
from tastypie.throttle import CacheDBThrottle
from tastypie.utils import trailing_slash

from orb.api.authorization import ORBAuthorization, ORBResourceAuthorization, ORBResourceTagAuthorization
from orb.api.error_codes import *
from orb.api.exceptions import ORBAPIBadRequest
from orb.api.serializers import PrettyJSONSerializer, ResourceSerializer
from orb.models import (Category, Resource, ResourceFile, ResourceTag, ResourceTracker, ResourceURL, SearchTracker,
                        Tag, User)
from orb.signals import resource_viewed, search
from orb.views import resource_can_edit


class TagBase(object):
    """
    Mixin class for orb.Tag resources
    """

    def obj_get_list(self, bundle, **kwargs):
        """
        Get a list of available tags that have associated resources

        Explicitly excludes items from the list that do not have an
        associated resource. In effect two different base querysets
        should be employed, 'all' and 'active', for list and detail
        API views, respectively. A Resource can only have one base
        queryset however. Further, filter kwargs must refer to
        *Resource fields* and not to *queryset fields* which precludes
        sending queryset filter arguments in the **kwargs parameter.

        Args:
            bundle: the Tastypie data bundle
            **kwargs: any filtering kwargs

        Returns:
            A limited Tag queryset

        """
        return super(TagBase, self).obj_get_list(
            bundle, **kwargs).exclude(resourcetag__isnull=True)


class ResourceResource(ModelResource):
    """
    To get, post and pushing resources
    """
    files = fields.ToManyField('orb.api.resources.ResourceFileResource', 'resourcefile_set',
                               related_name='resource', full=True, null=True, use_in='detail')
    urls = fields.ToManyField('orb.api.resources.ResourceURLResource', 'resourceurl_set',
                              related_name='resource', full=True, null=True, use_in='detail')
    tags = fields.ToManyField('orb.api.resources.ResourceTagResource', 'resourcetag_set',
                              related_name='resource', full=True, null=True, use_in='detail')
    url = fields.CharField(readonly=True)
    source_name = fields.CharField()
    source_host = fields.CharField()
    source_url = fields.CharField()
    languages = fields.ListField(readonly=True, default=[])

    class Meta:
        queryset = Resource.objects.all()
        resource_name = 'resource'
        excludes = ['source_peer']
        allowed_methods = ['get', 'post', 'put']
        authentication = MultiAuthentication(ApiKeyAuthentication(), SessionAuthentication())
        authorization = ORBResourceAuthorization()
        serializer = ResourceSerializer()
        always_return_data = True
        include_resource_uri = True
        throttle = CacheDBThrottle(throttle_at=1000, timeframe=3600)
        ordering = ['update_date']
        filtering = {
            'update_date': ['lte', 'gte'],  # `exact` would imply a timestamp, not date comparison
            'status': ['exact'],
        }

    def get_object_list(self, request):
        return Resource.objects.approved(request.user)

    def dehydrate_image(self, bundle):
        if bundle.obj.image:
            return bundle.request.build_absolute_uri(settings.MEDIA_URL + bundle.obj.image.name)
        else:
            return None

    def dehydrate_url(self, bundle):
        url = bundle.request.build_absolute_uri(
            reverse('orb_resource', args=[bundle.obj.slug]))
        return url

    def dehydrate_languages(self, bundle):
        """Returns a list of languages the resource is available in"""
        return bundle.obj.available_languages()

    def dehydrate_source_url(self, bundle):
        """Returns the *original* URL of the resource"""
        if bundle.obj.is_local():
            return self.dehydrate_url(bundle)
        return bundle.obj.source_url

    def dehydrate_source_name(self, bundle):
        if bundle.obj.is_local():
            return None
        return bundle.obj.source_name

    def dehydrate_source_host(self, bundle):
        if bundle.obj.is_local():
            return None
        return bundle.obj.source_host

    def authorized_read_detail(self, object_list, bundle):
        # add to ResourceTracker
        if bundle.obj.id:
            resource_viewed.send(sender=bundle.obj, resource=bundle.obj,
                                 request=bundle.request, type=ResourceTracker.VIEW_API)

    def prepend_urls(self):
        """
        for implementing a search API
        """
        return [
            url(r"^(?P<resource_name>%s)/search%s$" % (self._meta.resource_name,
                                                       trailing_slash()), self.wrap_view('get_search'), name="api_get_search"),
        ]

    def get_search(self, request, **kwargs):
        self.method_check(request, allowed=['get'])
        self.is_authenticated(request)
        self.throttle_check(request)

        q = request.GET.get('q', '')
        page_no = int(request.GET.get('page', 1))
        if q == '':
            raise ORBAPIBadRequest(ERROR_CODE_SEARCH_NO_QUERY)

        # Allow basic search without Solr based on local configuration
        if getattr(settings, 'SEARCH_DB', False):
            sqs = Resource.resources.approved().text_search(q)
        else:
            sqs = SearchQuerySet().models(Resource).load_all().auto_query(q)
        paginator = Paginator(sqs, 20)

        try:
            page = paginator.page(page_no)
        except InvalidPage:
            raise Http404("Sorry, no results on that page.")

        objects = []

        for result in page.object_list:
            if result:
                if getattr(settings, 'SEARCH_DB', False):
                    # Search performed directly against database
                    bundle = self.build_bundle(obj=result, request=request)
                else:
                    # Search performed against search engine
                    bundle = self.build_bundle(obj=result.object, request=request)
                bundle = self.full_dehydrate(bundle)
                objects.append(bundle)

        object_list = {
            'objects': objects,
        }

        search.send(sender=sqs, query=q, no_results=sqs.count(),
                    request=request, page=page_no, type=SearchTracker.SEARCH_API)

        self.log_throttled_access(request)
        return self.create_response(request, object_list)

    def hydrate(self, bundle, request=None):
        bundle.obj.create_user_id = bundle.request.user.id
        bundle.obj.update_user_id = bundle.request.user.id
        if 'status' in bundle.data:
            del bundle.obj.status
            del bundle.data['status']

        # check required fields
        if 'title' not in bundle.data or bundle.data['title'].strip() == '':
            raise ORBAPIBadRequest(ERROR_CODE_RESOURCE_NO_TITLE)

        if 'description' not in bundle.data or bundle.data['description'].strip() == '':
            raise ORBAPIBadRequest(ERROR_CODE_RESOURCE_NO_DESCRIPTION)

        no_words = len(strip_tags(bundle.data['description']).split(' '))
        if no_words > settings.ORB_RESOURCE_DESCRIPTION_MAX_WORDS:
            raise ORBAPIBadRequest(ERROR_CODE_RESOURCE_DESCRIPTION_TOO_LONG)

        request_method = bundle.request.META['REQUEST_METHOD']

        # check that resource doesn't already exist for this user
        if request_method.lower() != 'put':
            try:
                resource = Resource.objects.get(
                    create_user=bundle.request.user, title=bundle.data['title'])
                raise ORBAPIBadRequest(
                    ERROR_CODE_RESOURCE_EXISTS, pk=resource.id)
            except Resource.DoesNotExist:
                pass

        return bundle


class ResourceFileResource(ModelResource):

    file_extension = fields.CharField(readonly=True)
    is_embeddable = fields.BooleanField(readonly=True)

    class Meta:
        queryset = ResourceFile.objects.all()
        resource_name = 'resourcefile'
        allowed_methods = ['get', 'delete']
        excludes = ['create_date', 'update_date', 'image', 'file_full_text']
        authentication = ApiKeyAuthentication()
        authorization = ORBAuthorization()
        serializer = PrettyJSONSerializer()
        always_return_data = True
        include_resource_uri = True

    def dehydrate_is_embeddable(self, bundle):
        """Returns whether this file is considered embeddable or not"""
        return bundle.obj.is_embeddable

    def dehydrate_file_extension(self, bundle):
        """Returns the parsed file extension"""
        return bundle.obj.file_extension

    def dehydrate_file(self, bundle):
        if bundle.obj.file:
            return bundle.request.build_absolute_uri(settings.MEDIA_URL + bundle.obj.file.name)
        else:
            return None


class ResourceURLResource(ModelResource):

    class Meta:
        queryset = ResourceURL.objects.all()
        resource_name = 'resourceurl'
        allowed_methods = ['get', 'post', 'delete']
        excludes = ['create_date', 'update_date', 'image']
        authentication = ApiKeyAuthentication()
        authorization = ORBAuthorization()
        serializer = PrettyJSONSerializer()
        always_return_data = True
        include_resource_uri = True

    def get_object_list(self, request):
        return ResourceURL.objects.approved(request.user)

    def hydrate(self, bundle, request=None):
        # check that user has permissions on the resource
        resource = Resource.objects.get(pk=bundle.data['resource_id'])
        user = User.objects.get(pk=bundle.request.user.id)
        if not resource_can_edit(resource, user):
            raise Unauthorized("You do not have edit access for this resource")

        bundle.obj.create_user_id = bundle.request.user.id
        bundle.obj.update_user_id = bundle.request.user.id
        bundle.obj.resource_id = bundle.data['resource_id']

        if 'file_size' not in bundle.data:
            bundle.obj.file_size = 0

        return bundle


class ResourceTagResource(ModelResource):
    tag = fields.ToOneField('orb.api.resources.TagResource', 'tag', full=True)

    class Meta:
        queryset = ResourceTag.objects.all()
        resource_name = 'resourcetag'
        allowed_methods = ['get', 'post', 'delete']
        include_resource_uri = False
        authentication = ApiKeyAuthentication()
        authorization = ORBResourceTagAuthorization()
        serializer = PrettyJSONSerializer()
        always_return_data = True
        include_resource_uri = True

    def get_object_list(self, request):
        return ResourceTag.objects.approved(request.user)

    def hydrate(self, bundle, request=None):

        if 'resource_id' not in bundle.data or not bundle.data['resource_id']:
            raise ORBAPIBadRequest(ERROR_CODE_RESOURCETAG_NO_RESOURCE)

        if 'tag_id' not in bundle.data or not bundle.data['tag_id']:
            raise ORBAPIBadRequest(ERROR_CODE_RESOURCETAG_NO_TAG)

        # check resource exists
        try:
            resource = Resource.objects.get(pk=bundle.data['resource_id'])
        except Resource.DoesNotExist:
            raise ORBAPIBadRequest(ERROR_CODE_RESOURCE_DOES_NOT_EXIST)

        # check tag exists
        try:
            tag = Tag.objects.get(pk=bundle.data['tag_id'])
        except Tag.DoesNotExist:
            raise ORBAPIBadRequest(ERROR_CODE_TAG_DOES_NOT_EXIST)

        # check that user has permissions on the resource
        user = User.objects.get(pk=bundle.request.user.id)
        if not resource_can_edit(resource, user):
            raise Unauthorized("You do not have edit access for this resource")

        # check that tag not already added to resource
        resource_tags = ResourceTag.objects.filter(
            resource=resource, tag=tag).count()
        if resource_tags != 0:
            raise ORBAPIBadRequest(ERROR_CODE_RESOURCETAG_EXISTS)

        bundle.obj.create_user_id = bundle.request.user.id
        bundle.obj.resource_id = bundle.data['resource_id']
        bundle.obj.tag_id = bundle.data['tag_id']
        return bundle


class TagResource(TagBase, ModelResource):
    url = fields.CharField(readonly=True)
    category = fields.CharField(attribute="category")

    class Meta:
        queryset = Tag.objects.all()
        resource_name = 'tag'
        allowed_methods = ['get', 'post']
        excludes = ['contact_email', 'create_date', 'order_by', 'external_url', 'update_date', 'slug']
        authentication = ApiKeyAuthentication()
        authorization = ORBAuthorization()
        serializer = PrettyJSONSerializer()
        always_return_data = True
        include_resource_uri = True
        filtering = {
            "category": ('exact',),
            "name": ALL,
        }

    def build_filters(self, filters=None, **kwargs):
        """
        Creates additional filters for a querylist of Tag resources

        Args:
            filters: QueryDict of all URL param based filters

        Returns:
            dict of queryset filters

        """
        if filters is None:
            filters = {}

        orm_filters = super(TagResource, self).build_filters(filters)

        # What's wanted is in an iexact search but for the sake of the API
        # filter parameters it needs to be configured as an exact search
        if "category" in filters:
            orm_filters["category__name__iexact"] = filters["category"]
            del orm_filters["category__exact"]

        return orm_filters

    def dehydrate_category(self, bundle):
        """Return the name of the tag's category"""
        return bundle.obj.category.name

    def dehydrate_url(self, bundle):
        url = bundle.request.build_absolute_uri(
            reverse('orb_tags', args=[bundle.obj.slug]))
        return url

    def dehydrate_image(self, bundle):
        if bundle.obj.image:
            return bundle.request.build_absolute_uri(settings.MEDIA_URL + bundle.obj.image.name)
        else:
            return None

    def dehydrate(self, bundle):
        for field in Category.api_translation_fields():
            field_name = field.replace('name', 'category')
            bundle.data[field_name] = getattr(bundle.obj.category, field)
        return bundle

    def hydrate(self, bundle, request=None):

        # check not empty
        if bundle.data['name'].strip() == '':
            raise ORBAPIBadRequest(ERROR_CODE_TAG_EMPTY)

        # check not all non-word chars
        regex = re.compile('[,\.!?"\']')
        if regex.sub('', bundle.data['name'].strip()) == '':
            raise ORBAPIBadRequest(ERROR_CODE_TAG_EMPTY)

        # check tag doesn't already exist
        try:
            tag = Tag.objects.get(name=bundle.data['name'])
            tr = TagResource()
            bundle = tr.build_bundle(obj=tag, request=request)
            raise ORBAPIBadRequest(ERROR_CODE_TAG_EXISTS)
        except Tag.DoesNotExist:
            pass

        category = Category.objects.get(slug='other')
        bundle.obj.create_user_id = bundle.request.user.id
        bundle.obj.update_user_id = bundle.request.user.id
        bundle.obj.category_id = category.id
        return bundle


class TagsResource(TagBase, ModelResource):
    resources = fields.ToManyField('orb.api.resources.TagsResourceResource',
                                   'resourcetag_set', full=True, null=True, use_in='detail')
    url = fields.CharField(readonly=True)
    category = fields.CharField(attribute="category")

    class Meta:
        queryset = Tag.objects.all()
        resource_name = 'tags'
        allowed_methods = ['get']
        fields = ['id', 'name', 'image']
        authentication = ApiKeyAuthentication()
        authorization = ORBAuthorization()
        serializer = PrettyJSONSerializer()
        always_return_data = True
        include_resource_uri = True
        filtering = {
            "category": ('exact',),
            "name": ALL,
        }

    def build_filters(self, filters=None, **kwargs):
        """
        Creates additional filters for a querylist of Tag resources

        Args:
            filters: QueryDict of all URL param based filters

        Returns:
            dict of queryset filters

        """
        if filters is None:
            filters = {}

        orm_filters = super(TagsResource, self).build_filters(filters)

        # What's wanted is in an iexact search but for the sake of the API
        # filter parameters it needs to be configured as an exact search
        if "category" in filters:
            orm_filters["category__name__iexact"] = filters["category"]
            del orm_filters["category__exact"]

        return orm_filters

    def dehydrate_category(self, bundle):
        """Return the name of the tag's category"""
        return bundle.obj.category.name

    def dehydrate_url(self, bundle):
        url = bundle.request.build_absolute_uri(
            reverse('orb_tags', args=[bundle.obj.slug]))
        return url

    def dehydrate_image(self, bundle):
        if bundle.obj.image:
            return bundle.request.build_absolute_uri(settings.MEDIA_URL + bundle.obj.image.name)
        else:
            return None


class TagsResourceResource(ModelResource):
    resource = fields.ToOneField(
        'orb.api.resources.ResourceResource', 'resource', full=True)

    class Meta:
        queryset = ResourceTag.objects.filter(
            resource__status=Resource.APPROVED)
        resource_name = 'tagsresource'
        allowed_methods = ['get']
        authentication = ApiKeyAuthentication()
        authorization = ORBResourceTagAuthorization()
        serializer = PrettyJSONSerializer()
        always_return_data = True
        include_resource_uri = True


class CategoryResource(ModelResource):

    class Meta:
        queryset = Category.objects.all()
        resource_name = 'category'
        allowed_methods = ['get']
        authentication = ApiKeyAuthentication()
        authorization = ORBAuthorization()
        serializer = PrettyJSONSerializer()
        always_return_data = True
        include_resource_uri = True
