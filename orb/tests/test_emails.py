# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core import mail
from django.test import TestCase

from orb.emailer import send_orb_email


class BaseEmailTests(TestCase):

    def test_one_recipient(self):
        """Function should send with one recipient listed"""
        count = len(mail.outbox)
        send_orb_email(
            recipients=["bob@example.com"],
            template_html="orb/email/password_reset.html",
            template_text="orb/email/password_reset.txt",
            subject="Tu contraseña ha sido restablecida.",
        )
        self.assertEqual(count + 1, len(mail.outbox))

    def test_multiple_recipients(self):
        """Function should send with multiple recipients listed"""
        count = len(mail.outbox)
        send_orb_email(
            recipients=["bob@example.com", "sue@example.com"],
            template_html="orb/email/password_reset.html",
            template_text="orb/email/password_reset.txt",
            subject="Tu contraseña ha sido restablecida.",
        )
        self.assertEqual(count + 1, len(mail.outbox))
