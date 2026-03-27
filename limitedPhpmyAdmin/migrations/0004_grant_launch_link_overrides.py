# -*- coding: utf-8 -*-
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('limitedPhpmyAdmin', '0003_limitedphpmyadmingrant_privilege_profile'),
    ]

    operations = [
        migrations.AddField(
            model_name='limitedphpmyadmingrant',
            name='launch_link_ttl_hours',
            field=models.PositiveSmallIntegerField(
                blank=True,
                help_text='Override panel policy link validity (hours); null = use global policy',
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='limitedphpmyadmingrant',
            name='launch_link_single_use',
            field=models.BooleanField(
                blank=True,
                help_text='Override single-use launch links; null = use global policy',
                null=True,
            ),
        ),
    ]
