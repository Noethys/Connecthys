# -*- coding: utf-8 -*-
import urlparse
import string
import subprocess
from decimal import Decimal
import logging
import os
import os.path
import uuid
import warnings

from common import PaymentCommon, HTML, PaymentResponse, ResponseError
from cb import CB_RESPONSE_CODES

'''
Payment backend module for the ATOS/SIPS system used by many Frenck banks.

It use the middleware given by the bank.

The necessary options are:

 - pathfile, to indicate the absolute path of the pathfile file given by the
   bank,
 - binpath, the path of the directory containing the request and response
   executables,

All the other needed parameters SHOULD already be set in the parmcom files
contained in the middleware distribution file.

'''

__all__ = ['Payment']

BINPATH = 'binpath'
PATHFILE = 'pathfile'
AUTHORISATION_ID = 'authorisation_id'
REQUEST_VALID_PARAMS = ['merchant_id', 'merchant_country', 'amount',
    'currency_code', 'pathfile', 'normal_return_url', 'cancel_return_url',
    'automatic_response_url', 'language', 'payment_means', 'header_flag',
    'capture_day', 'capture_mode', 'bgcolor', 'block_align', 'block_order',
    'textcolor', 'receipt_complement', 'caddie', 'customer_id',
    'customer_email', 'customer_ip_address', 'data', 'return_context',
    'target', 'order_id']

RESPONSE_PARAMS = ['code', 'error', 'merchant_id', 'merchant_country',
    'amount', 'transaction_id', 'payment_means', 'transmission_date',
    'payment_time', 'payment_date', 'response_code', 'payment_certificate',
    AUTHORISATION_ID, 'currency_code', 'card_number', 'cvv_flag',
    'cvv_response_code', 'bank_response_code', 'complementary_code',
    'complementary_info', 'return_context', 'caddie', 'receipt_complement',
    'merchant_language', 'language', 'customer_id', 'order_id',
    'customer_email', 'customer_ip_address', 'capture_day', 'capture_mode',
    'data', ]

DATA = 'DATA'
PARAMS = 'params'

TRANSACTION_ID = 'transaction_id'
ORDER_ID = 'order_id'
MERCHANT_ID = 'merchant_id'
RESPONSE_CODE = 'response_code'

DEFAULT_PARAMS = {'merchant_id': '014213245611111',
                  'merchant_country': 'fr',
                  'currency_code': '978'}

LOGGER = logging.getLogger(__name__)

CB_BANK_RESPONSE_CODES = CB_RESPONSE_CODES

AMEX_BANK_RESPONSE_CODE = {
'00': 'Transaction approuvée ou traitée avec succès',
'02': 'Dépassement de plafond',
'04': 'Conserver la carte',
'05': 'Ne pas honorer',
'97': 'Échéance de la temporisation de surveillance globale',
}

FINAREF_BANK_RESPONSE_CODE = {
'00': 'Transaction approuvée',
'03': 'Commerçant inconnu - Identifiant de commerçant incorrect',
'05': 'Compte / Porteur avec statut bloqué ou invalide',
'11': 'Compte / porteur inconnu',
'16': 'Provision insuffisante',
'20': 'Commerçant invalide - Code monnaie incorrect - ' + \
      'Opération commerciale inconnue - Opération commerciale invalide',
'80': 'Transaction approuvée avec dépassement',
'81': 'Transaction approuvée avec augmentation capital',
'82': 'Transaction approuvée NPAI',
'83': 'Compte / porteur invalide',
}


class Payment(PaymentCommon):
    description = {
            'caption': 'SIPS',
            'parameters': [{
                'name': 'merchand_id',
                },
                {'name': 'merchant_country', },
                {'name': 'currency_code', }
            ],
    }

    def __init__(self, options, logger=None):
        super(Payment, self).__init__(options, logger=logger)
        self.options = options
        self.binpath = self.options.pop(BINPATH)
        self.logger.debug('initializing sips payment class with %s' % options)

    def execute(self, executable, params):
        if PATHFILE in self.options:
            params[PATHFILE] = self.options[PATHFILE]
        executable = os.path.join(self.binpath, executable)
        args = [executable] + ["%s=%s" % p for p in params.iteritems()]
        self.logger.debug('executing %s' % args)
        result,_ = subprocess.Popen(' '.join(args),
                stdout=subprocess.PIPE, shell=True).communicate()
        try:
            if result[0] == '!':
                result = result[1:]
            if result[-1] == '!':
                result = result[:-1]
        except IndexError:
            raise ValueError("Invalid response", result)
            return False
        result = result.split('!')
        self.logger.debug('got response %s' % result)
        return result

    def get_request_params(self):
        params = DEFAULT_PARAMS.copy()
        params.update(self.options)
        return params

    def request(self, amount, name=None, address=None, email=None, phone=None, orderid=None,
            info1=None, info2=None, info3=None, next_url=None, **kwargs):
        params = self.get_request_params()
        transaction_id = self.transaction_id(6, string.digits, 'sips',
                params[MERCHANT_ID])
        params[TRANSACTION_ID] = transaction_id
        params[ORDER_ID] = orderid or str(uuid.uuid4())
        params[ORDER_ID] = params[ORDER_ID].replace('-', '')
        params['amount'] = str(int(Decimal(amount) * 100))
        if email:
            params['customer_email'] = email
        normal_return_url = self.normal_return_url
        if next_url and not normal_return_url:
            warnings.warn("passing next_url to request() is deprecated, "
                          "set normal_return_url in options", DeprecationWarning)
            normal_return_url = next_url
        if normal_return_url:
            params['normal_return_url'] = normal_return_url
        code, error, form = self.execute('request', params)
        if int(code) == 0:
            return params[ORDER_ID], HTML, form
        else:
            raise RuntimeError('sips/request returned -1: %s' % error)

    def response(self, query_string, **kwargs):
        form = urlparse.parse_qs(query_string)
        if not DATA in form:
            raise ResponseError()
        params = {'message': form[DATA][0]}
        result = self.execute('response', params)
        d = dict(zip(RESPONSE_PARAMS, result))
        # The reference identifier for the payment is the authorisation_id
        d[self.BANK_ID] = d.get(AUTHORISATION_ID)
        self.logger.debug('response contains fields %s' % d)
        response_result = d.get(RESPONSE_CODE) == '00'
        response_code_msg = CB_BANK_RESPONSE_CODES.get(d.get(RESPONSE_CODE))
        response = PaymentResponse(
                result=response_result,
                signed=response_result,
                bank_data=d,
                order_id=d.get(ORDER_ID),
                transaction_id=d.get(AUTHORISATION_ID),
                bank_status=response_code_msg)
        return response
