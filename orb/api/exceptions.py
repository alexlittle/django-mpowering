
from __future__ import unicode_literals

import json

from django.utils.encoding import force_text
from tastypie.exceptions import BadRequest

from orb.api.error_codes import *


class ORBAPIBadRequest(BadRequest):

    def __init__(self, error_code, pk=None):
        error = {
            "code": error_code,
            "message": force_text(ERROR_CODES[error_code]),
        }

        if pk:
            error['pk'] = pk

        super(ORBAPIBadRequest, self).__init__(json.dumps(error))
