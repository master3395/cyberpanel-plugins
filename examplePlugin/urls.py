from django.urls import path
from . import views

urlpatterns = [
    path('', views.examplePlugin, name='examplePlugin'),
    path('settings/', views.settings_view, name='settings'),
]

