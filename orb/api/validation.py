
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _
from tastypie.validation import Validation


class APIValidation(Validation):

    def is_valid(self, bundle, request=None):
        errors = {}
        if bundle.request.user.userprofile.api_access == False:
            errors['error_message'] = _("You do not have API access")
        return errors
