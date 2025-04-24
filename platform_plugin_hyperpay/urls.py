"""
URLs for platform_plugin_hyperpay.
"""
from django.urls import path

from platform_plugin_hyperpay import views

urlpatterns = [
    path('info/', views.info_view, name='hyperpay-info'),
]
