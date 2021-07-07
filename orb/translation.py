"""
Translation registration for django modeltranslation
"""

from __future__ import unicode_literals

from modeltranslation.translator import TranslationOptions, translator

from orb import models


class CategoryTranslation(TranslationOptions):
    fields = ('name',)


class TagTranslation(TranslationOptions):
    fields = ('name', 'description', 'summary')


class ResourceTranslation(TranslationOptions):
    fields = ('title', 'description', 'attribution')


class ResourceURLTranslation(TranslationOptions):
    fields = ('title', 'description')


class ResourceFileTranslation(TranslationOptions):
    fields = ('title', 'description')


class ResourceCriteriaTranslation(TranslationOptions):
    fields = ('description',)


translator.register(models.Category, CategoryTranslation)
translator.register(models.Tag, TagTranslation)
translator.register(models.Resource, ResourceTranslation)
translator.register(models.ResourceURL, ResourceURLTranslation)
translator.register(models.ResourceFile, ResourceFileTranslation)
translator.register(models.ResourceCriteria, ResourceCriteriaTranslation)
