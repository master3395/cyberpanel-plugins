# -*- coding: utf-8 -*-
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='LimitedPhpmyAdminGrant',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('database_name', models.CharField(help_text='Must match databases.Databases.dbName for this website', max_length=64)),
                ('subject_type', models.CharField(choices=[('ftp', 'FTP user'), ('cpuser', 'CyberPanel user')], max_length=16)),
                ('subject_label', models.CharField(help_text='Display: FTP login or panel username', max_length=200)),
                ('ftp_user_id', models.IntegerField(blank=True, help_text='ftp.models.Users.pk when subject_type=ftp', null=True)),
                ('administrator_id', models.IntegerField(blank=True, help_text='Administrator.pk when subject_type=cpuser', null=True)),
                ('mysql_username', models.CharField(max_length=32, unique=True)),
                ('password_encrypted', models.TextField()),
                ('enabled', models.BooleanField(default=True)),
                ('notes', models.TextField(blank=True, default='')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('website', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='limited_pma_grants', to='websiteFunctions.websites')),
            ],
            options={
                'db_table': 'limitedphpmyadmin_grant',
                'ordering': ['-id'],
            },
        ),
    ]
