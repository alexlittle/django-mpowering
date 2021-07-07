# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('analytics', '0002_userlocationvisualization_source'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userlocationvisualization',
            name='ip',
            field=models.GenericIPAddressField(),
            preserve_default=True,
        ),
    ]
