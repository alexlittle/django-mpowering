from __future__ import unicode_literals

from django.db import models
from django.db.models import Q


class CriteriaQueryset(models.QuerySet):

    def general(self):
        return self.filter(role__isnull=True)

    def for_role(self, role):
        """Returns both general and role specific criteria for one role"""
        return self.filter(Q(role=role) | Q(role__isnull=True))

    def for_roles(self, *roles):
        """Returns both general and role specific criteria for multiple roles"""
        return self.filter(Q(role__in=roles) | Q(role__isnull=True))
