from __future__ import unicode_literals

from django.contrib import messages
from django.contrib.admin import helpers
from django.contrib.admin.utils import model_ngettext
from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from django.utils.encoding import force_text
from django.utils.translation import ugettext as _


def merge_selected_tags(modeladmin, request, queryset):
    """
    Default action which deletes the selected objects.

    This action first displays a confirmation page which shows all the
    deleteable objects, or, if the user has no permission one of the related
    childs (foreignkeys), a "permission denied" message.

    Next, it deletes all selected objects and redirects back to the change list.
    """
    opts = modeladmin.model._meta
    app_label = opts.app_label

    # Check that the user has delete permission for the actual model
    # TOD
    if not modeladmin.has_delete_permission(request):
        raise PermissionDenied

    # The user has already confirmed the deletion.
    # Do the deletion and return a None to display the change list view again.
    if request.POST.get('post'):

        winner = modeladmin.model.objects.get(pk=request.POST.get('winner'))

        queryset = queryset.exclude(pk=winner.pk)

        n = queryset.count()
        if n:

            n += 1  # For display we want to include the winner in the count

            for obj in queryset:
                obj_display = force_text(obj)
                modeladmin.log_deletion(request, obj, obj_display)
                winner.merge(obj)

            modeladmin.message_user(request, _("Successfully merged %(count)d %(items)s.") % {
                "count": n, "items": model_ngettext(modeladmin.opts, n)
            }, messages.SUCCESS)
        # Return None to display the change list page again.
        return None

    if len(queryset) == 1:
        objects_name = force_text(opts.verbose_name)
    else:
        objects_name = force_text(opts.verbose_name_plural)

    title = _("Are you sure?")

    context = dict(
        modeladmin.admin_site.each_context(request),
        title=title,
        objects_name=objects_name,
        model_count=queryset.count(),
        queryset=queryset,
        opts=opts,
        action_checkbox_name=helpers.ACTION_CHECKBOX_NAME,
    )

    request.current_app = modeladmin.admin_site.name

    return render(request, "admin/orb/tag/merge_tags_confirmation.html", context)
