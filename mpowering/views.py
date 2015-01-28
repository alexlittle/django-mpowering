
from django.contrib import messages
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.shortcuts import render,render_to_response
from django.template import RequestContext
from django.utils.translation import ugettext as _

from haystack.query import SearchQuerySet

from mpowering.forms import ResourceForm, SearchForm
from mpowering.models import Tag, Resource, Organisation, ResourceURL , Category
from mpowering.models import ResourceFile, ResourceOrganisation, ResourceTag

from mpowering.signals import resource_viewed, resource_url_viewed, resource_file_viewed, search

from PIL import Image


# Create your views here.


def home_view(request):
    topics = Tag.objects.filter(category__slug='health-topic').order_by('order_by')
    return render_to_response('mpowering/home.html',
                              {'topics': topics,},
                              context_instance=RequestContext(request))

def tag_view(request,tag_slug):
    try:
        tag = Tag.objects.get(slug=tag_slug)
    except Tag.DoesNotExist:
        raise Http404()
    resources = Resource.objects.filter(resourcetag__tag=tag, status=Resource.APPROVED)
    return render_to_response('mpowering/tag.html',
                              {'resources': resources,
                               'tag': tag, },
                              context_instance=RequestContext(request))
  
def resource_view(request,resource_slug):
    try:
        resource = Resource.objects.get(slug=resource_slug)
    except Resource.DoesNotExist:
        raise Http404()
    
    if not resource_can_view(resource,request.user):
        raise Http404()
    
    if resource.status != Resource.APPROVED:
        messages.error(request, _(u"This resource is not yet approved by the mPowering Content Review Team, so is not yet available for all users to view"))
    
    options_menu = []
    if resource_can_edit(resource,request.user):
        om = {}
        om['title'] = _(u'Edit')   
        om['url'] = resource.get_edit_url()
        options_menu.append(om)
        
    resource_viewed.send(sender=resource, resource=resource, request=request)
    return render_to_response('mpowering/resource/view.html',
                              {'resource': resource, 
                               'options_menu': options_menu, },
                              context_instance=RequestContext(request))  
    
def resource_create_view(request):
    if request.user.is_anonymous():
        return render_to_response('mpowering/login_required.html',
                              {'message': _(u'You need to be logged in to add a resource.') },
                              context_instance=RequestContext(request))
    if request.method == 'POST':
        form = ResourceForm(request.POST, request.FILES)
        resource_form_set_choices(form)
        if form.is_valid():
            # save resource
            resource = Resource(status = Resource.PENDING, create_user = request.user, update_user = request.user)
            resource.title = form.cleaned_data.get("title")
            resource.description = form.cleaned_data.get("description")
            if request.FILES.has_key('image'):
                resource.image = request.FILES["image"]
            resource.save()
            
            # add organisation(s)
            resource_add_organisations(request, form, resource)
                
            # add file and url
            if request.FILES.has_key('file'):
                rf = ResourceFile(resource=resource, create_user=request.user, update_user=request.user)
                rf.file=request.FILES["file"]
                rf.save()
            
            url = form.cleaned_data.get("url")
            if url:
                ru = ResourceURL(resource=resource, create_user=request.user, update_user=request.user) 
                ru.url = url
                ru.save()
                
            # add tags
            resource_add_tags(request, form, resource)
                
            # redirect to info page
            return HttpResponseRedirect(reverse('mpowering_resource_create_thanks', args=[resource.id])) # Redirect after POST
            
    else:
        form = ResourceForm()
        resource_form_set_choices(form)
        
    return render_to_response('mpowering/resource/create.html',
                              {'form': form, 
                               },
                              context_instance=RequestContext(request))
 
def resource_create_thanks_view(request,id):
    resource = Resource.objects.get(pk=id)
    return render_to_response('mpowering/resource/create_thanks.html',
                              {'resource': resource, 
                               },
                              context_instance=RequestContext(request))
       
def resource_link_view(request, id):
    # TODO check that resource is approved
    try:
        url = ResourceURL.objects.get(pk=id)
        
        if not resource_can_view(url.resource,request.user):
            raise Http404() 
        
        resource_url_viewed.send(sender=url, resource_url=url, request=request)
        return HttpResponseRedirect(url.url)
    except ResourceURL.DoesNotExist:
        raise Http404()
    
def resource_file_view(request, id):
    # TODO check that resource is approved
    try:
        file = ResourceFile.objects.get(pk=id)
        
        if not resource_can_view(file.resource,request.user):
            raise Http404() 
        
        resource_file_viewed.send(sender=file, resource_file=file, request=request)
        response = HttpResponse(file.file, content_type='application/unknown;charset=utf-8')
        response['Content-Disposition'] = "attachment; filename=" + file.filename()
        return response
    except ResourceFile.DoesNotExist:
        raise Http404()
    
    
    return render_to_response('mpowering/resource/file.html',
                              context_instance=RequestContext(request))

def resource_edit_view(request,resource_id):
    resource = Resource.objects.get(pk=resource_id)
    if not resource_can_edit(resource, request.user):
        raise Http404() 

    if request.method == 'POST':
        form = ResourceForm(data = request.POST, files = request.FILES)
        resource_form_set_choices(form)
            
        if form.is_valid():
            resource.update_user = request.user
            resource.title = form.cleaned_data.get("title")
            resource.description = form.cleaned_data.get("description")
            resource.save()
            
            # update organisations
            ResourceOrganisation.objects.filter(resource=resource).delete()
            resource_add_organisations(request, form, resource)
                
            # update image
            image_clear = form.cleaned_data.get("image-clear")
        
            if image_clear:
                resource.image = None
                resource.save()
            
            if request.FILES.has_key('image'):
                resource.image = request.FILES["image"]
                resource.save()
            
            # update file
            
            # update url
            url = form.cleaned_data.get("url")
            # check if resource already had a url or not
            urls = ResourceURL.objects.filter(resource=resource)
            if url:
                if urls:
                    resource_url = urls[0]
                    resource_url.url = url
                    resource_url.update_user = request.user
                    resource_url.save()
                else:
                    resource_url = ResourceURL(resource=resource, create_user=request.user, update_user=request.user) 
                    resource_url.url = url
                    resource_url.save()
            else:
                if urls:
                    urls.delete()
            
            
            # update tags - remove all current tags first
            ResourceTag.objects.filter(resource=resource).delete()
            resource_add_tags(request, form, resource)
        else:
            initial = request.POST
            initial['image'] = resource.image
            form = ResourceForm(initial = initial, data = request.POST, files = request.FILES)
            resource_form_set_choices(form)       
            
            
    else:
        data = {}
        data['title'] = resource.title
        organisations = Organisation.objects.filter(resourceorganisation__resource=resource).values_list('name', flat=True)
        data['organisations'] = ', '.join(organisations)
        data['description'] = resource.description
        data['image'] = resource.image
        
        files = ResourceFile.objects.filter(resource=resource)[:1]
        if files:
            data['file'] = files[0].file
        
        urls = ResourceURL.objects.filter(resource=resource)[:1]
        if urls:
            data['url'] = urls[0].url
            
        health_topic = Tag.objects.filter(category__slug='health-topic', resourcetag__resource=resource).values_list('id',flat=True)
        data['health_topic'] = health_topic
        
        resource_type = Tag.objects.filter(category__slug='type', resourcetag__resource=resource).values_list('id',flat=True)
        data['resource_type'] = resource_type
        
        audience = Tag.objects.filter(category__slug='audience', resourcetag__resource=resource).values_list('id',flat=True)
        data['audience'] = audience
        
        geography = Tag.objects.filter(category__slug='geography', resourcetag__resource=resource).values_list('id',flat=True)
        data['geography'] = geography
        
        device = Tag.objects.filter(category__slug='device', resourcetag__resource=resource).values_list('id',flat=True)
        data['device'] = device
        
        license = Tag.objects.filter(category__slug='license', resourcetag__resource=resource).values_list('id',flat=True)
        if license:
            data['license'] = license[0]
        
        other_tags = Tag.objects.filter(resourcetag__resource=resource, category__slug='other').values_list('name', flat=True)
        data['other_tags'] = ', '.join(other_tags)
        
        form = ResourceForm(initial= data)
        resource_form_set_choices(form )
        
    return render_to_response('mpowering/resource/edit.html',
                              {'form': form, 
                               },
                              context_instance=RequestContext(request))

def search_view(request):
     
    search_query = request.GET.get('q', '')
    
    print search_query
    
    if search_query:
        search_results = SearchQuerySet().filter(content=search_query)
        print search_results
        search.send(sender=search_results, query=search_query, no_results=search_results.count(), request=request)
    else:
        search_results = None
        
    data = {}
    data['q'] = search_query
    form = SearchForm(initial=data)
        
    return render_to_response('mpowering/search.html',
                              {'form': form, 
                               'query': search_query,
                               'search_results': search_results},
                              context_instance=RequestContext(request))
    
    
def resource_thumbnail_view(request, resource_id, size):
    resource= Resource.objects.get(pk=resource_id)
    im = Image.open(resource.image)
    im.thumbnail(size=(size,size))
    response = HttpResponse(content_type="image/jpg")
    im.save(response, "JPEG")
    return response

''' 
Helper functions
'''
def resource_form_set_choices(form):
    form.fields['health_topic'].choices = [(t.id, t.name) for t in Tag.objects.filter(category__slug='health-topic').order_by('order_by')]
    form.fields['resource_type'].choices = [(t.id, t.name) for t in Tag.objects.filter(category__slug='type').order_by('order_by')]
    form.fields['audience'].choices = [(t.id, t.name) for t in Tag.objects.filter(category__slug='audience').order_by('order_by')]
    form.fields['geography'].choices = [(t.id, t.name) for t in Tag.objects.filter(category__slug='geography').order_by('order_by')]
    form.fields['device'].choices = [(t.id, t.name) for t in Tag.objects.filter(category__slug='device').order_by('order_by')]
    form.fields['license'].choices = [(t.id, t.name) for t in Tag.objects.filter(category__slug='license').order_by('order_by')]
    return form 

def resource_can_view(resource, user):
    if user.is_staff or user == resource.create_user or user == resource.update_user:
        return True
    elif resource.status == Resource.APPROVED:
        return True
    else:
        return False

def resource_can_edit(resource,user):
    if user.is_staff or user == resource.create_user or user == resource.update_user:
        return True
    else:
        return False

def resource_add_organisations(request, form, resource):
    organisations = [x.strip() for x in form.cleaned_data.get("organisations").split(',')]
    for o in organisations:
        try:
            organisation = Organisation.objects.get(name = o)
        except Organisation.DoesNotExist:
            organisation = Organisation(name=o, create_user=request.user, update_user=request.user)
            organisation.save()
        ResourceOrganisation(resource=resource, organisation=organisation,create_user=request.user).save()
                  
def resource_add_tags(request, form, resource):
    tag_categories = ["health_topic", "resource_type", "audience", "geography", "device"]
    for tc in tag_categories:
        tag_category = form.cleaned_data.get(tc)
        for ht in tag_category:
            tag = Tag.objects.get(pk=ht)
            ResourceTag(tag=tag, resource=resource, create_user=request.user).save()
    # add license
    license = form.cleaned_data.get("license")
    tag = Tag.objects.get(pk=license)
    ResourceTag(tag=tag, resource= resource, create_user= request.user).save()
            
    # add misc_tags
    other_tags = [x.strip() for x in form.cleaned_data.get("other_tags").split(',')]
    for ot in other_tags:
        if ot:
            try:
                tag = Tag.objects.get(name = ot)
            except Tag.DoesNotExist:
                category = Category.objects.get(slug='other')
                tag = Tag(name =ot, category= category, create_user=request.user, update_user=request.user)
                tag.save()
            ResourceTag(tag=tag, resource= resource, create_user= request.user).save()