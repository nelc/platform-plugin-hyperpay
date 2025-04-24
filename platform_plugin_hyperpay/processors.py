from django.utils.translation import gettext_lazy as _
from django.conf import settings
from platform_plugin_hyperpay.exceptions import HyperPayException
from urllib.parse import urlencode
from django.urls import reverse

import requests

def format_price(price):
    """
    Return the price in the expected format.
    """
    return '{:0.2f}'.format(price)


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


    def __init__(self):
        self.access_token = settings.HYPERPAY_CONFIG[self.NAME]['access_token']
        self.entity_id = settings.HYPERPAY_CONFIG[self.NAME]['entity_id']
        self.return_url = settings.HYPERPAY_CONFIG[self.NAME]['return_url']
        self.currency = settings.HYPERPAY_CONFIG[self.NAME]['currency']
        self.hyper_pay_api_base_url = settings.HYPERPAY_CONFIG[self.NAME].get('hyper_pay_api_base_url', 'https://test.oppwa.com')
        self.test_mode = settings.HYPERPAY_CONFIG[self.NAME].get('test_mode')
        self.encryption_key = settings.HYPERPAY_CONFIG[self.NAME].get('encryption_key', settings.SECRET_KEY)
        self.salt = settings.HYPERPAY_CONFIG[self.NAME]['salt']

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
        print("--------------\n")
        print(request_data)
        try:
            response = requests.post(
                checkouts_api_url,
                request_data,
                headers=self.authentication_headers
            )
        except Exception as exc:
            raise HyperPayException('Error creating a checkout. {}'.format(exc))

        data = response.json()
        print(data)
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
            'payment_page_url': reverse('hyperpay:payment-form'),
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

class HyperPayMada(HyperPay):
    """
    HyperPay payment processor for mada.
    """
    NAME = 'hyperpay_mada'
    PAYMENT_MODE = _('mada')
    BRANDS = "MADA"
    CHECKOUT_TEXT = _("Checkout with mada")
    PAYMENT_TYPE = 'DB'
