from __future__ import unicode_literals

from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.sites.models import Site
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from six import text_type

from orb.emailer import send_orb_email
from orb.review.utils import unmet_criteria


def reverse_fqdn(url_name, *args, **kwargs):
    """
    Returns a reversed URL including the fully qualified domain name and protocol

    Args:
        url_name: named URL
        *args: positional arguments to pass to `reverse`
        **kwargs: keyword arguments to pass to `reverse`

    Returns:
        the whole URL

    """
    return "{protocol}://{domain}{path}".format(
        protocol=getattr(settings, "SITE_HTTP_PROTOCOL", "http"),
        domain=Site.objects.get_current().domain,
        path=reverse(url_name, args=args, kwargs=kwargs),
    )


def send_review_assignment_email(review):
    """
    Sends an email to the assigned reviewer for the given review.

    Args:
        review: a ContentReview

    Returns:
        result of `send_mail` - 1 or 0

    """
    return send_orb_email(
        template_html="orb/email/review_assignment.html",
        template_text="orb/email/review_assignment.txt",
        subject=_("Content Review for: ") + text_type(review.resource),
        recipients=[review.reviewer.email],
        reviewer_name=review.reviewer.get_full_name(),
        resource_title=review.resource.title,
        reviewer_role=review.role.get_name_display(),
        review=review,
        reviews_link=reverse_fqdn('orb_user_reviews'),
    )


def send_review_reminder_email(review):
    """

    Args:
        review: a ContentReview

    Returns:
        result of `send_mail` - 1 or 0

    """
    return send_orb_email(
        template_html="orb/email/review_reminder.html",
        template_text="orb/email/review_reminder.txt",
        subject=_("Resource review reminder: ") + text_type(review.resource),
        recipients=[review.reviewer.email],
        reviewer_name=review.reviewer.get_full_name(),
        resource_title=review.resource.title,
        review=review,
        review_age_days=7,
        reviews_link=reverse_fqdn('orb_user_reviews'),
    )


def remind_reviewers(start_days=7, end_days=8):
    """
    Sends reminders to reviewers for all late reviews created during a defined window

    A window is defined by looking back

    Args:
        start_days: the earlier number of days to go "back"
        end_days: the final number of days to go "back"

    Returns:
        None

    """
    from orb.review.models import ContentReview

    assert start_days < end_days

    pending_reviews = ContentReview.reviews.select_related().pending().filter(
        create_date__lte=datetime.utcnow() - timedelta(days=start_days),
        create_date__gt=datetime.utcnow() - timedelta(days=end_days),
    )

    for review in pending_reviews:
        send_review_reminder_email(review)


def send_resource_approved_email(resource):
    return send_orb_email(
        template_html="orb/email/resource_approved.html",
        template_text="orb/email/resource_approved.txt",
        subject=_("Resource Submission") + ": " + resource.title,
        recipients=[resource.create_user.email],
        title=resource.title,
        firstname=resource.create_user.first_name,
        lastname=resource.create_user.last_name,
        info_email=settings.ORB_INFO_EMAIL,
        resource_link=reverse_fqdn('orb_resource', resource.slug),
    )


def send_resource_rejected_email(resource):
    return send_orb_email(
        template_html="orb/email/resource_rejected.html",
        template_text="orb/email/resource_rejected.txt",
        subject=_("Resource Submission") + ": " + resource.title,
        recipients=[resource.create_user.email],
        title=resource.title,
        firstname=resource.create_user.first_name,
        lastname=resource.create_user.last_name,
        info_email=settings.ORB_INFO_EMAIL,
        resource_link=reverse_fqdn('orb_resource', resource.slug),
        notes=resource.workflow_trackers.rejected().notes(),
        rejected_criteria=unmet_criteria(resource),
    )


def send_review_complete_email(resource, **kwargs):
    """
    Sends an email to staff recipients that all reviews for the given
    resource have been completed.
    """
    return send_orb_email(
        template_html="orb/email/review_complete.html",
        template_text="orb/email/review_complete.txt",
        subject=_("Resource Review Complete") + ": " + resource.title,
        recipients=[settings.ORB_INFO_EMAIL],
        title=resource.title,
        firstname=resource.create_user.first_name,
        lastname=resource.create_user.last_name,
        resource_link=reverse_fqdn('orb_staff_review', resource.pk),
        resource=resource,
        **kwargs
    )
