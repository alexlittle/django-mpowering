# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('orb', '0023_auto_20151028_2050'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='name_en',
            field=models.CharField(max_length=100, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='category',
            name='name_es',
            field=models.CharField(max_length=100, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='category',
            name='name_pt_br',
            field=models.CharField(max_length=100, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='tag',
            name='description_en',
            field=models.TextField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='tag',
            name='description_es',
            field=models.TextField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='tag',
            name='description_pt_br',
            field=models.TextField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='tag',
            name='name_en',
            field=models.CharField(max_length=100, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='tag',
            name='name_es',
            field=models.CharField(max_length=100, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='tag',
            name='name_pt_br',
            field=models.CharField(max_length=100, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='tag',
            name='summary_en',
            field=models.CharField(max_length=100, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='tag',
            name='summary_es',
            field=models.CharField(max_length=100, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='tag',
            name='summary_pt_br',
            field=models.CharField(max_length=100, null=True, blank=True),
            preserve_default=True,
        ),
    ]
