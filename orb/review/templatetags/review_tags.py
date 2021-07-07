"""
Template labels for content review
"""

from __future__ import unicode_literals

from django import template

from orb.models import ResourceCriteria, ReviewerRole

register = template.Library()


@register.inclusion_tag("orb/review/_status_labels.html")
def status_labels(resource):
    """
    Renders tag labels for the individual reviews (assigned or
    unassigned by role) for a given resource.

    Args:
        resource: an orb.Resource under review

    Returns:
        Rendered template

    """
    roles = list(ReviewerRole.objects.all())

    reviews = resource.content_reviews.all()
    assigned_reviews= {review.role: review for review in reviews}

    assignments = {}
    for role in roles:
        assigned = assigned_reviews.get(role)
        if not assigned:
            assignments[role.name] = {
                'status': 'unassigned',
                'class': 'default',
            }
        else:
            if assigned.is_overdue:
                assignments[role.name] = {
                    'status': 'overdue',
                    'class': 'warning',
                }
            elif assigned.is_pending:
                assignments[role.name] = {
                    'status': 'pending',
                    'class': 'info',
                }
            else:
                assignments[role.name] = {
                    'status': 'complete',
                    'class': 'success',
                }

    return {
        'assignments': assignments,
    }


@register.inclusion_tag("orb/review/_selected_review_criteria.html")
def selected_criteria(review):
    selected = review.criteria.all()
    unselected = ResourceCriteria.objects.for_role(review.role).exclude(pk__in=selected)
    return {
        'selected': selected,
        'unselected': unselected,
    }


@register.simple_tag(takes_context=True)
def can_start_review(context, resource):
    """
    Returns a boolean value for whether the user in the context
    is a reviewer for one of the unassigned roles for the given
    resource

    Args:
        context: the template context
        resource: an orb.Resource instance

    Returns:
        Boolean value

    """
    profile = context['user'].userprofile
    if not profile.is_reviewer:
        return False
    # TODO this is wrong
    return not resource.content_reviews.filter(role__in=profile.reviewer_roles.all()).exists()
