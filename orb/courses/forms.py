
from django import forms
import json

from orb.courses import models


class CourseAdminForm(forms.ModelForm):

    class Meta:
        model = models.Course
        fields = "__all__"

    def clean_sections(self):
        data = self.cleaned_data.get("sections", "[]")
        try:
            json.loads(data)
        except ValueError:
            raise forms.ValidationError("Invalid JSON. Try checking this using https://jsonlint.com/")
        return data


class CourseForm(forms.ModelForm):

    class Meta:
        model = models.Course
        fields = ['title', 'sections']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(CourseForm, self).__init__(*args, **kwargs)

    def clean_sections(self):
        data = self.cleaned_data.get("sections", "[]")
        try:
            json.loads(data)
        except ValueError:
            raise forms.ValidationError("Invalid JSON")
        return data