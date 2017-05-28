# -*- coding: utf-8 -*-
import collections
import json
import urlparse
import string
from decimal import Decimal
import uuid
import hashlib
import hmac
from gettext import gettext as _
import requests
import warnings

from common import (PaymentCommon, FORM, Form, PaymentResponse, PAID, ERROR,
        CANCELED, ResponseError)

__all__ = ['Payment']


class Payment(PaymentCommon):
    '''
    Payment backend module for the ATOS/SIPS system used by many French banks.

    The necessary options are:
    - merchant_id
    - secret_key
    - normal_return_url
    - automatic_return_url

    It was writtent using the documentation from file:

        Worldline Benelux_Sips_Technical_integration_guide_Version_1.5.pdf

    '''
    URL = {
        'test': 'https://payment-webinit.simu.sips-atos.com/paymentInit',
        'prod': 'https://payment-webinit.sips-atos.com/paymentInit',
    }
    WS_URL = {
        'test': 'https://office-server.test.sips-atos.com',
        'prod': 'https://office-server.sips-atos.com',
    }

    INTERFACE_VERSION = 'HP_2.3'
    RESPONSE_CODES = {
        '00': 'Authorisation accepted',
        '02': 'Authorisation request to be performed via telephone with the issuer, as the '
              'card authorisation threshold has been exceeded, if the forcing is authorised for '
              'the merchant',
        '03': 'Invalid distance selling contract',
        '05': 'Authorisation refused',
        '12': 'Invalid transaction, verify the parameters transferred in the request.',
        '14': 'Invalid bank details or card security code',
        '17': 'Buyer cancellation',
        '24': 'Operation impossible. The operation the merchant wishes to perform is not '
              'compatible with the status of the transaction.',
        '25': 'Transaction not found in the Sips database',
        '30': 'Format error',
        '34': 'Suspicion of fraud',
        '40': 'Function not supported: the operation that the merchant would like to perform '
              'is not part of the list of operations for which the merchant is authorised',
        '51': 'Amount too high',
        '54': 'Card is past expiry date',
        '60': 'Transaction pending',
        '63': 'Security rules not observed, transaction stopped',
        '75': 'Number of attempts at entering the card number exceeded',
        '90': 'Service temporarily unavailable',
        '94': 'Duplicated transaction: for a given day, the TransactionReference has already been '
              'used',
        '97': 'Timeframe exceeded, transaction refused',
        '99': 'Temporary problem at the Sips Office Server level',
    }
    TEST_MERCHANT_ID = '002001000000001'

    description = {
        'caption': 'SIPS 2',
        'parameters': [
            {
                'name': 'platform',
                'caption': _('Platform'),
                'default': 'test',
                'choices': ['test', 'prod'],
                'required': True,
            },
            {
                'name': 'merchant_id',
                'caption': _('Merchant ID'),
                'default': TEST_MERCHANT_ID,
                'required': True,
            },
            {
                'name': 'secret_key',
                'caption': _('Secret Key'),
                'default': '002001000000001_KEY1',
                'required': True,
            },
            {
                'name': 'key_version',
                'caption': _('Key Version'),
                'default': '1',
                'required': True,
            },
            {
                'name': 'normal_return_url',
                'caption': _('Normal return URL'),
                'default': '',
                'required': True,
            },
            {
                'name': 'automatic_return_url',
                'caption': _('Automatic return URL'),
                'required': False,
            },
            {
                'name': 'currency_code',
                'caption': _('Currency code'),
                'default': '978',
                'choices': ['978'],
                'required': True,
            },
            {
                'name': 'capture_mode',
                'caption': _('Capture Mode'),
                'default': 'AUTHOR_CAPTURE',
                'choices': ['AUTHOR_CAPTURE', 'IMMEDIATE', 'VALIDATION'],
                'required': True,
            },
            {
                'name': 'capture_day',
                'caption': _('Capture Day'),
                'required': False,
            },
            {
                'name': 'payment_means',
                'caption': _('Payment Means'),
                'required': False
            }
        ],
    }

    def encode_data(self, data):
        return u'|'.join(u'%s=%s' % (unicode(key), unicode(value))
                         for key, value in data.iteritems())

    def seal_data(self, data):
        s = self.encode_data(data)
        s += unicode(self.secret_key)
        s = s.encode('utf-8')
        s = hashlib.sha256(s).hexdigest()
        return s

    def get_data(self):
        data = collections.OrderedDict()
        data['merchantId'] = self.merchant_id
        data['keyVersion'] = self.key_version
        data['normalReturnUrl'] = self.normal_return_url
        if self.automatic_return_url:
            data['automaticResponseUrl'] = self.automatic_return_url
        data['currencyCode'] = self.currency_code
        data['captureMode'] = self.capture_mode
        if self.capture_day:
            data['captureDay'] = self.capture_day
        if self.payment_means:
            data['paymentMeanBrandList'] = self.payment_means
        return data

    def get_url(self):
        return self.URL[self.platform]

    def request(self, amount, name=None, first_name=None, last_name=None,
                address=None, email=None, phone=None, orderid=None,
                info1=None, info2=None, info3=None, next_url=None, **kwargs):
        data = self.get_data()
        transaction_id = self.transaction_id(6, string.digits, 'sips2', data['merchantId'])
        data['transactionReference'] = unicode(transaction_id)
        data['orderId'] = orderid or unicode(uuid.uuid4()).replace('-', '')
        data['amount'] = unicode(int(Decimal(amount) * 100))
        if email:
            data['billingContact.email'] = email
        if 'captureDay' in kwargs:
            data['captureDay'] == kwargs.get('captureDay')
        normal_return_url = self.normal_return_url
        if next_url and not normal_return_url:
            warnings.warn("passing next_url to request() is deprecated, "
                          "set normal_return_url in options", DeprecationWarning)
            normal_return_url = next_url
        if normal_return_url:
            data['normalReturnUrl'] = normal_return_url
        form = Form(
            url=self.get_url(),
            method='POST',
            fields=[
                {
                    'type': 'hidden',
                    'name': 'Data',
                    'value': self.encode_data(data)
                },
                {
                    'type': 'hidden',
                    'name': 'Seal',
                    'value': self.seal_data(data),
                },
                {
                    'type': 'hidden',
                    'name': 'InterfaceVersion',
                    'value': self.INTERFACE_VERSION,
                },
            ])
        self.logger.debug('emitting request %r', data)
        return transaction_id, FORM, form

    def decode_data(self, data):
        data = data.split('|')
        data = [map(unicode, p.split('=', 1)) for p in data]
        return collections.OrderedDict(data)

    def check_seal(self, data, seal):
        return seal == self.seal_data(data)

    response_code_to_result = {
        '00': PAID,
        '17': CANCELED,
    }

    def response(self, query_string, **kwargs):
        form = urlparse.parse_qs(query_string)
        if not set(form) >= set(['Data', 'Seal', 'InterfaceVersion']):
            raise ResponseError()
        self.logger.debug('received query string %r', form)
        data = self.decode_data(form['Data'][0])
        seal = form['Seal'][0]
        self.logger.debug('parsed response %r seal %r', data, seal)
        signed = self.check_seal(data, seal)
        response_code = data['responseCode']
        transaction_id = data.get('transactionReference')
        result = self.response_code_to_result.get(response_code, ERROR)
        merchant_id = data.get('merchantId')
        test = merchant_id == self.TEST_MERCHANT_ID
        return PaymentResponse(
            result=result,
            signed=signed,
            bank_data=data,
            order_id=transaction_id,
            transaction_id=data.get('authorisationId'),
            bank_status=self.RESPONSE_CODES.get(response_code, u'unknown code - ' + response_code),
            test=test)

    def get_seal_for_json_ws_data(self, data):
        data_to_send = []
        for key in sorted(data.keys()):
            if key in ('keyVersion', 'sealAlgorithm', 'seal'):
                continue
            data_to_send.append(unicode(data[key]))
        data_to_send_str = u''.join(data_to_send).encode('utf-8')
        return hmac.new(unicode(self.secret_key).encode('utf-8'), data_to_send_str, hashlib.sha256).hexdigest()

    def perform_cash_management_operation(self, endpoint, data):
        data['merchantId'] = self.merchant_id
        data['interfaceVersion'] = 'CR_WS_2.3'
        data['keyVersion'] = self.key_version
        data['currencyCode'] = self.currency_code
        data['seal'] = self.get_seal_for_json_ws_data(data)
        url = self.WS_URL.get(self.platform) + '/rs-services/v2/cashManagement/%s' % endpoint
        self.logger.debug('posting %r to %s endpoint', data, endpoint)
        response = requests.post(url, data=json.dumps(data),
                headers={'content-type': 'application/json',
                         'accept': 'application/json'})
        self.logger.debug('received %r', response.content)
        response.raise_for_status()
        json_response = response.json()
        if self.platform == 'prod':
            # test environment doesn't set seal
            if json_response.get('seal') != self.get_seal_for_json_ws_data(json_response):
                raise ResponseError('wrong signature on response')
        if json_response.get('responseCode') != '00':
            raise ResponseError('non-zero response code (%s)' % json_response)
        return json_response

    def cancel(self, amount, bank_data, **kwargs):
        data = {}
        data['operationAmount'] = unicode(int(Decimal(amount) * 100))
        data['transactionReference'] = bank_data.get('transactionReference')
        return self.perform_cash_management_operation('cancel', data)

    def validate(self, amount, bank_data, **kwargs):
        data = {}
        data['operationAmount'] = unicode(int(Decimal(amount) * 100))
        data['transactionReference'] = bank_data.get('transactionReference')
        return self.perform_cash_management_operation('validate', data)

    def diagnostic(self, amount, bank_data, **kwargs):
        data = {}
        data['transactionReference'] = bank_data.get('transactionReference')
        data['merchantId'] = self.merchant_id
        data['interfaceVersion'] = 'DR_WS_2.9'
        data['keyVersion'] = self.key_version
        data['seal'] = self.get_seal_for_json_ws_data(data)
        url = self.WS_URL.get(self.platform) + '/rs-services/v2/diagnostic/getTransactionData'
        self.logger.debug('posting %r to %s endpoint', data, 'diagnostic')
        response = requests.post(url, data=json.dumps(data),
                headers={'content-type': 'application/json',
                         'accept': 'application/json'})
        self.logger.debug('received %r', response.content)
        response.raise_for_status()
        return response.json()
