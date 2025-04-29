"""
URLs for platform_plugin_hyperpay.
"""
from django.urls import include, path

from platform_plugin_hyperpay import views

urlpatterns = [
    path('info/', views.info_view, name='hyperpay-info'),
    path('payment/', include('platform_plugin_hyperpay.payment.urls', namespace='hyperpay-payment')),
    path('saleor-app/api/', include('platform_plugin_hyperpay.saleor_app.urls', namespace='hyperpay-saleor-app')),
]
