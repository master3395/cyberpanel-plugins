from django.urls import path
from . import views

app_name = 'googleTagManager'

urlpatterns = [
    path('', views.main_view, name='main'),
    path('settings/', views.settings_view, name='settings'),
    path('api/domains/', views.api_get_domains, name='api_domains'),
    path('api/save/', views.api_save_gtm, name='api_save'),
    path('api/delete/', views.api_delete_gtm, name='api_delete'),
    path('api/code/<str:domain>/', views.api_get_gtm_code, name='api_code'),
    path('api/toggle/', views.api_toggle_gtm, name='api_toggle'),
]
