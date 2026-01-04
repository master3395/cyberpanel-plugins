from django.apps import AppConfig

class Fail2banPluginConfig(AppConfig):
    name = 'fail2ban_plugin'
    verbose_name = 'Fail2ban Security Manager'
    default_auto_field = 'django.db.models.BigAutoField'
    
    def ready(self):
        # Import signal handlers when the app is ready
        try:
            import fail2ban_plugin.signals
        except Exception as e:
            # Silently ignore signal import errors during startup
            pass
