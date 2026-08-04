from django.apps import AppConfig


class Fail2banPluginConfig(AppConfig):
    name = 'fail2ban'
    verbose_name = 'Fail2ban Security Manager'
    default_auto_field = 'django.db.models.BigAutoField'

    def ready(self):
        try:
            from . import signals  # noqa: F401
        except Exception:
            pass
        try:
            from .auto_ban import ensure_autoban_monitor_if_enabled
            ensure_autoban_monitor_if_enabled()
        except Exception:
            pass
