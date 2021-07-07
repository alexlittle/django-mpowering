from __future__ import unicode_literals

from haystack import indexes

from orb.models import Resource


class ResourceIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    author = indexes.CharField(model_attr='create_user')

    def get_model(self):
        return Resource

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.filter(status=Resource.APPROVED)

    def get_updated_field(self):
        return "update_date"
