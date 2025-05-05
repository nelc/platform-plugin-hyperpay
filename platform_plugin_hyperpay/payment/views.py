
import logging
import re
from django.views.generic import View
import uuid
import requests
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
import base64

from django.conf import settings
from platform_plugin_hyperpay.processors import HyperPay, HyperPayMada, PaymentStatus
from platform_plugin_hyperpay.exceptions import HyperPayException
from django.shortcuts import redirect, render
from enum import Enum
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet
from django.urls import reverse
from django.http import JsonResponse
logger = logging.getLogger(__name__)


def generate_key(encryption_key, salt):
    """
    Generate the encryption key.
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        iterations=100000,
        salt=salt.encode(),
        backend=default_backend()
    )
    return base64.urlsafe_b64encode(kdf.derive(encryption_key.encode()))


def encrypt_string(message, encryption_key, salt):
    """
    Encrypt the string.
    """
    fernet = Fernet(generate_key(encryption_key, salt))
    return fernet.encrypt(message.encode()).decode('utf-8')


def decrypt_string(encrypted_message, encryption_key, salt):
    """
    Decrypt the encrypted string.
    """
    fernet = Fernet(generate_key(encryption_key, salt))
    return fernet.decrypt(encrypted_message.encode()).decode('utf-8')


class HyperPayPaymentPageView(View):
    """
    Render the template which loads the HyperPay payment form via JavaScript
    """
    template_name = 'payment/pay.html'

    @property
    def payment_processor(self):
        return HyperPay()

    def get(self, request):
        """
        Handles the GET request.
        """
        context = self.payment_processor.get_transaction_parameters(request=request)
        context["nonce_id"] = str(uuid.uuid4())
        return render(request, self.template_name, context)


class HyperMadaPayPaymentPageView(View):
    """
    Render the template which loads the HyperPay Mada payment form via JavaScript
    """
    template_name = 'payment/pay.html'

    @property
    def payment_processor(self):
        return HyperPayMada()



class HyperPayResponseView(View):
    """
    Handle the response from HyperPay after processing the payment.

    The result codes returned by HyperPay are documented at https://hyperpay.docs.oppwa.com/reference/resultCodes
    """
    PENDING_STATUS_URL_NAME = 'hyperpay-payment:status-check'
    PENDING_STATUS_PAGE_TITLE = 'HyperPay - Credit card - pending'

    # @method_decorator(transaction.non_atomic_requests)
    # @method_decorator(csrf_exempt)
    # def dispatch(self, request, *args, **kwargs):
    #     return super(HyperPayResponseView, self).dispatch(request, *args, **kwargs)

    @property
    def payment_processor(self):
        return HyperPay()


    def _handle_pending_status(self, request, encrypted_resource_path, resource_path):
        """
        Handles the pending status.
        """
        encrypted_resource_path_value = encrypt_string(
            resource_path,
            self.payment_processor.encryption_key,
            self.payment_processor.salt
        )
        context = {
            'title': self.PENDING_STATUS_PAGE_TITLE,
            'interval': self.payment_processor.pending_status_polling_interval
        }
        if encrypted_resource_path is not None:
            return render(request, 'payment/pending.html', context)

        request.session['hyperpay_dont_check_status'] = True
        return redirect(
            reverse(
                self.PENDING_STATUS_URL_NAME,
                kwargs={'encrypted_resource_path': encrypted_resource_path_value}
            )
        )

    def _get_resource_path(self, request, encrypted_resource_path):
        """
        Get the resource_path for checking the payment status.
        """
        if encrypted_resource_path is not None:
            resource_path = decrypt_string(
                encrypted_resource_path,
                self.payment_processor.encryption_key,
                self.payment_processor.salt
            )
        else:
            resource_path = request.GET.get('resourcePath')
        return resource_path

    def _get_check_status(self, request):
        """
        Get the value of the check_status variable.
        """
        check_status = True
        if 'hyperpay_dont_check_status' in request.session:
            check_status = False
            del request.session['hyperpay_dont_check_status']
        return check_status


    def get(self, request, encrypted_resource_path=None):
        """
        Handle the response from HyperPay and redirect to the appropriate page based on the status.
        """
        logger.info('Received a response from HyperPay: %s', request.GET)
        resource_path = self._get_resource_path(request, encrypted_resource_path)
        if resource_path is None:
            raise HyperPayException('Received an invalid response from HyperPay')
        check_status = self._get_check_status(request)
        verification_response = ''
        transaction_id = 'Unknown'

        try:
            status = PaymentStatus.PENDING
            if check_status:
                verification_response, status = self.payment_processor._verify_status(resource_path)
                if (verification_response and isinstance(verification_response, dict) and
                        verification_response.get('merchantTransactionId')):
                    transaction_id = verification_response['merchantTransactionId']
            if status == PaymentStatus.FAILURE:
                #return redirect(reverse('payment_error'))
                raise HyperPayException('Payment failed')
            if status == PaymentStatus.PENDING:
                return self._handle_pending_status(request, encrypted_resource_path, resource_path)

            transaction_id = verification_response['id']
        finally:
            logger.info('Transaction ID: %s received \n Verification_response:\n %s \n', transaction_id, verification_response)

        try:
            if verification_response:
                order_data = self.payment_processor.complete_saleor_checkout(verification_response)
        except Exception as exc:  # pylint:disable=broad-except
            logger.exception(
                'Attempts to handle payment for basket [%d] failed due to [%s].',
                transaction_id,
                exc.__class__.__name__
            )
        order_id = order_data.get('id')
        order_url = f"{settings.SALEOR_STOREFRONT_HOST}/order?order={order_id}"
        return redirect(order_url)
