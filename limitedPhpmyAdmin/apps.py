# -*- coding: utf-8 -*-
import os

from django.apps import AppConfig


class LimitedPhpmyAdminConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'limitedPhpmyAdmin'
    verbose_name = 'Limited phpMyAdmin'

    def ready(self):
        """
        Ensure templates resolve even when APP_DIRS discovery misses this app (e.g. odd
        install order, partial extract). Registers .../limitedPhpmyAdmin/templates on the
        main DjangoTemplates engine DIRS.
        """
        try:
            from django.conf import settings
        except Exception:
            return
        tpl_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
        if not os.path.isdir(tpl_root):
            return
        for tcfg in getattr(settings, 'TEMPLATES', []):
            if not str(tcfg.get('BACKEND', '')).endswith('DjangoTemplates'):
                continue
            dirs = tcfg.get('DIRS')
            if dirs is None:
                tcfg['DIRS'] = [tpl_root]
            elif tpl_root not in dirs:
                tcfg['DIRS'] = list(dirs) + [tpl_root]
            break
