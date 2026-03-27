# -*- coding: utf-8 -*-
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('limitedPhpmyAdmin', '0002_pmalaunchtoken'),
    ]

    operations = [
        migrations.AddField(
            model_name='limitedphpmyadmingrant',
            name='privilege_profile',
            field=models.CharField(
                default='ALL',
                help_text='Comma-separated MySQL privileges for this database, or ALL',
                max_length=300,
            ),
        ),
    ]
