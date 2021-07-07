from __future__ import unicode_literals

from django import forms
from django.conf.urls import url
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.db.models import F
from django.db.models import Value as V
from django.db.models.functions import Concat
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import ugettext_lazy as _

from orb import models
from orb.actions import merge_selected_tags
from orb.profiles.forms import UserCreationForm


class TagMergeForm(forms.Form):
    tag = forms.ModelChoiceField(queryset=models.Tag.tags.all(), label=_('Winner'))

    def __init__(self, other=None, *args, **kwargs):
        super(TagMergeForm, self).__init__(*args, **kwargs)
        if other:
            self.fields['tag'].queryset = models.Tag.tags.exclude(pk=other.pk)


class ReviewerFilter(admin.SimpleListFilter):
    """
    List filter for UserProfiles, to filter by reviewer status
    """
    title = _('is reviewer')
    parameter_name = 'reviewer'

    def lookups(self, request, model_admin):
        return (
            ('1', _('Yes')),
            ('0', _('No')),
        )

    def queryset(self, request, queryset):
        if self.value() == '1':
            return queryset.reviewers()
        if self.value() == '0':
            return queryset.nonreviewers()


class ResourceCriteriaInline(admin.TabularInline):
    """Inline class for showing related ResourceCriteria"""
    model = models.ResourceCriteria
    extra = 0


@admin.register(models.ReviewerRole)
class ReviewerRoleAdmin(admin.ModelAdmin):
    inlines = [ResourceCriteriaInline]


@admin.register(models.Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'top_level', 'slug', 'order_by')


@admin.register(models.Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'create_user', 'create_date', 'slug')
    search_fields = ['title', 'description']
    raw_id_fields = ('create_user', 'update_user')
    list_filter = ('status',)


@admin.register(models.ResourceCriteria)
class ResourceCriteriaAdmin(admin.ModelAdmin):
    list_display = ('description', 'get_role_display', 'order_by', )
    search_fields = ['description']


@admin.register(models.ResourceURL)
class ResourceURLAdmin(admin.ModelAdmin):
    list_display = ('resource', 'url', 'title', 'description')
    search_fields = ['title', 'description', 'url']
    raw_id_fields = ('resource', 'create_user', 'update_user')


@admin.register(models.ResourceFile)
class ResourceFileAdmin(admin.ModelAdmin):
    list_display = ('resource', 'file', 'title', 'description')
    search_fields = ['title', 'description']
    raw_id_fields = ('resource', 'create_user', 'update_user')


@admin.register(models.ResourceTag)
class ResourceTagAdmin(admin.ModelAdmin):
    list_display = ('resource', 'tag')
    raw_id_fields = ('resource', 'tag', 'create_user')


@admin.register(models.ResourceRating)
class ResourceRatingAdmin(admin.ModelAdmin):
    list_display = ('resource', 'rating', 'user', 'comments')
    raw_id_fields = ('resource', 'user')


@admin.register(models.ResourceTracker)
class ResourceTrackerAdmin(admin.ModelAdmin):
    list_display = ('resource', 'user', 'access_date', 'ip', 'type')
    raw_id_fields = ('resource', 'user', 'resource_file', 'resource_url')


@admin.register(models.ResourceWorkflowTracker)
class ResourceWorkflowTrackerAdmin(admin.ModelAdmin):
    list_display = ('resource', 'create_user', 'create_date',
                    'status', 'notes', 'owner_email_sent')
    search_fields = ['notes']
    raw_id_fields = ('resource', 'create_user')


@admin.register(models.SearchTracker)
class SearchTrackerAdmin(admin.ModelAdmin):
    list_display = ('query', 'user', 'access_date', 'no_results', 'ip', 'type')
    raw_id_fields = ('user',)


@admin.register(models.Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'external_url',
                    'slug', 'published', 'parent_tag', 'order_by', 'image')
    search_fields = ['name', 'description']
    raw_id_fields = ('create_user', 'update_user', 'category', 'parent_tag')
    list_filter = ['category']
    actions = [merge_selected_tags]

    def get_urls(self):
        urls = super(TagAdmin, self).get_urls()
        my_urls = [
            url(r'^(?P<object_id>\d+)/merge/$', self.admin_site.admin_view(self.merge_tags), name="merge_tags"),
        ]
        return my_urls + urls

    def merge_tags(self, request, object_id):
        tag = get_object_or_404(models.Tag, pk=object_id)

        form = TagMergeForm(tag)

        if request.method == 'POST':
            form = TagMergeForm(tag, data=request.POST)
            if form.is_valid():
                winner = form.cleaned_data['tag']
                winner.merge(tag)
                messages.success(request, "The tag '{}' was merged into '{}'".format(tag, winner))
                return redirect('admin:orb_tag_changelist')

        context = dict(
            self.admin_site.each_context(request),
            app_label='orb',
            tag=tag,
            form=form,
        )
        return render(request, "admin/orb/tag/merge_tag_form.html", context)


@admin.register(models.TagProperty)
class TagPropertyAdmin(admin.ModelAdmin):
    list_display = ('tag', 'name', 'value')
    search_fields = ['name', 'value']
    raw_id_fields = ('tag',)


@admin.register(models.UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')
    list_display = ('user_name', 'api_access', 'about', 'job_title', 'organisation')
    list_filter = (
        ReviewerFilter,
        'reviewer_roles',
    )

    def get_queryset(self, request):
        return super(UserProfileAdmin, self).get_queryset(request).annotate(
            full_user_name=Concat(
                F('user__first_name'),
                V(' '),
                F('user__last_name'),
            )
        )

    def user_name(self, obj):
        return obj.user.get_full_name() or obj.user
    user_name.admin_order_field = 'full_user_name'


@admin.register(models.TagOwner)
class TagOwnerAdmin(admin.ModelAdmin):
    list_display = ('user', 'tag')
    raw_id_fields = ('user', 'tag')


@admin.register(models.Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'visibility')


@admin.register(models.CollectionResource)
class CollectionResourceAdmin(admin.ModelAdmin):
    list_display = ('collection', 'resource', 'order_by')
    raw_id_fields = ('resource',)


@admin.register(models.CollectionUser)
class CollectionUserAdmin(admin.ModelAdmin):
    list_display = ('collection', 'user')


class CustomUserAdmin(UserAdmin):
    """Create a UserProfile when creating user from admin"""
    add_form = UserCreationForm


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
