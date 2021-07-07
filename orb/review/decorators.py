from __future__ import unicode_literals

from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied


def content_reviewer(user, include_staff=True):
    """
    Tests that user is content reviewer (or superuser)

    Args:
        user: the User object
        include_staff: boolean for whether to also allow non-reviewer staff

    Returns:
        Boolean

    Raises:
        PermissionDenied

    """
    if not user.is_authenticated:
        return False

    is_staff = user.is_staff if include_staff else False

    if user.is_active and (user.userprofile.is_reviewer or is_staff):
        return True

    raise PermissionDenied


def reviewer_required(function=None, include_staff=True, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None):
    """
    Decorator for views that checks that the user is logged in and either a
    staff member or a content reviewer.
    """
    actual_decorator = user_passes_test(
        lambda u: content_reviewer(u, include_staff=include_staff),
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator
