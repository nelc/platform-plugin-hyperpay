"""Defines the manifest for the Saleor app."""

from django.conf import settings
from platform_plugin_hyperpay.saleor_app.client.subscriptions import TRANSACTION_INITIALIZE, PAYMENT_GATEWAY_INITIALIZE_SESSION

HYPERPAY_APP_ID = "platform.plugin.hyperpay"


def get_app_manifest():
    """
    Generate the application manifest for Saleor integration.

    The manifest defines the application's metadata, permissions, webhooks,
    and integration points that Saleor will use to interact with this plugin.

    Returns:
        dict: A dictionary containing the complete application manifest.
    """
    manifest = {
        'id': HYPERPAY_APP_ID,
        'version': '0.1.0',
        'requiredSaleorVersion': '^3.13',
        'name': 'platform-plugin-hyperpay',
        'author': 'NELC Team',
        'about': 'This is a test plugin for hyperpay payment processor.',

        'permissions': [
            'HANDLE_PAYMENTS',
            'MANAGE_CHECKOUTS',
            'MANAGE_APPS',
            'MANAGE_USERS',
            'MANAGE_STAFF',
            'MANAGE_TAXES',
            'MANAGE_MENUS',
            'MANAGE_PAGES',
            'MANAGE_ORDERS',
            'MANAGE_PLUGINS',
            'MANAGE_CHANNELS',
            'MANAGE_PRODUCTS',
            'MANAGE_SHIPPING',
            'MANAGE_SETTINGS',
            'MANAGE_CHECKOUTS',
            'MANAGE_DISCOUNTS',
            'MANAGE_GIFT_CARD',
            'MANAGE_TRANSLATIONS',
            'MANAGE_OBSERVABILITY',
            'MANAGE_ORDERS_IMPORT',
            'MANAGE_PAGE_TYPES_AND_ATTRIBUTES',
            'MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES'
        ],
        'appUrl': f'{settings.LMS_ROOT_URL}/hyperpay/saleor-app',
        'configurationUrl': f'{settings.LMS_ROOT_URL}/hyperpay/saleor-app/api/configuration',
        'tokenTargetUrl': f'{settings.LMS_ROOT_URL}/hyperpay/saleor-app/api/register',
        'dataPrivacy': 'Lorem ipsum',
        'brand': {
          'logo': {
            'default': f'{settings.LMS_ROOT_URL}/static/nelp-edx-theme-bragi/images/logo.png',
          }
        },
        'webhooks': [
          {
            'name': 'Transaction Initialize Session',
            'syncEvents': ['TRANSACTION_INITIALIZE_SESSION',],
            'query':  TRANSACTION_INITIALIZE,
            'targetUrl': f'{settings.LMS_ROOT_URL}/hyperpay/saleor-app/api/webhooks/transaction-initialize-session',
            'isActive': True,
          },
          {
            'name': 'Payment Gateway Initialize Session',
            'syncEvents': ['PAYMENT_GATEWAY_INITIALIZE_SESSION',],
            'query':  PAYMENT_GATEWAY_INITIALIZE_SESSION,
            'targetUrl': f'{settings.LMS_ROOT_URL}/hyperpay/saleor-app/api/webhooks/payment-gateway-initialize-session',
            'isActive': True,
          },

        ]
    }

    return manifest
