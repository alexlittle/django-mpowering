"""
Forms specific to working directly with resources
"""
from __future__ import unicode_literals

from collections import OrderedDict

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Layout, Submit
from django import forms
from django.utils.translation import ugettext_lazy as _

from orb.models import Tag


class ResourceAccessForm(forms.Form):
    """
    Form class for collecting information prior to allowing a user to
    download a resource file or access a resource link.
    """
    INTENDED_USE = OrderedDict([
        ("learning", _("For my own learning")),
        ("browsing", _("I'm just browsing")),
        ("training", _("For training frontline health workers")),
        ("other", _("Other")),
    ])

    survey_intended_use = forms.ChoiceField(
        label=_("Please let us know how you are intending to use this resource"),
        required=True,
        choices=INTENDED_USE.items(),
        widget=forms.RadioSelect(),
    )
    survey_intended_use_other = forms.CharField(
        label=_("Please explain"),
        required=False,
        widget=forms.Textarea(),
    )
    survey_health_worker_count = forms.IntegerField(
        label=_("How many frontline health workers are you intending to train?"),
        required=False,
        widget=forms.NumberInput(attrs={'min': 1}),
    )
    survey_health_worker_cadre = forms.ChoiceField(
        label=_("What type/cadre of frontline health workers are you intending to train?"),
        required=False,
        choices=[],
    )

    def __init__(self, *args, **kwargs):
        super(ResourceAccessForm, self).__init__(*args, **kwargs)
        self.fields['survey_health_worker_cadre'].choices = Tag.tags.roles().slugchoices(empty_label=_("Choose type/cadre"))
        self.helper = FormHelper()
        self.helper.form_method = 'GET'
        self.helper.form_class = 'form-horizontal'
        self.helper.disable_csrf = True
        self.helper.label_class = 'col-lg-2'
        self.helper.field_class = 'col-lg-8'
        self.helper.layout = Layout(
            'survey_intended_use',
            'survey_intended_use_other',
            'survey_health_worker_count',
            'survey_health_worker_cadre',
            Div(
                Submit('submit', _('Continue &gt;&gt;'),
                       css_class='btn btn-default'),
                css_class='col-lg-offset-2 col-lg-8',
            ),
        )

    def clean(self):
        data = self.cleaned_data

        intended_use = data.get('survey_intended_use')
        exclude = {
            'browsing': ['survey_intended_use_other', 'survey_health_worker_count', 'survey_health_worker_cadre'],
            'learning': ['survey_intended_use_other', 'survey_health_worker_count', 'survey_health_worker_cadre'],
            'training': ['survey_intended_use_other'],
            'other': ['survey_health_worker_count', 'survey_health_worker_cadre'],
        }

        for field in exclude.get(intended_use, []):
            if field in data:
                del data[field]

        use_other = data.get('survey_intended_use_other')
        worker_count = data.get('survey_health_worker_count', 0) or 0  # Enforce 0 if '' or None
        worker_cadre = data.get('survey_health_worker_cadre')

        if intended_use == 'training':
            if not worker_cadre:
                self.add_error('survey_health_worker_cadre', _("Please select an item"))
            if worker_count < 1:
                self.add_error('survey_health_worker_count', _("Please enter a number greater than zero"))

        elif intended_use == 'other' and not use_other:
            self.add_error('survey_intended_use_other', _("Please enter an explanation"))

        return data
