"""
Forms for resources - primarily for content review
"""

from __future__ import unicode_literals

import logging

from crispy_forms.bootstrap import StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Div, Layout, Row, Submit
from django import forms
from django.contrib import messages
from django.urls import reverse
from django.forms import inlineformset_factory
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _

from orb.models import Resource, ResourceCriteria, ResourceWorkflowTracker, ReviewerRole, UserProfile

from .models import ContentReview

logger = logging.getLogger(__name__)


class FormErrors(object):
    """Consolidates form error string literals"""
    MISSING_REASON = _("Please provide a reason for rejecting this content.")
    ASSIGN_COMPLETED_REIVEW = _("Cannot reassign a completed review.")
    ALL_CRITERIA = _("All criteria must be met before resource can be approved.")


class ReviewForm(forms.Form):
    """
    Form for allowing a reviewer to enter a resource review
    """
    approved = forms.BooleanField(required=False)
    reason = forms.CharField(required=False, widget=forms.Textarea)

    def __init__(self, *args, **kwargs):
        super(ReviewForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-2'
        self.helper.field_class = 'col-lg-8'
        self.helper.layout = Layout(
            'reason',
        )

    def clean(self):
        data = self.cleaned_data
        if not data.get('approved') and not data.get('reason'):
            raise forms.ValidationError(FormErrors.MISSING_REASON)
        return data


class StaffReviewForm(forms.ModelForm):
    """
    Form for allowing a staff user to approve or reject content
    """
    approved = forms.BooleanField(required=False)

    class Meta:
        model = ResourceWorkflowTracker
        fields = ['notes']

    def __init__(self, *args, **kwargs):
        self.resource = kwargs.pop('resource')
        self.user = kwargs.pop('user')
        super(StaffReviewForm, self).__init__(*args, **kwargs)
        self.helper = self.form_helper()

    def clean(self):
        data = self.cleaned_data
        if not data.get('approved') and not data.get('notes'):
            raise forms.ValidationError(FormErrors.MISSING_REASON)
        return data

    def save(self):
        """
        Handles logic of either approving or rejecting the resource
        """
        approved = self.cleaned_data['approved']

        instance = super(StaffReviewForm, self).save(commit=False)
        instance.create_user = self.user
        instance.resource = self.resource

        # TODO the following should be re-encapsulated in the review app workflow

        if approved:
            instance.status = Resource.APPROVED
            instance.save()
            self.resource.approve()
            self.resource.save()
            return messages.SUCCESS, _("The resource has been approved")

        instance.status = Resource.REJECTED
        instance.save()
        self.resource.reject()
        self.resource.save()
        return messages.SUCCESS, _("The resource has been rejected")

    def form_helper(self):
        helper = FormHelper()
        helper.form_class = 'form-horizontal'
        helper.label_class = 'col-lg-2'
        helper.field_class = 'col-lg-8'
        helper.layout = Layout(
            'notes',
            Row(HTML('<hr>')),
            Div(
                StrictButton(_('Approve'), name='approved', value=1, type="submit",
                       css_class='btn btn-success'),
                StrictButton(_('Reject'), name='approved', type="submit",
                       css_class='btn btn-warning'),

                HTML(
                    "<a class='btn btn-danger' href='{}'>{}</a>".format(
                        reverse('orb_delete_resource', kwargs={'resource_id': self.resource.pk}),
                        _('Delete'),
                    )
                ),
                css_class='col-lg-offset-2 col-lg-8',
            ),
        )
        return helper


class ReviewStartForm(forms.ModelForm):
    """
    Form class for validating a user starting a review on a resource.

    Takes a resource, a user, and then validates that the role selected
    belongs to the user and that it is available for a reivew.
    """
    class Meta:
        model = ContentReview
        fields = ['role']

    def __init__(self, *args, **kwargs):
        self.resource = kwargs.pop('resource')
        self.reviewer = kwargs.pop('reviewer')
        super(ReviewStartForm, self).__init__(*args, **kwargs)
        self.fields['role'].queryset = ReviewerRole.objects.filter(
            profiles__user=self.reviewer).exclude(reviews__in=self.resource.content_reviews.all())

    def save(self):
        instance = super(ReviewStartForm, self).save(commit=False)
        instance.resource = self.resource
        instance.reviewer = self.reviewer
        instance.save()
        return instance


class ContentReviewForm(forms.ModelForm):
    """
    Form class for capturing the explanation for rejecting a submitted resource

    This form is used for capturing review feedback which is then used
    by a staff member for final approval.
    """
    approved = forms.BooleanField(required=False)
    criteria = forms.ModelMultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
        queryset=ResourceCriteria.objects.all().order_by('order_by'),
        required=False,
        label=_("Approval criteria"),
    )
    notes = forms.CharField(
        widget=forms.Textarea,
        required=False,
        error_messages={'required': FormErrors.MISSING_REASON},
        help_text=_(
            'The text you enter here will be used for providing feedback to the submitter of the '
            'resource, so please bear this in mind when explaining your reasoning.'),
        label=_("Rejection reason or other notes")
    )

    class Meta:
        model = ContentReview
        fields = ('criteria', 'notes')

    def __init__(self, user=None, *args, **kwargs):
        self.user = user
        super(ContentReviewForm, self).__init__(*args, **kwargs)
        self.fields['criteria'].queryset = self.get_criteria().order_by('order_by')
        self.helper = self.form_helper()

    def clean(self):
        data = self.cleaned_data

        if data.get('approved'):
            selected_criteria = data.get('criteria').values_list('pk', flat=True)
            given_criteria = self.fields['criteria'].queryset.values_list('pk', flat=True)

            if set(selected_criteria) != set(given_criteria):
                raise forms.ValidationError(FormErrors.ALL_CRITERIA)

        else:
            if not data.get('notes'):
                raise forms.ValidationError(FormErrors.MISSING_REASON)

        return data

    def get_criteria(self):
        try:
            roles = self.user.userprofile.reviewer_roles.all()
        except AttributeError:
            logger.warning("{} has no profile, showing all resource criteria".format(self.user))
            return ResourceCriteria.criteria.all().order_by('order_by')
        return ResourceCriteria.criteria.for_roles(*roles)

    def form_helper(self):
        helper = FormHelper()
        helper.form_class = 'form-horizontal'
        helper.label_class = 'col-lg-2'
        helper.field_class = 'col-lg-8'
        helper.layout = Layout(
            'criteria',
            Row(HTML('<hr>')),
            'notes',
            Div(
                StrictButton(_('Approve'), name='approved', value=1, type="submit",
                       css_class='btn btn-success'),
                StrictButton(_('Reject'), name='approved', type="submit",
                       css_class='btn btn-danger'),
                css_class='col-lg-offset-2 col-lg-8',
            ),
        )
        return helper

    def save(self, *args, **kwargs):
        instance = super(ContentReviewForm, self).save()
        for criterion in self.cleaned_data['criteria']:
            self.instance.criteria.add(criterion)
        return instance


class AssignmentForm(forms.Form):
    """
    Form class for assigning reviews
    """
    def __init__(self, *args, **kwargs):
        self.resource = kwargs.pop('resource')
        for role in self.roles:
            self.declared_fields[role.name] = forms.ModelChoiceField(
                queryset=UserProfile.objects.filter(reviewer_roles=role),
                required=False,
            )
            self.declared_fields[role.name].initial = self.assignments.get(role.name)

        super(AssignmentForm, self).__init__(*args, **kwargs)

        for role in self.roles:
            self.fields[role.name] = forms.ModelChoiceField(
                queryset=UserProfile.objects.filter(reviewer_roles=role),
                required=False,
            )
            self.declared_fields[role.name] = self.fields[role.name]
            self.initial[role.name] = self.assignments.get(role.name)
            self.fields[role.name].initial = self.assignments.get(role.name)
            self.declared_fields[role.name].initial = self.fields[role.name].initial

        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-2'
        self.helper.field_class = 'col-lg-8'
        self.helper.layout = Layout(*self.layout_fields())

    def clean(self):
        data = self.cleaned_data
        complete_reviews = self.resource.content_reviews.complete()
        for review in complete_reviews:
            if data[review.role.name] != review.reviewer.userprofile:
                self.add_error(review.role.name, FormErrors.ASSIGN_COMPLETED_REIVEW)
        return data

    def save(self):
        for role in self.roles:
            assigned = self.cleaned_data.get(role.name)
            if assigned:
                try:
                    review = ContentReview.reviews.get(resource=self.resource, role=role)
                except ContentReview.DoesNotExist:
                    review = ContentReview.reviews.assign(resource=self.resource, role=role, reviewer=assigned.user)
                    logger.debug("New assignment {} for {}".format(review, assigned.user))
                else:
                    if review.reviewer != assigned.user:
                        logger.debug("Reassigning review {} to user {}".format(review, assigned.user))
                        review.reassign(assigned.user)
                        review.save()

    def layout_fields(self):
        """
        Yields the fields for the layout.

        This allows indeterminate fields to be added while maintaining a
        pre-defined ordering.
        """
        for role in self.roles:
            yield role.name
        yield Div(
            Submit('submit', _('Assign'),
                   css_class='btn btn-default'),
            HTML("<a href='{0}'>{1}</a>".format(
                reverse("orb_pending_resources"),
                _("Return to pending list"),
            )),
            css_class='col-lg-offset-2 col-lg-8',
        )

    @cached_property
    def roles(self):
        return ReviewerRole.objects.all()

    @cached_property
    def assignments(self):
        x = {
            review.role.name: review.reviewer.userprofile
            for review in ContentReview.objects.filter(resource=self.resource)
        }
        return x

AssignmentFormSet = inlineformset_factory(
    Resource,
    ContentReview,
    can_delete=False,
    extra=0,
    fields=('reviewer', 'role'),
)
