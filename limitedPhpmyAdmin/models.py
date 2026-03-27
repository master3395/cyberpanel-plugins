# -*- coding: utf-8 -*-
from django.db import models
from websiteFunctions.models import Websites


class LimitedPhpmyAdminGrant(models.Model):
    """
    One row per limited phpMyAdmin credential: one MySQL user, one database, optional soft-disable.
    """

    SUBJECT_FTP = 'ftp'
    SUBJECT_CPUSER = 'cpuser'
    SUBJECT_CHOICES = (
        (SUBJECT_FTP, 'FTP user'),
        (SUBJECT_CPUSER, 'CyberPanel user'),
    )

    website = models.ForeignKey(Websites, on_delete=models.CASCADE, related_name='limited_pma_grants')
    database_name = models.CharField(max_length=64, help_text='Must match databases.Databases.dbName for this website')
    subject_type = models.CharField(max_length=16, choices=SUBJECT_CHOICES)
    subject_label = models.CharField(max_length=200, help_text='Display: FTP login or panel username')
    ftp_user_id = models.IntegerField(null=True, blank=True, help_text='ftp.models.Users.pk when subject_type=ftp')
    administrator_id = models.IntegerField(null=True, blank=True, help_text='Administrator.pk when subject_type=cpuser')
    mysql_username = models.CharField(max_length=32, unique=True)
    password_encrypted = models.TextField()
    privilege_profile = models.CharField(
        max_length=300,
        default='ALL',
        help_text='Comma-separated MySQL privileges for this database, or ALL',
    )
    enabled = models.BooleanField(default=True)
    notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'limitedphpmyadmin_grant'
        ordering = ['-id']

    def __str__(self):
        return '%s -> %s (%s)' % (self.mysql_username, self.database_name, self.subject_label)


class PmaLaunchToken(models.Model):
    """
    Short-lived, single-use token so an end user can open phpMyAdmin via the panel
    signon script without CyberPanel admin credentials.
    """

    grant = models.ForeignKey(
        LimitedPhpmyAdminGrant,
        on_delete=models.CASCADE,
        related_name='pma_launch_tokens',
    )
    token = models.CharField(max_length=64, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'limitedphpmyadmin_pma_launch_token'
        ordering = ['-id']

    def __str__(self):
        return 'launch %s…' % (self.token[:8],)
