# orb/emailer.py
from __future__ import unicode_literals

from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _

from orb.models import ResourceCriteria


def send_orb_email(
        from_email=settings.SERVER_EMAIL,
        template_html=None,
        template_text=None,
        subject="",
        fail_silently=False,
        recipients=None,
        **context):
    """
    Base email task function

    Args:
        from_email: from address
        template_html: path to HTML body template
        template_text: path to text body template
        subject: email subject, not including prefex
        fail_silently: boolean, should send_mail fail silently
        recipients: a list or iterable of email addresses
        **context: dictionary providing email template context

    Returns:
        0 or 1, return value of send_mail

    """
    email_subject = settings.EMAIL_SUBJECT_PREFIX + subject
    text_content = render_to_string(template_text, context)
    html_content = render_to_string(template_html, context)
    return send_mail(
        email_subject,
        text_content,
        from_email,
        recipients or [],
        fail_silently=fail_silently,
        html_message=html_content,
    )


def user_welcome(to_user):
    template_html = 'orb/email/welcome.html'
    template_text = 'orb/email/welcome.txt'

    from_email = settings.SERVER_EMAIL
    subject = settings.EMAIL_SUBJECT_PREFIX + _("Welcome to ORB")

    data = {"firstname": to_user.first_name,
            "lastname": to_user.last_name,
            "info_email": settings.ORB_INFO_EMAIL}

    text_content = render_to_string(template_text, data)
    html_content = render_to_string(template_html, data)

    send_mail(subject,
              text_content,
              from_email,
              [to_user.email],
              fail_silently=False,
              html_message=html_content)


def password_reset(to_user, new_password):
    template_html = 'orb/email/password_reset.html'
    template_text = 'orb/email/password_reset.txt'

    from_email = settings.SERVER_EMAIL
    subject = settings.EMAIL_SUBJECT_PREFIX + _("Password reset")

    text_content = render_to_string(
        template_text, {"new_password": new_password})
    html_content = render_to_string(
        template_html, {"new_password": new_password})

    send_mail(subject,
              text_content,
              from_email,
              [to_user.email],
              fail_silently=False,
              html_message=html_content)


def first_resource(to_user, resource):
    template_html = 'orb/email/first_resource.html'
    template_text = 'orb/email/first_resource.txt'

    from_email = settings.SERVER_EMAIL
    subject = settings.EMAIL_SUBJECT_PREFIX + \
        _("Resource Submitted") + ": " + resource.title

    data = {"title": resource.title,
            "firstname": to_user.first_name,
            "lastname": to_user.last_name,
            "info_email": settings.ORB_INFO_EMAIL}

    text_content = render_to_string(template_text, data)
    html_content = render_to_string(template_html, data)

    send_mail(subject,
              text_content,
              from_email,
              [to_user.email],
              fail_silently=False,
              html_message=html_content)


def resource_approved(request, to_user, resource):
    template_html = 'orb/email/resource_approved.html'
    template_text = 'orb/email/resource_approved.txt'

    from_email = settings.SERVER_EMAIL
    subject = settings.EMAIL_SUBJECT_PREFIX + \
        _("Resource Submission") + ": " + resource.title

    data = {"title": resource.title,
            "firstname": to_user.first_name,
            "lastname": to_user.last_name,
            "info_email": settings.ORB_INFO_EMAIL,
            "resource_link":  request.build_absolute_uri(reverse('orb_resource', args=[resource.slug]))}

    text_content = render_to_string(template_text, data)
    html_content = render_to_string(template_html, data)

    send_mail(subject,
              text_content,
              from_email,
              [to_user.email],
              fail_silently=False,
              html_message=html_content)


def resource_rejected(to_user, resource, criteria, notes):
    template_html = 'orb/email/resource_rejected.html'
    template_text = 'orb/email/resource_rejected.txt'

    from_email = settings.SERVER_EMAIL
    subject = settings.EMAIL_SUBJECT_PREFIX + \
        _("Resource Submission") + ": " + resource.title

    rejection_criteria = ResourceCriteria.objects.filter(id__in=criteria)
    data = {"title": resource.title,
            "firstname": to_user.first_name,
            "lastname": to_user.last_name,
            "info_email": settings.ORB_INFO_EMAIL,
            "criteria": rejection_criteria,
            "notes": notes}

    text_content = render_to_string(template_text, data)
    html_content = render_to_string(template_html, data)

    send_mail(subject,
              text_content,
              from_email,
              [to_user.email],
              fail_silently=False,
              html_message=html_content)


def new_resource_submitted(request, resource):
    template_html = 'orb/email/resource_submitted.html'
    template_text = 'orb/email/resource_submitted.txt'

    from_email = settings.SERVER_EMAIL
    subject = settings.EMAIL_SUBJECT_PREFIX + \
        _(" New resource submitted") + ": " + resource.title

    resource_link = "https://covid-19library.org" + reverse('orb_resource', args=[resource.slug])
    assign_reviewers_link = "https://covid-19library.org" + reverse('orb_assign_review', args=[resource.id])

    data = {"title": resource.title,
            "firstname": resource.create_user.first_name,
            "lastname": resource.create_user.last_name,
            "info_email": settings.ORB_INFO_EMAIL,
            "resource_link": resource_link,
            "assign_reviewers_link": assign_reviewers_link
            }

    text_content = render_to_string(template_text, data)
    html_content = render_to_string(template_html, data)

    send_mail(subject,
              text_content,
              from_email,
              [settings.ORB_INFO_EMAIL],
              fail_silently=False,
              html_message=html_content)


def link_checker_results(resource_urls, tags):
    template_html = 'orb/email/link_checker_results.html'
    template_text = 'orb/email/link_checker_results.txt'

    from_email = settings.SERVER_EMAIL
    subject = settings.EMAIL_SUBJECT_PREFIX + _("Link checker results")

    data = {"resource_urls": resource_urls,
            "tags": tags,
            "info_email": settings.ORB_INFO_EMAIL,
            }

    text_content = render_to_string(template_text, data)
    html_content = render_to_string(template_html, data)

    send_mail(subject,
              text_content,
              from_email,
              [email for name, email in settings.ADMINS],
              fail_silently=False,
              html_message=html_content)
