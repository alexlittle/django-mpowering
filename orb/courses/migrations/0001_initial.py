# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]

    operations = [
        migrations.CreateModel(
            name="Course",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                ("create_date", models.DateTimeField(auto_now_add=True)),
                ("update_date", models.DateTimeField(auto_now=True)),
                (
                    "status",
                    models.CharField(
                        default="active",
                        max_length=50,
                        choices=[("active", "active"), ("archived", "archived")],
                    ),
                ),
                ("title", models.CharField(max_length=200)),
                ("sections", models.TextField(default="[]")),
                (
                    "create_user",
                    models.ForeignKey(
                        related_name="course_create_user", to=settings.AUTH_USER_MODEL
                    ),
                ),
                (
                    "update_user",
                    models.ForeignKey(
                        related_name="course_update_user", to=settings.AUTH_USER_MODEL
                    ),
                ),
            ],
            options={"abstract": False},
        )
    ]
