"""
Translation registration for django modeltranslation
"""


from modeltranslation.translator import translator, TranslationOptions
from .models import Category, Tag


@translator.register(Category)
class CategoryTranslation(TranslationOptions):
    fields = ('name',)


@translator.register(Tag)
class TagTranslation(TranslationOptions):
    fields = ('name', 'description', 'summary')


