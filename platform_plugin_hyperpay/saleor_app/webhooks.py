import json
import logging
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse



logger = logging.getLogger(__name__)

@csrf_exempt
def transaction_initialize(request):
    """
    Handle the order fully paid webhook from Saleor.
    This endpoint receives notifications when orders are fully paid in the Saleor system
    and enrolls the user in the specified course.
    Args:
        request: The HTTP request object containing the webhook payload.
    Returns:
        JsonResponse: A JSON response indicating success or failure.
    """
    payload = json.loads(request.body)
    logger.info("received webhook payload: %s", payload)

    action_type = payload.get("action",{}).get("actionType")
    amount = payload.get("action",{}).get("amount")
    data = payload.get("data", {})
    response = {
        "pspReference": "fixedUUID",
        "result": data.get("event",{}).get("type"),
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
