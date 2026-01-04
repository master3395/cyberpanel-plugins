from django.contrib import admin
from .models import DiscordWebhook, WebhookSettings

admin.site.register(DiscordWebhook)
admin.site.register(WebhookSettings)
