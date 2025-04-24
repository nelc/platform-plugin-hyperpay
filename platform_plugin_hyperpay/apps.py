"""
platform_plugin_hyperpay Django application initialization.
"""

from django.apps import AppConfig
from edx_django_utils.plugins import PluginSettings, PluginURLs

class PlatformPluginHyperpayConfig(AppConfig):
    """
    Configuration for the platform_plugin_hyperpay Django application.
    """

    name = 'platform_plugin_hyperpay'
    plugin_app = {
        PluginURLs.CONFIG: {
            "lms.djangoapp": {
                PluginURLs.NAMESPACE: "",
                PluginURLs.REGEX: r"^hyperpay/",
                PluginURLs.RELATIVE_PATH: "urls",
            },
        },
        PluginSettings.CONFIG: {
            "lms.djangoapp": {
                "production": {PluginSettings.RELATIVE_PATH: "settings.production"},
                "common": {PluginSettings.RELATIVE_PATH: "settings.common"},
            },
        },
    }
