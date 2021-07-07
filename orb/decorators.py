"""
Custom access decorators
"""

from __future__ import unicode_literals

from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied


def staff_test(user):
    """
    Tests that raises an exception for logged in, non-staff users

    PermissionDenied excpetion is returned as an HTTP 403 response
    """
    if not user.is_authenticated:
        return False
    if user.is_active and user.is_staff:
        return True
    raise PermissionDenied


def staff_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None):
    """
    Decorator for views that checks that the user is logged in and a staff member.

    Unauthenticated users are redirected to the login page, authenticated users
    lacking the necessary status are returns a 403 Forbidden status (further
    authentication will not make any difference).
    """
    actual_decorator = user_passes_test(
        lambda u: staff_test(u),
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator
