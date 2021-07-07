
from __future__ import unicode_literals

from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from orb.emailer import send_orb_email


def send_peer_sync_notification_email(peer, **kwargs):
    """
    Sends an email to staff recipients that the peer was synced and a
    summary of updated resource counts.

    kwargs should includ3 new_resource_count and updated_resource_count
    """
    return send_orb_email(
        template_html="orb/email/api_resources_updated.html",
        template_text="orb/email/api_resources_updated.txt",
        subject=_("Peer Sync Complete") + ": " + peer.name,
        recipients=[settings.ORB_INFO_EMAIL],
        peer=peer,
        **kwargs
    )
