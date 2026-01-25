from django.urls import path
from . import views

app_name = 'paypalPremiumPlugin'

urlpatterns = [
    path('', views.main_view, name='main'),
    path('settings/', views.settings_view, name='settings'),
    path('api/status/', views.api_status_view, name='api_status'),
]
