from django.apps import AppConfig

class Fail2banPluginConfig(AppConfig):
    name = 'fail2ban'
    verbose_name = 'Fail2ban Security Manager'
    default_auto_field = 'django.db.models.BigAutoField'
    
    def ready(self):
        # Import signal handlers when the app is ready
        try:
            import fail2ban.signals
        except Exception as e:
            # Silently ignore signal import errors during startup
            pass
