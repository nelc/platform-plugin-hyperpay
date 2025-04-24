
from django.views.generic import View
import uuid
import requests
from django.conf import settings
from platform_plugin_hyperpay.processors import HyperPay, HyperPayMada
from platform_plugin_hyperpay.exceptions import HyperPayException
from django.shortcuts import redirect, render


class HyperPayPaymentPageView(View):
    """
    Render the template which loads the HyperPay payment form via JavaScript
    """
    template_name = 'payment.html'

    def get(self, request):
        """
        Handles the GET request.
        """
        if request.GET["processor"] == HyperPay.NAME:
            processor = HyperPay()
        elif request.GET["processor"] == HyperPayMada.NAME:
            processor = HyperPayMada()
        else:
            raise HyperPayException('Invalid processor name.')


        context = processor.get_transaction_parameters(request=request)

        context["nonce_id"] = str(uuid.uuid4())
        return render(request, self.template_name, context)
