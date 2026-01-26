from django.urls import path
from . import views

app_name = 'discordAuth'

urlpatterns = [
    path('', views.main_view, name='main'),
    path('settings/', views.settings_view, name='settings'),
    path('login/', views.discord_login, name='login'),
    path('callback/', views.discord_callback, name='callback'),
    path('check/', views.check_enabled, name='check'),
]
