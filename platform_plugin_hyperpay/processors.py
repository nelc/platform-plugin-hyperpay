from django.utils.translation import gettext_lazy as _
from django.conf import settings
from platform_plugin_hyperpay.exceptions import HyperPayException
from urllib.parse import urlencode
from django.urls import reverse
from enum import Enum

import requests
import logging
import re

logger = logging.getLogger(__name__)


def format_price(price):
    """
    Return the price in the expected format.
    """
    return '{:0.2f}'.format(price)

class PaymentStatus(Enum):
    SUCCESS = 0
    PENDING = 1
    FAILURE = 2

class HyperPay:
    """
    HyperPay payment processor.

    For reference, see https://hyperpay.docs.oppwa.com/integration-guide and
    https://hyperpay.docs.oppwa.com/reference/parameters.
    """

    NAME = 'hyperpay'
    PAYMENT_MODE = _('Credit card')
    PAYMENT_TYPE = 'DB'
    CHECKOUTS_ENDPOINT = '/v1/checkouts'
    PAYMENT_WIDGET_JS_PATH = '/v1/paymentWidgets.js'
    RESULT_CODE_SUCCESSFULLY_CREATED_CHECKOUT = '000.200.100'
    CART_ITEM_TYPE_DIGITAL = 'DIGITAL'
    BILLING_ADDRESS_STREET1_MAX_LEN = 95
    BILLING_ADDRESS_STREET2_MAX_LEN = 100
    BRANDS = "VISA MASTER"
    CHECKOUT_TEXT = _("Checkout with credit card")

    SUCCESS_CODES_REGEX = re.compile(r'^(000\.000\.|000\.100\.1|000\.[36])')
    SUCCESS_MANUAL_REVIEW_CODES_REGEX = re.compile(r'^(000\.400\.0[^3]|000\.400\.[0-1]{2}0)')
    PENDING_CHANGEABLE_SOON_CODES_REGEX = re.compile(r'^(000\.200)')
    PENDING_NOT_CHANGEABLE_SOON_CODES_REGEX = re.compile(r'^(800\.400\.5|100\.400\.500)')
    PENDING_STATUS_URL_NAME = 'hyperpay:status-check'
    PENDING_STATUS_PAGE_TITLE = 'HyperPay - Credit card - pending'


    def __init__(self):
        self.access_token = settings.HYPERPAY_CONFIG[self.NAME]['access_token']
        self.entity_id = settings.HYPERPAY_CONFIG[self.NAME]['entity_id']
        self.return_url = settings.HYPERPAY_CONFIG[self.NAME]['return_url']
        self.currency = settings.HYPERPAY_CONFIG[self.NAME]['currency']
        self.hyper_pay_api_base_url = settings.HYPERPAY_CONFIG[self.NAME].get('hyper_pay_api_base_url', 'https://test.oppwa.com')
        self.test_mode = settings.HYPERPAY_CONFIG[self.NAME].get('test_mode')
        self.encryption_key = settings.HYPERPAY_CONFIG[self.NAME].get('encryption_key', settings.SECRET_KEY)
        self.salt = settings.HYPERPAY_CONFIG[self.NAME]['salt']
        self.pending_status_polling_interval = 30

    @property
    def authentication_headers(self):
        """
        Return the authentication headers.
        """
        return {
            'Authorization': 'Bearer {}'.format(self.access_token)
        }

    def _get_basket_data(self, request):
        """
        Prepare the basket data and return the basket data.
        """
        def get_cart_field(index, name):
            """
            Return the cart field name.
            """
            return 'cart.items[{}].{}'.format(index, name)

        basket_data = {
            'amount': format_price(float(request.GET['amount'])),
            'currency': self.currency,
            'merchantTransactionId': request.GET['merchantTransactionId'],
            'merchantMemo': request.GET['merchantMemo'],

        }
        index = 0 # Initialize index for cart items
        cart_data = {
            get_cart_field(index, 'name'): request.GET['name'],
            get_cart_field(index, 'quantity'): request.GET['quantity'],
            get_cart_field(index, 'type'): self.CART_ITEM_TYPE_DIGITAL,
            get_cart_field(index, 'sku'): request.GET['SKU'],
            get_cart_field(index, 'price'): request.GET['price'],
            get_cart_field(index, 'totalAmount'): request.GET['totalamount'],
        }
        basket_data.update(cart_data)

        return basket_data

    def _get_profile_data(self, request):
        if not request.user.is_authenticated:
            raise HyperPayException('User is not authenticated.')

        return {
            'customer.email': request.user.email,
            'customer.givenName': request.user.first_name,
            'customer.surname': request.user.last_name,
        }

    def _get_checkout_data(self, request):
        """
        Prepare the checkout and return the checkout data.
        """
        checkouts_api_url = self.hyper_pay_api_base_url + self.CHECKOUTS_ENDPOINT
        request_data = {
            'entityId': self.entity_id,
            'paymentType': self.PAYMENT_TYPE,
            'integrity': True,
        }
        if self.test_mode:
            request_data['testMode'] = self.test_mode

        request_data.update(self._get_basket_data(request))
        request_data.update(self._get_profile_data(request))
        logger.info("--------------\n")
        logger.info(request_data)
        try:
            response = requests.post(
                checkouts_api_url,
                request_data,
                headers=self.authentication_headers
            )
        except Exception as exc:
            raise HyperPayException('Error creating a checkout. {}'.format(exc))

        data = response.json()
        logger.info(data)
        if 'result' not in data or 'code' not in data['result']:
            raise HyperPayException(
                'Error creating checkout. Invalid response from HyperPay.'
            )
        result_code = data['result']['code']
        if result_code != self.RESULT_CODE_SUCCESSFULLY_CREATED_CHECKOUT:
            raise HyperPayException(
                'Error creating checkout. HyperPay status code: {}'.format(result_code)
            )
        return data

    def get_transaction_parameters(self,request=None):
        """
        Return the transaction parameters needed for this processor.
        """
        checkout_data = self._get_checkout_data(request)
        payment_widget_js_url = '{}?{}'.format(
            self.hyper_pay_api_base_url + self.PAYMENT_WIDGET_JS_PATH,
            urlencode({'checkoutId': checkout_data['id']})
        )
        transaction_parameters = {
            'payment_widget_js': payment_widget_js_url,
            'payment_page_url': reverse('hyperpay-payment:pay-page'),
            'payment_result_url': self.return_url,
            'brands': self.BRANDS,
            'payment_mode': self.PAYMENT_MODE,
            'locale': request.LANGUAGE_CODE.split('-')[0],
            #'csrfmiddlewaretoken': get_token(request),
            'integrity': checkout_data['integrity'],
            'hyper_pay_api_base_url': self.hyper_pay_api_base_url,
            'extra_hosts_content_security_policy': getattr(settings, 'EXTRA_HOSTS_CONTENT_SECURITY_POLICY', ''),
        }
        return transaction_parameters

    def _verify_status(self, resource_path):
        """
        Verify the status of the payment.
        """
        status = PaymentStatus.SUCCESS
        payment_status_endpoint = "{}?{}".format(
            self.payment_processor.hyper_pay_api_base_url + resource_path,
            urlencode({'entityId': self.payment_processor.configuration['entity_id']})
        )
        response = requests.get(payment_status_endpoint, headers=self.payment_processor.authentication_headers)
        response_data = response.json()

        result_code = response_data['result']['code']
        if not response.ok:
            logger.error('Received a non-success response status code from HyperPay %s', response.status_code)
            status = PaymentStatus.FAILURE
        elif self.PENDING_CHANGEABLE_SOON_CODES_REGEX.search(result_code):
            logger.warning(
                'Received a pending status code %s from HyperPay for payment id %s.',
                result_code,
                response_data['id']
            )
            status = PaymentStatus.PENDING
        elif self.PENDING_NOT_CHANGEABLE_SOON_CODES_REGEX.search(result_code):
            logger.warning(
                'Received a pending status code %s from HyperPay for payment id %s. As this can change '
                'after several days, treating it as a failure.',
                result_code,
                response_data['id']
            )
            status = PaymentStatus.FAILURE
        elif self.SUCCESS_CODES_REGEX.search(result_code):
            logger.info(
                'Received a success status code %s from HyperPay for payment id %s.',
                result_code,
                response_data['id']
            )
        elif self.SUCCESS_MANUAL_REVIEW_CODES_REGEX.search(result_code):
            logger.error(
                'Received a success status code %s from HyperPay which requires manual verification for payment id %s.'
                'Treating it as a failed transaction.',
                result_code,
                response_data['id']
            )

            # This is a temporary change till we get clarity on whether this should be treated as a failure.
            status = PaymentStatus.FAILURE
        else:
            logger.error(
                'Received a rejection status code %s from HyperPay for payment id %s',
                result_code,
                response_data['id']
            )
            status = PaymentStatus.FAILURE

        return response_data, status

    def _verify_status(self, resource_path):
        """
        Verify the status of the payment.
        """
        status = PaymentStatus.SUCCESS
        payment_status_endpoint = "{}?{}".format(
            self.hyper_pay_api_base_url + resource_path,
            urlencode({'entityId': self.entity_id})
        )
        response = requests.get(payment_status_endpoint, headers=self.authentication_headers)
        response_data = response.json()

        result_code = response_data['result']['code']
        if not response.ok:
            logger.error('Received a non-success response status code from HyperPay %s', response.status_code)
            status = PaymentStatus.FAILURE
        elif self.PENDING_CHANGEABLE_SOON_CODES_REGEX.search(result_code):
            logger.warning(
                'Received a pending status code %s from HyperPay for payment id %s.',
                result_code,
                response_data['id']
            )
            status = PaymentStatus.PENDING
        elif self.PENDING_NOT_CHANGEABLE_SOON_CODES_REGEX.search(result_code):
            logger.warning(
                'Received a pending status code %s from HyperPay for payment id %s. As this can change '
                'after several days, treating it as a failure.',
                result_code,
                response_data['id']
            )
            status = PaymentStatus.FAILURE
        elif self.SUCCESS_CODES_REGEX.search(result_code):
            logger.info(
                'Received a success status code %s from HyperPay for payment id %s.',
                result_code,
                response_data['id']
            )
        elif self.SUCCESS_MANUAL_REVIEW_CODES_REGEX.search(result_code):
            logger.error(
                'Received a success status code %s from HyperPay which requires manual verification for payment id %s.'
                'Treating it as a failed transaction.',
                result_code,
                response_data['id']
            )

            # This is a temporary change till we get clarity on whether this should be treated as a failure.
            status = PaymentStatus.FAILURE
        else:
            logger.error(
                'Received a rejection status code %s from HyperPay for payment id %s',
                result_code,
                response_data['id']
            )
            status = PaymentStatus.FAILURE

        return response_data, status

class HyperPayMada(HyperPay):
    """
    HyperPay payment processor for mada.
    """
    NAME = 'hyperpay_mada'
    PAYMENT_MODE = _('mada')
    BRANDS = "MADA"
    CHECKOUT_TEXT = _("Checkout with mada")
    PAYMENT_TYPE = 'DB'
