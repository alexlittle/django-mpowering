from __future__ import unicode_literals

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

import orb
from orb.models import TagOwner, home_resources


def get_menu(request):
    if request.user.is_authenticated:
        tags = TagOwner.objects.filter(user=request.user)
    else:
        tags = None

    if request.user.is_authenticated:
        try:
            if request.user.userprofile and request.user.userprofile.is_reviewer:
                reviewer = True
            else:
                reviewer = False
        except ObjectDoesNotExist:
            reviewer = False
    else:
        reviewer = False

    return {
        'header_menu_categories': home_resources(),
        'header_owns_tags': tags,
        'settings': settings,
        'reviewer': reviewer,
    }


def get_version(request):
    version = "v" + str(orb.VERSION[0]) + "." + \
        str(orb.VERSION[1]) + "." + str(orb.VERSION[2])

    if getattr(settings, 'STAGING', False):
        staging = True
    else:
        staging = False

    notices = []
    #if date.today() >= date(2017, 04, 05) and date.today() <= date(2017, 05, 21):
    #    notices.append(_('<strong>ORB Survey.</strong> We would like to hear from you on your experience using ORB as a training tool. Please fill out our short survey and enter in to win a $25 Amazon gift card! <strong><a href="https://goo.gl/forms/mPML9uiRZpjSeQkJ3" target="_blank">Take the survey</a></strong>'))

    return {'version': version,
            'ORB_GOOGLE_ANALYTICS_CODE': settings.ORB_GOOGLE_ANALYTICS_CODE,
            'ORB_RESOURCE_MIN_RATINGS': settings.ORB_RESOURCE_MIN_RATINGS,
            'STAGING': staging,
            'NOTICES': notices,}


def base_context_processor(request):
    return {
        'BASE_URL': request.build_absolute_uri("/").rstrip("/")
    }
