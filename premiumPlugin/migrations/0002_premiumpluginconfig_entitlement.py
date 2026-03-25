# -*- coding: utf-8 -*-
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('premiumPlugin', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='premiumpluginconfig',
            name='entitlement_token',
            field=models.TextField(blank=True, default='', help_text='Short-lived API entitlement; requires phone-home refresh.'),
        ),
        migrations.AddField(
            model_name='premiumpluginconfig',
            name='entitlement_expires_at',
            field=models.PositiveIntegerField(blank=True, help_text='Unix expiry for entitlement_token (from API).', null=True),
        ),
    ]
