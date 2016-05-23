"""
Translation registration for django modeltranslation
"""


from modeltranslation.translator import translator, TranslationOptions
from .models import Category, Tag


class CategoryTranslation(TranslationOptions):
    fields = ('name',)


class TagTranslation(TranslationOptions):
    fields = ('name', 'description', 'summary')


translator.register(Category, CategoryTranslation)
translator.register(Tag, TagTranslation)
