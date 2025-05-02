"""URLs for Saleor app views and webhooks."""

from django.urls import path
from platform_plugin_hyperpay.saleor_app.views import (
    configure_saleor_app,
    get_saleor_app_manifest,
    register_saleor_app_token,
)
from platform_plugin_hyperpay.saleor_app.webhooks import transaction_initialize, payment_gateway_initialize_session

app_name = 'platform_plugin_hyperpay'  # pylint: disable=invalid-name

urlpatterns = [
    path("api/manifest", get_saleor_app_manifest, name="get-app-manifest"),
    path("api/register", register_saleor_app_token, name="register-saleor-app-token"),
    path("", configure_saleor_app, name="saleor-app"),
    path("api/webhooks/transaction-initialize-session", transaction_initialize, name="transaction-initialize"),  # Placeholder for webhooks
    path("api/webhooks/payment-gateway-initialize-session", payment_gateway_initialize_session, name="payment-gateway-initialize"),
]
