from django.apps import AppConfig


class DiscordwebhooksConfig(AppConfig):
    name = 'discordWebhooks'

    def ready(self):
        from . import signals
