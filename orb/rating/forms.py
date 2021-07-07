from __future__ import unicode_literals

from django import forms

from orb.models import ResourceRating


class RatingForm(forms.ModelForm):

    class Meta:
        fields = '__all__'
        model = ResourceRating

    def save(self):
        """Prevent duplicates (per user/resource) and save"""
        try:
            self.instance = ResourceRating.objects.get(
                user=self.cleaned_data['user'],
                resource=self.cleaned_data['resource'],
            )
        except ResourceRating.DoesNotExist:
            pass
        else:
            self.instance.rating = self.cleaned_data['rating']

        super(RatingForm, self).save()
