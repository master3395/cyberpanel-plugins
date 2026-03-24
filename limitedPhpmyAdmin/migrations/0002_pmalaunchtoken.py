# -*- coding: utf-8 -*-
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('limitedPhpmyAdmin', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PmaLaunchToken',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.CharField(db_index=True, max_length=64, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField()),
                ('used_at', models.DateTimeField(blank=True, null=True)),
                (
                    'grant',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='pma_launch_tokens',
                        to='limitedPhpmyAdmin.limitedphpmyadmingrant',
                    ),
                ),
            ],
            options={
                'db_table': 'limitedphpmyadmin_pma_launch_token',
                'ordering': ['-id'],
            },
        ),
    ]
