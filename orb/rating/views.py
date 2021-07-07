from __future__ import unicode_literals

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from orb.models import ResourceRating

from .forms import RatingForm


@login_required
@csrf_exempt
@require_POST
def resource_rate_view(request):
    """
    View that allows a user to add or update a rating for a resource.
    """
    form_data = request.POST.copy()
    form_data.update({"user": request.user.pk})
    form = RatingForm(data=form_data)

    if not form.is_valid():
        return HttpResponseBadRequest()

    form.save()

    resource = form.cleaned_data['resource']

    return JsonResponse({
        'no_ratings': ResourceRating.objects.filter(resource=resource).count(),
        'ratings_required': settings.ORB_RESOURCE_MIN_RATINGS,
    })
