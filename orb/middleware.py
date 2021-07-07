from __future__ import unicode_literals

from orb.forms import HeaderSearchForm


class SearchFormMiddleware(object):
    """Adds HeaderSearchForm to request as `search_form`"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        form = HeaderSearchForm()
        # attach the form to the request so it can be accessed within the
        # templates
        request.search_form = form
        return self.get_response(request)
