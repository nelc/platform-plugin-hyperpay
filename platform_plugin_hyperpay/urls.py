"""
URLs for platform_plugin_hyperpay.
"""
from django.urls import path  # pylint: disable=unused-import
from platform_plugin_hyperpay import views

urlpatterns = [
    # TODO: Fill in URL patterns and views here.
    # re_path(r'', TemplateView.as_view(template_name="platform_plugin_hyperpay/base.html")),
    path('info/', views.info_view, name='hyperpay-info'),
]
