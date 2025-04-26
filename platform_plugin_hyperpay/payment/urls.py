"""eox_nelp course_api  urls
"""
from django.urls import include, path
from platform_plugin_hyperpay.payment import views
app_name = 'platform_plugin_hyperpay'  # pylint: disable=invalid-name

urlpatterns = [
    path('pay/', views.HyperPayPaymentPageView.as_view(), name='pay-page'),
    path('submit/', views.HyperPayResponseView.as_view(), name='submit-page'),
    path('status/(?P<encrypted_resource_path>.+)/$', views.HyperPayResponseView.as_view(), name='status-check'),
]
