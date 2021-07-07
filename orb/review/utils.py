"""
Utility functions isolated to prevent circular dependencies
"""
from __future__ import unicode_literals


def unmet_criteria(resource):
    """
    Returns criteria which were unselected for the resource.

    Whether a criterion is unmet or not must take into account the context of
    the reviewer's role, as a reviewer has only to select from general criteria
    and the criteria specific to their role. Thus they may leave criteria
    unchecked which does not indicate that the review failed baesd on these
    criteria.

    Args:
        resource:

    Returns:
        an list of unique ResourceCriteria

    """
    unmet = []
    for review in resource.content_reviews.all():
        unmet += review.unmet_criteria()
    return set(unmet)
