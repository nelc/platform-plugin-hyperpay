"""eox_nelp course_api  urls
"""
from django.urls import include, path
from platform_plugin_hyperpay.payment import views
app_name = 'platform_plugin_hyperpay'  # pylint: disable=invalid-name

urlpatterns = [
    path('pay/', views.HyperPayPaymentPageView.as_view(), name='hyperpay-payment-page'),
]
