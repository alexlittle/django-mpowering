from __future__ import unicode_literals

import os
from collections import defaultdict

from django.conf import settings
from django.contrib import messages
from django.core.paginator import EmptyPage, InvalidPage, Paginator
from django.urls import reverse
from django.db.models import Count, Q
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.utils.translation import ugettext_lazy as _
from haystack.query import SearchQuerySet

from orb.forms import AdvancedSearchForm, ResourceRejectForm, ResourceStep1Form, ResourceStep2Form, SearchForm
from orb.models import (Category, Collection, Resource, ResourceCriteria, ResourceFile, ResourceRating, ResourceTag,
                        ResourceURL, ReviewerRole, SearchTracker, Tag, TagOwner, home_resources)
from orb.signals import (resource_file_viewed, resource_submitted, resource_url_viewed, resource_viewed,
                         resource_workflow, search, tag_viewed)
from orb.tags.forms import TagPageForm


def home_view(request):
    topics = []
    organized_topics = defaultdict(list)
    for tag in Tag.tags.public().top_level():
        child_tags = tag.children.values_list('id')
        resource_count = Resource.objects.filter(status=Resource.APPROVED).filter(
            Q(resourcetag__tag__pk__in=child_tags) | Q(resourcetag__tag=tag)).distinct().count()

        for category_slug in ["health-domain"]:
            if tag.category.slug == category_slug:
                organized_topics[category_slug.replace("-", "_")].append({
                    'resource_count': resource_count,
                    'tag': tag,
                })

        topics.append({
            'resource_count': resource_count,
            'tag': tag,
        })

    return render(request, 'orb/home.html', {
        'topics': topics,
        'organized_topics': home_resources(),
        'page_title': _('COVID-19'),
    })


def partner_view(request):
    PARTNERS = ['jhu-ccp', 'digital-campus', 'digital-green',
                'global-health-media-project', 'medical-aid-films', 'zinc-ors']
    partners = Tag.objects.filter(
        category__slug='organisation', slug__in=PARTNERS).order_by('name')
    return render(request, 'orb/partners.html', {'partners': partners})


def tag_view(request, tag_slug):
    """
    Renders a tag detail page.

    Allows the user to paginate resultes and sort by preselected options.

    Args:
        request: HttpRequest
        tag_slug: the identifier for the tag

    Returns:
        Rendered response with a tag's resource list

    """
    tag = get_object_or_404(Tag, slug=tag_slug)
    filter_params = {
        'page': 1,
        'order': TagPageForm.CREATED,
    }

    params_form = TagPageForm(data=request.GET)
    if params_form.is_valid():
        filter_params.update(params_form.cleaned_data)

    order_by = filter_params['order']
    if order_by == TagPageForm.RATING:
        data = Resource.resources.approved().with_ratings(tag).order_by(order_by)
    else:
        data = Resource.resources.approved().for_tag(tag).order_by(order_by)

    paginator = Paginator(data, settings.ORB_PAGINATOR_DEFAULT)

    try:
        resources = paginator.page(filter_params['page'])
    except (EmptyPage, InvalidPage):
        resources = paginator.page(paginator.num_pages)

    show_filter_link = tag.category.slug in [slug for name, slug in settings.ADVANCED_SEARCH_CATEGORIES]

    tag_viewed.send(sender=tag, tag=tag, request=request)

    is_geo_tag = tag.category.name == "Geography"

    return render(request, 'orb/tag.html', {
        'tag': tag,
        'resource_count': paginator.count,
        'page': resources,
        'params_form': params_form,
        'show_filter_link': show_filter_link,
        'is_geo_tag': is_geo_tag,
    })


def upload_instructions_view(request):
    return render(request, 'orb/upload_instructions.html')


def resource_permalink_view(request, id):
    resource = get_object_or_404(Resource, pk=id)
    return resource_view(request, resource.slug)


def resource_view(request, resource_slug):
    resource = get_object_or_404(
        Resource.objects.approved(user=request.user), slug=resource_slug)

    if resource.status == Resource.ARCHIVED:
        messages.error(request, _(
            "This resource has been archived by the COVID-19 Library Content"
            " Review Team, so is not available for users to view"))
    elif resource.status != Resource.APPROVED:
        messages.error(request, _(
            "This resource is not yet approved by the COVID-19 Library Content"
            " Review Team, so is not yet available for all users to view"))

    options_menu = []
    if resource_can_edit(resource, request.user):
        om = {}
        om['title'] = _('Edit')
        om['url'] = reverse('orb_resource_edit', args=[resource.id])
        options_menu.append(om)

    if request.user.is_staff and resource.status == Resource.PENDING:
        om = {}
        om['title'] = _('Reject')
        om['url'] = reverse('orb_resource_reject', args=[resource.id])
        options_menu.append(om)

        om = {}
        om['title'] = _('Approve')
        om['url'] = reverse('orb_resource_approve', args=[resource.id])
        options_menu.append(om)

    resource_viewed.send(sender=resource, resource=resource, request=request)

    user_rating = 0
    if request.user.is_authenticated:
        try:
            user_rating = ResourceRating.objects.get(
                resource=resource, user=request.user).rating
        except ResourceRating.DoesNotExist:
            pass

    # get the collections for this resource
    collections = Collection.objects.filter(
        collectionresource__resource=resource, visibility=Collection.PUBLIC)

    # See if bookmarked
    bookmarks = Collection.objects.filter(collectionresource__resource=resource,
                                          visibility=Collection.PRIVATE, collectionuser__user__id=request.user.id).count()
    if bookmarks > 0:
        bookmarked = True
    else:
        bookmarked = False

    return render(request, 'orb/resource/view.html', {
        'resource': resource,
        'options_menu': options_menu,
        'user_rating': user_rating,
        'collections': collections,
        'bookmarked': bookmarked,
    })


def resource_create_step1_view(request):
    if request.user.is_anonymous:
        return render(request, 'orb/login_required.html', {
            'message': _('You need to be logged in to add a resource.'),
        })

    if request.method == 'POST':
        form = ResourceStep1Form(request.POST, request.FILES, request=request)
        resource_form_set_choices(form)
        if form.is_valid():
            # save resource
            resource = Resource(status=Resource.PENDING,
                                create_user=request.user, update_user=request.user)
            resource.title = form.cleaned_data.get("title")
            resource.description = form.cleaned_data.get("description")
            if form.cleaned_data.get("study_time_number") and form.cleaned_data.get("study_time_unit"):
                resource.study_time_number = form.cleaned_data.get(
                    "study_time_number")
                resource.study_time_unit = form.cleaned_data.get(
                    "study_time_unit")
            if 'image' in request.FILES:
                resource.image = request.FILES["image"]
            resource.attribution = form.cleaned_data.get("attribution")
            resource.save()

            # add organisation(s)/geography and other tags
            resource_add_free_text_tags(
                resource, form.cleaned_data.get('organisations'), request.user, 'organisation')
            resource_add_free_text_tags(
                resource, form.cleaned_data.get('geography'), request.user, 'geography')
            resource_add_free_text_tags(
                resource, form.cleaned_data.get('languages'), request.user, 'language')
            resource_add_free_text_tags(
                resource, form.cleaned_data.get('other_tags'), request.user, 'other')

            # add tags
            resource_add_tags(request, form, resource)

            # see if email needs to be sent
            resource_workflow.send(sender=resource, resource=resource, request=request,
                                   status=Resource.PENDING, notes="")
            resource_submitted.send(sender=resource, resource=resource, request=request)

            # redirect to step 2
            # Redirect after POST
            return HttpResponseRedirect(reverse('orb_resource_create2', args=[resource.id]))

    else:
        if request.user.userprofile.organisation:
            user_org = request.user.userprofile.organisation.name
            initial = {'organisations': user_org, }
        else:
            initial = {}
        form = ResourceStep1Form(initial=initial, request=request)
        resource_form_set_choices(form)

    return render(request, 'orb/resource/create_step1.html', {'form': form})


def resource_create_step2_view(request, id):
    if request.user.is_anonymous:
        # TODO use contrib.messages
        return render(request, 'orb/login_required.html', {
            'message': _('You need to be logged in to add a resource.'),
        })

    resource = get_object_or_404(Resource, pk=id)

    # check if owner of this resource
    if not resource_can_edit(resource, request.user):
        raise Http404()

    if request.method == 'POST':
        form = ResourceStep2Form(request.POST, request.FILES, request=request)

        if form.is_valid():
            title = form.cleaned_data.get("title")
            # add file and url
            if 'file' in request.FILES:
                rf = ResourceFile(
                    resource=resource, create_user=request.user, update_user=request.user)
                rf.file = request.FILES["file"]
                if title:
                    rf.title = title
                rf.save()

            url = form.cleaned_data.get("url")
            if url:
                ru = ResourceURL(
                    resource=resource, create_user=request.user, update_user=request.user)
                ru.url = url
                if title:
                    ru.title = title
                ru.save()

    initial = {}
    form = ResourceStep2Form(initial=initial, request=request)

    resource_files = ResourceFile.objects.filter(resource=resource)
    resource_urls = ResourceURL.objects.filter(resource=resource)

    return render(request, 'orb/resource/create_step2.html', {
        'form': form,
        'resource': resource,
        'resource_files': resource_files,
        'resource_urls': resource_urls,
    })


def resource_create_file_delete_view(request, id, file_id):
    # check ownership
    resource = get_object_or_404(Resource, pk=id)
    if not resource_can_edit(resource, request.user):
        raise Http404()

    try:
        ResourceFile.objects.get(resource=resource, pk=file_id).delete()
    except ResourceFile.DoesNotExist:
        pass

    return HttpResponseRedirect(reverse('orb_resource_create2', args=[id]))


def resource_create_url_delete_view(request, id, url_id):
    # check ownership
    resource = get_object_or_404(Resource, pk=id)
    if not resource_can_edit(resource, request.user):
        raise Http404()

    try:
        ResourceURL.objects.get(resource=resource, pk=url_id).delete()
    except ResourceURL.DoesNotExist:
        pass

    return HttpResponseRedirect(reverse('orb_resource_create2', args=[id]))


def resource_edit_file_delete_view(request, id, file_id):
    # check ownership
    resource = get_object_or_404(Resource, pk=id)
    if not resource_can_edit(resource, request.user):
        raise Http404()

    try:
        ResourceFile.objects.get(resource=resource, pk=file_id).delete()
    except ResourceFile.DoesNotExist:
        pass

    return HttpResponseRedirect(reverse('orb_resource_edit2', args=[id]))


def resource_edit_url_delete_view(request, id, url_id):
    # check ownership
    resource = get_object_or_404(Resource, pk=id)
    if not resource_can_edit(resource, request.user):
        raise Http404()

    try:
        ResourceURL.objects.get(resource=resource, pk=url_id).delete()
    except ResourceURL.DoesNotExist:
        pass

    return HttpResponseRedirect(reverse('orb_resource_edit2', args=[id]))


def resource_create_thanks_view(request, id):
    resource = get_object_or_404(Resource, pk=id)
    if not resource_can_edit(resource, request.user):
        raise Http404()
    return render(request, 'orb/resource/create_thanks.html', {'resource': resource})


def resource_guidelines_view(request):

    criteria = []

    # get the general criteria
    criteria_general = ResourceCriteria.objects.filter(role=None).order_by('order_by')
    obj = {}
    obj['category'] = _("General")
    obj['criteria'] = criteria_general
    criteria.append(obj)

    for k in ReviewerRole.objects.all():
        obj = {}
        cat = ResourceCriteria.objects.filter(role=k).order_by('order_by')
        obj['category'] = k
        obj['criteria'] = cat

        criteria.append(obj)

    return render(request, 'orb/resource/guidelines.html', {'criteria_categories': criteria})


def resource_approve_view(request, id):
    if not request.user.is_staff:
        return HttpResponse(status=401, content="Not Authorized")
    resource = Resource.objects.get(pk=id)
    resource.status = Resource.APPROVED
    resource.save()

    resource_workflow.send(sender=resource, resource=resource,
                           request=request, status=Resource.APPROVED, notes="")
    return render(request, 'orb/resource/status_updated.html', {'resource': resource})


def resource_reject_view(request, id):
    if not request.user.is_staff:
        return HttpResponse(status=401, content="Not Authorized")

    resource = Resource.objects.get(pk=id)

    if request.method == 'POST':
        form = ResourceRejectForm(data=request.POST)
        form.fields['criteria'].choices = [(t.id, t.description) for t in ResourceCriteria.objects.all(
        ).order_by('category_order_by', 'order_by')]

        if form.is_valid():
            resource.status = Resource.REJECTED
            resource.save()
            notes = form.cleaned_data.get("notes")
            criteria = form.cleaned_data.get("criteria")
            resource_workflow.send(sender=resource, resource=resource, request=request,
                                   status=Resource.REJECTED, notes=notes, criteria=criteria)
            return HttpResponseRedirect(reverse('orb_resource_reject_sent', args=[resource.id]))
    else:
        form = ResourceRejectForm()
        form.fields['criteria'].choices = [(t.id, t.description) for t in ResourceCriteria.objects.all(
        ).order_by('category_order_by', 'order_by')]

    return render(request, 'orb/resource/reject_form.html', {
        'resource': resource,
        'form': form,
    })


def resource_reject_sent_view(request, id):
    if not request.user.is_staff:
        return HttpResponse(status=401, content="Not Authorized")

    resource = Resource.objects.get(pk=id)

    return render(request, 'orb/resource/status_updated.html', {'resource': resource, })


def resource_pending_mep_view(request, id):
    if not request.user.is_staff:
        return HttpResponse(status=401, content="Not Authorized")

    resource = Resource.objects.get(pk=id)
    resource.status = Resource.PENDING
    resource.save()

    resource_workflow.send(sender=resource, resource=resource, request=request,
                           status=Resource.PENDING, notes="")
    return render(request, 'orb/resource/status_updated.html', {'resource': resource})


def resource_edit_view(request, resource_id):
    resource = get_object_or_404(Resource, pk=resource_id)
    if not resource_can_edit(resource, request.user):
        raise Http404()

    if request.method == 'POST':
        form = ResourceStep1Form(data=request.POST, files=request.FILES)
        resource_form_set_choices(form)

        if form.is_valid():
            resource.update_user = request.user
            resource.title = form.cleaned_data.get("title")
            resource.description = form.cleaned_data.get("description")
            if form.cleaned_data.get("study_time_number") and form.cleaned_data.get("study_time_unit"):
                resource.study_time_number = form.cleaned_data.get(
                    "study_time_number")
                resource.study_time_unit = form.cleaned_data.get(
                    "study_time_unit")
            resource.attribution = form.cleaned_data.get("attribution")
            resource.save()

            # update image
            image = form.cleaned_data.get("image")

            if image == False:
                resource.image = None
                resource.save()

            if 'image' in request.FILES:
                resource.image = request.FILES["image"]
                resource.save()

            # update tags - remove all current tags first
            ResourceTag.objects.filter(resource=resource).delete()
            resource_add_tags(request, form, resource)
            resource_add_free_text_tags(
                resource, form.cleaned_data.get('organisations'), request.user, 'organisation')
            resource_add_free_text_tags(
                resource, form.cleaned_data.get('geography'), request.user, 'geography')
            resource_add_free_text_tags(
                resource, form.cleaned_data.get('languages'), request.user, 'language')
            resource_add_free_text_tags(
                resource, form.cleaned_data.get('other_tags'), request.user, 'other')

            # All successful - now redirect
            # Redirect after POST
            return HttpResponseRedirect(reverse('orb_resource_edit2', args=[resource.id]))
        else:
            initial = request.POST.copy()
            initial['image'] = resource.image
            files = ResourceFile.objects.filter(resource=resource)[:1]
            if files:
                initial['file'] = files[0].file
            form = ResourceStep1Form(
                initial=initial, data=request.POST, files=request.FILES)
            resource_form_set_choices(form)

    else:
        data = {}
        data['title'] = resource.title
        organisations = Tag.objects.filter(
            category__slug='organisation', resourcetag__resource=resource).values_list('name', flat=True)
        data['organisations'] = ', '.join(organisations)
        data['description'] = resource.description
        data['image'] = resource.image
        data['study_time_number'] = resource.study_time_number
        data['study_time_unit'] = resource.study_time_unit
        data['attribution'] = resource.attribution

        files = ResourceFile.objects.filter(resource=resource)[:1]
        if files:
            data['file'] = files[0].file

        urls = ResourceURL.objects.filter(resource=resource)[:1]
        if urls:
            data['url'] = urls[0].url

        health_topic = Tag.objects.filter(
            category__top_level=True, resourcetag__resource=resource).values_list('id', flat=True)
        data['health_topic'] = health_topic

        resource_type = Tag.objects.filter(
            category__slug='type', resourcetag__resource=resource).values_list('id', flat=True)
        data['resource_type'] = resource_type

        audience = Tag.objects.filter(
            category__slug='audience', resourcetag__resource=resource).values_list('id', flat=True)
        data['audience'] = audience

        geography = Tag.objects.filter(
            category__slug='geography', resourcetag__resource=resource).values_list('name', flat=True)
        data['geography'] = ', '.join(geography)

        languages = Tag.objects.filter(
            category__slug='language', resourcetag__resource=resource).values_list('name', flat=True)
        data['languages'] = ', '.join(languages)

        device = Tag.objects.filter(
            category__slug='device', resourcetag__resource=resource).values_list('id', flat=True)
        data['device'] = device

        license = Tag.objects.filter(
            category__slug='license', resourcetag__resource=resource).values_list('id', flat=True)
        if license:
            data['license'] = license[0]

        other_tags = Tag.objects.filter(
            resourcetag__resource=resource, category__slug='other').values_list('name', flat=True)
        data['other_tags'] = ', '.join(other_tags)

        form = ResourceStep1Form(initial=data)
        resource_form_set_choices(form)

    return render(request, 'orb/resource/edit.html', {'form': form})


def resource_edit_step2_view(request, resource_id):
    if request.user.is_anonymous:
        # TODO use contrib.messages
        return render(request, 'orb/login_required.html', {
            'message': _('You need to be logged in to add a resource.'),
        })

    resource = get_object_or_404(Resource, pk=resource_id)

    # check if owner of this resource
    if not resource_can_edit(resource, request.user):
        raise Http404()

    if request.method == 'POST':
        form = ResourceStep2Form(request.POST, request.FILES, request=request)

        if form.is_valid():
            title = form.cleaned_data.get("title")
            # add file and url
            if 'file' in request.FILES:
                rf = ResourceFile(
                    resource=resource, create_user=request.user, update_user=request.user)
                rf.file = request.FILES["file"]
                if title:
                    rf.title = title
                rf.save()

            url = form.cleaned_data.get("url")
            if url:
                ru = ResourceURL(
                    resource=resource, create_user=request.user, update_user=request.user)
                ru.url = url
                if title:
                    ru.title = title
                ru.save()

    initial = {}
    form = ResourceStep2Form(initial=initial, request=request)

    resource_files = ResourceFile.objects.filter(resource=resource)
    resource_urls = ResourceURL.objects.filter(resource=resource)

    return render(request, 'orb/resource/edit_step2.html', {
        'form': form,
        'resource': resource,
        'resource_files': resource_files,
        'resource_urls': resource_urls,
    })


def resource_edit_thanks_view(request, id):
    resource = get_object_or_404(Resource, pk=id)
    if not resource_can_edit(resource, request.user):
        raise Http404()
    return render(request, 'orb/resource/edit_thanks.html', {'resource': resource})


def search_view(request):

    search_query = request.GET.get('q', '')

    if search_query:
        search_results = SearchQuerySet().filter(content=search_query).models(Resource).values_list('pk', flat=True)
        results = Resource.objects.filter(pk__in=search_results)
    else:
        search_results = []
        results = Resource.objects.none()

    data = {}
    data['q'] = search_query
    form = SearchForm(initial=data)

    paginator = Paginator(results, settings.ORB_PAGINATOR_DEFAULT)
    # Make sure page request is an int. If not, deliver first page.
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    try:
        results = paginator.page(page)
    except (EmptyPage, InvalidPage):
        results = paginator.page(paginator.num_pages)

    if search_query:
        search.send(sender=search_results, query=search_query,
                    no_results=search_results.count(), request=request, page=page)

    return render(request, 'orb/search.html', {
        'form': form,
        'query': search_query,
        'page': results,
        'total_results': paginator.count,
    })


def search_advanced_view(request, tag_id=None):

    if request.method == 'POST':
        form = AdvancedSearchForm(request.POST)
        if form.is_valid():
            urlparams = request.POST.copy()
            # delete these from params as not required
            del urlparams['csrfmiddlewaretoken']
            del urlparams['submit']
            return HttpResponseRedirect(reverse('orb_search_advanced_results') + "?" + urlparams.urlencode())
    else:
        form = AdvancedSearchForm()

    return render(request, 'orb/search_advanced.html', {'form': form})


def search_advanced_results_view(request):

    form = AdvancedSearchForm(request.GET)

    if form.is_valid():
        q = form.cleaned_data.get('q')

        results, filter_tags = form.search()
        if q:
            search_results = SearchQuerySet().filter(content=q).models(Resource).values_list('pk', flat=True)
            results = results.filter(pk__in=search_results)

        paginator = Paginator(results, settings.ORB_PAGINATOR_DEFAULT)
        try:
            page = int(request.GET.get('page', 1))
        except ValueError:
            page = 1

        try:
            resources = paginator.page(page)
        except (EmptyPage, InvalidPage):
            resources = paginator.page(paginator.num_pages)

        search.send(sender=results, query=q, no_results=results.count(),
                    request=request, type=SearchTracker.SEARCH_ADV, page=page)
        license_tags = form.cleaned_data['license']
    else:
        filter_tags = Tag.objects.filter(pk=None)
        license_tags = []
        resources = Resource.objects.filter(pk=None)
        paginator = Paginator(resources, settings.ORB_PAGINATOR_DEFAULT)

    return render(request, 'orb/search_advanced_results.html', {
        'filter_tags': filter_tags,
        'license_tags': license_tags,
        'q': form.cleaned_data.get('q'),
        'page': resources,
        'total_results': paginator.count,
    })


def collection_view(request, collection_slug):
    collection = get_object_or_404(Collection,
        slug=collection_slug, visibility=Collection.PUBLIC)

    data = Resource.objects.filter(collectionresource__collection=collection,
                                   status=Resource.APPROVED).order_by('collectionresource__order_by')

    paginator = Paginator(data, settings.ORB_PAGINATOR_DEFAULT)

    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    try:
        resources = paginator.page(page)
    except (EmptyPage, InvalidPage):
        resources = paginator.page(paginator.num_pages)

    return render(request, 'orb/collection/view.html', {
        'collection': collection,
        'page': resources,
        'total_results': paginator.count,
    })

# Helper functions


def resource_form_set_choices(form):
    form.fields['health_topic'].choices = [(t.id, t.name) for t in Tag.objects.filter(
        category__top_level=True).order_by('order_by', 'name')]
    form.fields['resource_type'].choices = [(t.id, t.name) for t in Tag.objects.filter(
        category__slug='type').order_by('order_by', 'name')]
    form.fields['audience'].choices = [(t.id, t.name) for t in Tag.objects.filter(
        category__slug='audience').order_by('order_by', 'name')]
    form.fields['device'].choices = [(t.id, t.name) for t in Tag.objects.filter(
        category__slug='device').order_by('order_by', 'name')]
    form.fields['license'].choices = [(t.id, t.name) for t in Tag.objects.filter(
        category__slug='license').order_by('order_by', 'name')]
    return form


def advanced_search_form_set_choices(form):
    for name, slug in settings.ADVANCED_SEARCH_CATEGORIES:
        form.fields[name].choices = [(t.id, t.name) for t in Tag.objects.filter(
            category__slug=slug, resourcetag__resource__status=Resource.APPROVED).distinct().order_by('order_by', 'name')]

    form.fields['license'].choices = [
        ('ND', _('Derivatives allowed')), ('NC', _('Commercial use allowed'))]
    return form


def resource_can_edit(resource, user):
    if user.is_staff or user == resource.create_user or user == resource.update_user:
        return True
    else:
        return TagOwner.objects.filter(user__pk=user.id, tag__resourcetag__resource=resource).exists()


def resource_add_free_text_tags(resource, tag_text, user, category_slug):
    """
    Adds tags to a resource based on free text and category slugs

    Args:
        resource: a Resource object
        tag_text: string of text including multiple comma separated tags
        user: the User object to use for the tags
        category_slug: the slug of the related Category

    Returns:
        None

    """
    free_text_tags = [x.strip() for x in tag_text.split(',') if x.strip()]

    category = Category.objects.get(slug=category_slug)

    for tag_name in free_text_tags:
        try:
            tag = Tag.tags.rewrite(False).get(name=tag_name)
        except Tag.DoesNotExist:
            try:
                tag = Tag.tags.get(name=tag_name)
            except Tag.DoesNotExist:
                tag = Tag.tags.create(
                    name=tag_name,
                    category=category,
                    create_user=user,
                    update_user=user,
                )
        ResourceTag.objects.get_or_create(
            tag=tag, resource=resource, defaults={'create_user': user})


def resource_add_tags(request, form, resource):
    """
    Adds structured tags to the resource

    Args:
        request: the HttpRequest
        form: Resource add/edit form that has the tag data
        resource: the resource to add the tags

    Returns:
        None

    """
    tag_categories = ["health_topic", "resource_type", "audience", "device"]
    for tc in tag_categories:
        tag_category = form.cleaned_data.get(tc)
        for ht in tag_category:
            tag = Tag.objects.get(pk=ht)
            ResourceTag.objects.get_or_create(
                tag=tag, resource=resource, defaults={'create_user': request.user})
    # add license
    license = form.cleaned_data.get("license")
    tag = Tag.objects.get(pk=license)
    ResourceTag(tag=tag, resource=resource, create_user=request.user).save()
