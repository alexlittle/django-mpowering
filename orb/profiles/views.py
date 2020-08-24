from __future__ import unicode_literals

import hashlib
import urllib

from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.urls import reverse
from django.db.models import Q
from django.forms.models import model_to_dict
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.utils.translation import ugettext_lazy as _
from django.views.generic import FormView
from tastypie.models import ApiKey

from orb.emailer import password_reset
from orb.models import (Category, Collection, CollectionUser, Resource, ResourceFile, ResourceRating, ResourceTracker,
                        ResourceURL, SearchTracker, Tag, TagTracker, UserProfile)
from orb.profiles.forms import DeleteProfileForm, LoginForm, ProfileForm, RegisterForm, ResetForm
from orb.signals import user_registered


def login_view(request):
    username = password = ''

    # if already logged in
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse('orb_home'))

    if request.POST:
        form = LoginForm(request.POST)
        username = request.POST.get('username')
        password = request.POST.get('password')
        next = request.POST.get('next')
        user = authenticate(username=username, password=password)
        if user is not None and user.is_active:
            login(request, user)
            return redirect(next) if next else redirect(reverse('orb_home'))
    else:
        form = LoginForm(initial={'next': request.GET.get('next'), })

    return render(request, 'orb/form.html', {'username': username, 'form': form, 'title': _('Login')})


class RegistrationView(FormView):
    template_name = 'orb/form.html'
    form_class = RegisterForm
    initial = {'mailing': True}

    def get_initial(self):
        initial = self.initial.copy()
        initial.update({'next': self.request.GET.get('next', '')})
        return initial

    def get_form_kwargs(self):
        kwargs = super(RegistrationView, self).get_form_kwargs()
        print(kwargs)
        return kwargs

    def get_success_url(self, form):
        return form.cleaned_data['next'] if form.cleaned_data.get('next') else reverse('profile_register_thanks')

    def get_context_data(self, **kwargs):
        context = super(RegistrationView, self).get_context_data(**kwargs)
        context['title'] = _('Register')
        return context

    def form_valid(self, form):
        user_profile = form.save_profile()
        user_registered.send(sender=user_profile.user, user=user_profile.user, request=self.request)

        authd_user= form.authenticate_user()
        if authd_user and authd_user.is_active:
            login(self.request, authd_user)

        return redirect(self.get_success_url(form))


def reset(request):
    if request.method == 'POST':  # if form submitted...
        form = ResetForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            try:
                user = User.objects.get(username__exact=username)
            except User.DoesNotExist:
                user = User.objects.get(email__exact=username)
            newpass = User.objects.make_random_password(length=8)
            user.set_password(newpass)
            user.save()

            password_reset(user, newpass)

            return HttpResponseRedirect('sent')
    else:
        form = ResetForm()  # An unbound form

    return render(request, 'orb/form.html', {'form': form, 'title': _('Reset password')})


@login_required
def edit(request):
    key = ApiKey.objects.get(user__id=request.user.id)
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES)
        build_form_options(form, blank_options=False)
        if form.is_valid():
            # update basic data
            email = form.cleaned_data.get("email")
            first_name = form.cleaned_data.get("first_name")
            last_name = form.cleaned_data.get("last_name")
            request.user.email = email
            request.user.first_name = first_name
            request.user.last_name = last_name
            request.user.save()

            try:
                user_profile = UserProfile.objects.get(user=request.user)
            except UserProfile.DoesNotExist:
                user_profile = UserProfile()
                user_profile.user = request.user

            if 'photo' in request.FILES:
                user_profile.photo = request.FILES["photo"]

            if form.cleaned_data.get("organisation").strip() != '':
                category = Category.objects.get(slug='organisation')
                try:
                    organisation = Tag.objects.get(
                        name=form.cleaned_data.get("organisation"), category=category)
                except Tag.DoesNotExist:
                    organisation = Tag()
                    organisation.name = form.cleaned_data.get("organisation")
                    organisation.category = category
                    organisation.create_user = request.user
                    organisation.update_user = request.user
                    organisation.save()

                user_profile.organisation = organisation

            if form.cleaned_data.get("role") != '0':
                role = Tag.objects.get(pk=form.cleaned_data.get("role"))
                user_profile.role = role
            else:
                user_profile.role = None
            user_profile.role_other = form.cleaned_data.get("role_other")
            user_profile.gender = form.cleaned_data.get("gender")
            user_profile.age_range = form.cleaned_data.get("age_range")
            user_profile.mailing = form.cleaned_data.get("mailing")
            user_profile.website = form.cleaned_data.get("website")
            user_profile.twitter = form.cleaned_data.get("twitter")
            user_profile.about = form.cleaned_data.get("about")
            user_profile.save()

            messages.success(request, _("Profile updated"))

            # if password should be changed
            password = form.cleaned_data.get("password")
            if password:
                request.user.set_password(password)
                request.user.save()
                messages.success(request, _("Password updated"))
    else:
        try:
            user_profile = UserProfile.objects.get(user=request.user)
        except UserProfile.DoesNotExist:
            user_profile = UserProfile()

        if user_profile.role is not None:
            role = user_profile.role.id
        else:
            role = 0
        form = ProfileForm(initial={'username': request.user.username,
                                    'email': request.user.email,
                                    'first_name': request.user.first_name,
                                    'last_name': request.user.last_name,
                                    'api_key': key.key,
                                    'organisation': user_profile.organisation,
                                    'role': role,
                                    'role_other': user_profile.role_other,
                                    'age_range': user_profile.age_range,
                                    'gender': user_profile.gender,
                                    'mailing': user_profile.mailing,
                                    'about': user_profile.about,
                                    'website': user_profile.website,
                                    'twitter': user_profile.twitter,
                                    'photo': user_profile.photo})
        build_form_options(form, blank_options=False)

    return render(request, 'orb/profile/edit.html', {'form': form, })

@login_required
def view_profile(request, id):
    try:
        user = User.objects.get(pk=id)
    except User.DoesNotExist:
        raise Http404()

    gravatar_url = "https://www.gravatar.com/avatar.php?"
    gravatar_url += urllib.urlencode({
        'gravatar_id': hashlib.md5(user.email).hexdigest(),
        'size': 64
    })

    return render(request, 'orb/profile/view.html', {'viewuser': user, 'gravatar_url': gravatar_url})

@login_required
def view_my_profile(request):
    try:
        user = User.objects.get(pk=request.user.id)
        return view_profile(request, user.id)
    except User.DoesNotExist:
        raise Http404()

@login_required
def view_my_ratings(request):
    try:
        user = User.objects.get(pk=request.user.id)
    except User.DoesNotExist:
        raise Http404()

    ratings = ResourceRating.objects.filter(
        resource__status=Resource.APPROVED, user=user).order_by('resource__title')
    return render(request, 'orb/profile/rated.html', {'ratings': ratings})

@login_required
def view_my_bookmarks(request):
    try:
        user = User.objects.get(pk=request.user.id)
    except User.DoesNotExist:
        raise Http404()

    bookmarks = Resource.objects.filter(status=Resource.APPROVED, collectionresource__collection__visibility=Collection.PRIVATE,
                                        collectionresource__collection__collectionuser__user=user).order_by('title')
    return render(request, 'orb/profile/bookmarks.html', {'bookmarks': bookmarks})

@login_required
def export_data(request):
    '''
    '''
    resources = Resource.objects.filter(Q(create_user=request.user) | Q(update_user=request.user)).order_by('-create_date')
    collections = Collection.objects.filter(collectionuser__user=request.user).order_by('-create_date')
    resource_trackers = ResourceTracker.objects.filter(user=request.user).order_by('-access_date')
    tag_trackers = TagTracker.objects.filter(user=request.user).order_by('-access_date')
    search_trackers = SearchTracker.objects.filter(user=request.user).order_by('-access_date')
    ratings = ResourceRating.objects.filter(user=request.user).order_by('-create_date')

    return render(request, 'orb/profile/export.html',
                  {'userrecord': model_to_dict(request.user, fields=[field.name for field in request.user._meta.fields]),
                   'userprofile': model_to_dict(request.user.userprofile, fields=[field.name for field in request.user.userprofile._meta.fields]),
                   'organisation': request.user.userprofile.organisation.name,
                   'resources': resources,
                   'collections': collections,
                   'resource_trackers': resource_trackers,
                   'tag_trackers': tag_trackers,
                   'search_trackers': search_trackers,
                   'ratings': ratings})



@login_required
def delete_account(request):
    resources_count = Resource.objects.filter(create_user=request.user).count()

    if request.method == 'POST':
        form = DeleteProfileForm(resources_count, request.POST)
        if form.is_valid():

            # ratings
            ResourceRating.objects.filter(user=request.user).delete()

            # search trackers
            SearchTracker.objects.filter(user=request.user).delete()

            # tag trackers
            TagTracker.objects.filter(user=request.user).delete()

            # resource trackers
            ResourceTracker.objects.filter(user=request.user).delete()

            # collections
            CollectionUser.objects.filter(user=request.user).delete()

            if form.cleaned_data.get("delete_resources"):
                # resources
                Resource.objects.filter(create_user=request.user).delete()
                # resource_urls
                ResourceURL.objects.filter(create_user=request.user).delete()
                # resource_files
                ResourceFile.objects.filter(create_user=request.user).delete()

            # user
            u = User.objects.get(pk=request.user.id)
            u.delete()

            return HttpResponseRedirect(reverse('profile_delete_account_complete'))
    else:
        form = DeleteProfileForm(resources_count, initial={'username':request.user.username},)

    return render(request, 'orb/profile/delete.html',
                  {'form': form })


def delete_account_complete(request):
    return render(request, 'orb/profile/delete_complete.html')

# Helper Methods

def build_form_options(form, blank_options=True):
    # roles
    form.fields['role'].choices = [('0', '--')]
    for t in Tag.objects.filter(category__slug='audience').order_by('order_by', 'name'):
        form.fields['role'].choices.append((t.id, t.name))

    if blank_options == True:
        form.fields['age_range'].choices = [('0', '--')]
        form.fields['gender'].choices = [('0', '--')]
    else:
        form.fields['age_range'].choices = []
        form.fields['gender'].choices = []

    # age range
    for x, y in UserProfile.AGE_RANGE:
        form.fields['age_range'].choices.append((x, y))

    # gender
    for x, y in UserProfile.GENDER:
        form.fields['gender'].choices.append((x, y))
    return
