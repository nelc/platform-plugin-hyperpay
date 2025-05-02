"""Views for Saleor Hyperpay app integration."""

import json
import logging

from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from platform_plugin_hyperpay.saleor_app.manifest import get_app_manifest

logger = logging.getLogger(__name__)


@csrf_exempt
def get_saleor_app_manifest(request):
    """
    Provide the Saleor app manifest.
    This endpoint returns the application manifest that Saleor uses to register
    and configure the application within its ecosystem.
    Args:
        request: The HTTP request object.
    Returns:
        JsonResponse: A JSON response containing the application manifest.
    """
    return JsonResponse(get_app_manifest(), safe=True)


@csrf_exempt
def register_saleor_app_token(request):
    """
    Register the authentication token received from Saleor.
    This endpoint receives and stores the authentication token that will be used
    for subsequent API calls to the Saleor API.
    Args:
        request: The HTTP request object containing the auth token.
    Returns:
        JsonResponse: A JSON response indicating the token was successfully received.
    """
    payload = json.loads(request.body.decode("utf-8"))
    token = payload.get("auth_token")
    settings.SALEOR_API_TOKEN = token

    return JsonResponse(
        {"success": True, "message": "Token received successfully."},
        status=200,
    )


@csrf_exempt
def configure_saleor_app(request):
    """
    This view renders the configuration form and saves the data in cache.
    """
    if request.method == "POST":
        payment_url = request.POST.get('payment_url')
        payment_button_image = request.POST.get('payment_button_image')
        hyper_pay_api_base_url = request.POST.get('hyper_pay_api_base_url')
        access_token = request.POST.get('access_token')

        cache.set('payment_url', payment_url, timeout=36000)
        cache.set('payment_button_image', payment_button_image, timeout=36000)
        cache.set('hyper_pay_api_base_url', hyper_pay_api_base_url, timeout=36000)
        cache.set('access_token', access_token, timeout=36000)

        return render(request, 'saleor_app/configure.html', {
            'payment_url': payment_url,
            'hyper_pay_api_base_url': hyper_pay_api_base_url,
            'access_token': access_token,
            'success': True,
        })
    payment_url = cache.get('payment_url', '')
    payment_button_image = cache.get('payment_button_image', '')
    hyper_pay_api_base_url = cache.get('hyper_pay_api_base_url', '')
    access_token = cache.get('access_token', '')

    return render(request, 'saleor_app/configure.html', {
        'payment_url': payment_url,
        'hyper_pay_api_base_url': hyper_pay_api_base_url,
        'access_token': access_token,
        'success': False,
    })
