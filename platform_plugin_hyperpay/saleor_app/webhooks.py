import json
import logging

from django.core.cache import cache
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger(__name__)

@csrf_exempt
def transaction_initialize(request):
    """
    Handle the transaction init from Saleor.
    Args:
        request: The HTTP request object containing the webhook payload.
    Returns:
        JsonResponse: A JSON response indicating success or failure.
    """
    payload = {}
    if request.method == "POST":
        payload = json.loads(request.body)
    payload = json.loads(request.body)
    logger.info("received webhook payload: %s", payload)

    amount = payload.get("action",{}).get("amount")
    data = payload.get("data", {})
    response = {
        "pspReference": data.get("id"),
        "result": "CHARGE_SUCCESS",
        "hyperpay_result_code": data.get("code"),
        "description": data.get("description"),
        "message": "Great success!",
        "actions": "REFUND", # todo create this function
        "amount": amount,
        "externalUrl": "https://example.com",
      }
    logger.info("return response webhook payload: %s", response)

    return JsonResponse(
        response,
        status=200,
    )


@csrf_exempt
def payment_gateway_initialize_session(request):
    """
    Handle the payment_gateway_init session from Saleor.
    This endpoint receives notifications when orders are fully paid in the Saleor system
    and enrolls the user in the specified course.
    Args:
        request: The HTTP request object containing the webhook payload.
    Returns:
        JsonResponse: A JSON response indicating success or failure.
    """
    payload = {}
    if request.method == "POST":
        payload = json.loads(request.body)
    logger.info("received webhook payload: %s", payload)

    amount = payload.get("action",{}).get("amount")
    data = payload.get("data", {})
    response = {
        "data": {
            "payment_url": cache.get('payment_url', ''),
            "payment_button_image" : cache.get('payment_button_image', ''),
            "hyper_pay_api_base_url": cache.get('hyper_pay_api_base_url', ''),
            "access_token": cache.get('access_token', ''),
        }
      }
    logger.info("return response webhook payload: %s", response)

    return JsonResponse(
        response,
        status=200,
    )
