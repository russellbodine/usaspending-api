# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2017-04-09 17:24
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('references', '0063_auto_20170409_0104'),
    ]

    operations = [
        migrations.AlterField(
            model_name='legalentity',
            name='business_types_description',
            field=models.CharField(blank=True, max_length=150, null=True),
        ),
    ]
