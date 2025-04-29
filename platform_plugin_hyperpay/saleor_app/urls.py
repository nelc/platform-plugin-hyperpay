"""URLs for Saleor app views and webhooks."""

from django.urls import path

from platform_plugin_hyperpay.saleor_app.views import get_saleor_app_manifest, register_saleor_app_token

app_name = 'platform_plugin_hyperpay'  # pylint: disable=invalid-name

urlpatterns = [
    path("manifest", get_saleor_app_manifest, name="get_app_manifest"),
    path("register", register_saleor_app_token, name="register_saleor_app_token"),
]
