"""URLs for Saleor app views and webhooks."""

from django.urls import path

from platform_plugin_hyperpay.saleor_app.views import get_saleor_app_manifest, register_saleor_app_token
from platform_plugin_hyperpay.saleor_app.webhooks import transaction_initialize

app_name = 'platform_plugin_hyperpay'  # pylint: disable=invalid-name

urlpatterns = [
    path("api/manifest", get_saleor_app_manifest, name="get-app-manifest"),
    path("api/register", register_saleor_app_token, name="register-saleor-app-token"),
    path("api/webhooks/transaction-initialize-session", transaction_initialize, name="transaction-initialize"),  # Placeholder for webhooks
]
