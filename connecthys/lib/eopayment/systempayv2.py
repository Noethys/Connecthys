# -*- coding: utf-8 -*-

import datetime as dt
import hashlib
import logging
import string
import urlparse
import warnings
from gettext import gettext as _

from common import (PaymentCommon, PaymentResponse, PAID, ERROR, FORM, Form,
                    ResponseError, force_text, force_byte)
from cb import CB_RESPONSE_CODES

__all__ = ['Payment']

VADS_TRANS_DATE = 'vads_trans_date'
VADS_AUTH_NUMBER = 'vads_auth_number'
VADS_AUTH_RESULT = 'vads_auth_result'
VADS_RESULT = 'vads_result'
VADS_EXTRA_RESULT = 'vads_extra_result'
VADS_CUST_EMAIL = 'vads_cust_email'
VADS_CUST_NAME = 'vads_cust_name'
VADS_CUST_PHONE = 'vads_cust_phone'
VADS_CUST_INFO1 = 'vads_order_info'
VADS_CUST_INFO2 = 'vads_order_info2'
VADS_CUST_INFO3 = 'vads_order_info3'
VADS_CUST_FIRST_NAME = 'vads_cust_first_name'
VADS_CUST_LAST_NAME = 'vads_cust_last_name'
VADS_URL_RETURN = 'vads_url_return'
VADS_AMOUNT = 'vads_amount'
VADS_SITE_ID = 'vads_site_id'
VADS_TRANS_ID = 'vads_trans_id'
SIGNATURE = 'signature'
VADS_CTX_MODE = 'vads_ctx_mode'


def isonow():
    return dt.datetime.utcnow().isoformat('T').replace('-', '') \
        .replace('T', '').replace(':', '')[:14]


class Parameter:
    def __init__(self, name, ptype, code, max_length=None, length=None,
                 needed=False, default=None, choices=None, description=None,
                 help_text=None):
        self.name = name
        self.ptype = ptype
        self.code = code
        self.max_length = max_length
        self.length = length
        self.needed = needed
        self.default = default
        self.choices = choices
        self.description = description
        self.help_text = help_text

    def check_value(self, value):
        if self.length and len(value) != self.length:
            return False
        if self.max_length and len(value) > self.max_length:
            return False
        if self.choices and value not in self.choices:
            return False
        if value == '':
            return True
        value = value.replace('.', '')
        if self.ptype == 'n':
            return value.isdigit()
        elif self.ptype == 'an':
            return value.isalnum()
        elif self.ptype == 'an-':
            return value.replace('-', '').isalnum()
        elif self.ptype == 'an;':
            return value.replace(';', '').isalnum()
        return True


PARAMETERS = [
    # amount as euro cents
    Parameter('vads_action_mode', None, 47, needed=True, default='INTERACTIVE',
              choices=('SILENT', 'INTERACTIVE')),
    Parameter('vads_amount', 'n', 9, max_length=12, needed=True),
    Parameter('vads_capture_delay', 'n', 6, max_length=3, default=''),
    Parameter('vads_contrib', 'ans', 31, max_length=255, default='eopayment'),
    # defaut currency = EURO, norme ISO4217
    Parameter('vads_currency', 'n', 10, length=3, default='978', needed=True),
    Parameter('vads_cust_address', 'an', 19, max_length=255),
    # code ISO 3166
    Parameter('vads_cust_country', 'a', 22, length=2, default='FR'),
    Parameter('vads_cust_email', 'an@', 15, max_length=127),
    Parameter('vads_cust_id', 'an', 16, max_length=63),
    Parameter('vads_cust_name', 'ans', 18, max_length=127),
    Parameter('vads_cust_phone', 'an', 23, max_length=63),
    Parameter('vads_cust_title', 'an', 17, max_length=63),
    Parameter('vads_cust_city', 'an', 21, max_length=63),
    Parameter('vads_cust_zip', 'an', 20, max_length=63),
    Parameter('vads_ctx_mode', 'a', 11, needed=True, choices=('TEST',
                                                              'PRODUCTION'),
              default='TEST'),
    # ISO 639 code
    Parameter('vads_language', 'a', 12, length=2, default='fr'),
    Parameter('vads_order_id', 'an-', 13, max_length=32),
    Parameter('vads_order_info', 'an', 14, max_length=255,
              description=_(u"Complément d'information 1")),
    Parameter('vads_order_info2', 'an', 14, max_length=255,
              description=_(u"Complément d'information 2")),
    Parameter('vads_order_info3', 'an', 14, max_length=255,
              description=_(u"Complément d'information 3")),
    Parameter('vads_page_action', None, 46, needed=True, default='PAYMENT',
              choices=('PAYMENT',)),
    Parameter('vads_payment_cards', 'an;', 8, max_length=127, default='',
              description=_(u'Liste des cartes de paiement acceptées'),
              help_text=_(u'vide ou des valeurs sépareés par un point-virgule '
                          'parmi AMEX, AURORE-MULTI, BUYSTER, CB, COFINOGA, '
                          'E-CARTEBLEUE, MASTERCARD, JCB, MAESTRO, ONEY, '
                          'ONEY_SANDBOX, PAYPAL, PAYPAL_SB, PAYSAFECARD, '
                          'VISA')),
    # must be SINGLE or MULTI with parameters
    Parameter('vads_payment_config', '', 07, default='SINGLE',
              choices=('SINGLE', 'MULTI'), needed=True),
    Parameter('vads_return_mode', None, 48, default='GET',
              choices=('', 'NONE', 'POST', 'GET')),
    Parameter('signature', 'an', None, length=40),
    Parameter('vads_site_id', 'n', 02, length=8, needed=True,
              description=_(u'Identifiant de la boutique')),
    Parameter('vads_theme_config', 'ans', 32, max_length=255),
    Parameter(VADS_TRANS_DATE, 'n', 04, length=14, needed=True,
              default=isonow),
    Parameter('vads_trans_id', 'n', 03, length=6, needed=True),
    Parameter('vads_validation_mode', 'n', 5, max_length=1, choices=('', 0, 1),
              default=''),
    Parameter('vads_version', 'an', 01, default='V2', needed=True,
              choices=('V2',)),
    Parameter('vads_url_success', 'ans', 24, max_length=127),
    Parameter('vads_url_referral', 'ans', 26, max_length=127),
    Parameter('vads_url_refused', 'ans', 25, max_length=127),
    Parameter('vads_url_cancel', 'ans', 27, max_length=127),
    Parameter('vads_url_error', 'ans', 29, max_length=127),
    Parameter('vads_url_return', 'ans', 28, max_length=127),
    Parameter('vads_user_info', 'ans', 61, max_length=255),
    Parameter('vads_contracts', 'ans', 62, max_length=255),
    Parameter(VADS_CUST_FIRST_NAME, 'ans', 104, max_length=63),
    Parameter(VADS_CUST_LAST_NAME, 'ans', 104, max_length=63),
]
PARAMETER_MAP = dict(((parameter.name,
                       parameter) for parameter in PARAMETERS))

AUTH_RESULT_MAP = CB_RESPONSE_CODES

RESULT_MAP = {
    '00': 'paiement réalisé avec succés',
    '02': 'le commerçant doit contacter la banque du porteur',
    '05': 'paiement refusé',
    '17': 'annulation client',
    '30': 'erreur de format',
    '96': 'erreur technique lors du paiement'
}

EXTRA_RESULT_MAP = {
    '': "Pas de contrôle effectué",
    '00': "Tous les contrôles se sont déroulés avec succés",
    '02': "La carte a dépassé l'encours autorisé",
    '03': "La carte appartient à la liste grise du commerçant",
    '04': "Le pays d'émission de la carte appartient à la liste grise du "
    "commerçant ou le pays d'émission de la carte n'appartient pas à la "
    "liste blanche du commerçant",
    '05': "L'addresse IP appartient à la liste grise du commerçant",
    '99': "Problème technique recontré par le serveur lors du traitement "
    "d'un des contrôles locaux",
}


def add_vads(kwargs):
    new_vargs = {}
    for k, v in kwargs.iteritems():
        if k.startswith('vads_'):
            new_vargs[k] = v
        else:
            new_vargs['vads_' + k] = v
    return new_vargs


def check_vads(kwargs, exclude=[]):
    for parameter in PARAMETERS:
        name = parameter.name
        if name not in kwargs and name not in exclude and parameter.needed:
            raise ValueError('parameter %s must be defined' % name)
        if name in kwargs and not parameter.check_value(kwargs[name]):
            raise ValueError('parameter %s value %s is not of the type %s' % (
                name, kwargs[name],
                parameter.ptype))


class Payment(PaymentCommon):
    '''
        Produce request for and verify response from the SystemPay payment
        gateway.

            >>> gw =Payment(dict(secret_test='xxx', secret_production='yyyy',
                                 site_id=123, ctx_mode='PRODUCTION'))
            >>> print gw.request(100)
            ('20120525093304_188620',
            'https://paiement.systempay.fr/vads-payment/?vads_url_return=http%3A%2F%2Furl.de.retour%2Fretour.php&vads_cust_country=FR&vads_site_id=&vads_payment_config=SINGLE&vads_trans_id=188620&vads_action_mode=INTERACTIVE&vads_contrib=eopayment&vads_page_action=PAYMENT&vads_trans_date=20120525093304&vads_ctx_mode=TEST&vads_validation_mode=&vads_version=V2&vads_payment_cards=&signature=5d412498ab523627ec5730a09118f75afa602af5&vads_language=fr&vads_capture_delay=&vads_currency=978&vads_amount=100&vads_return_mode=NONE',
            {'vads_url_return': 'http://url.de.retour/retour.php',
            'vads_cust_country': 'FR', 'vads_site_id': '',
            'vads_payment_config': 'SINGLE', 'vads_trans_id': '188620',
            'vads_action_mode': 'INTERACTIVE', 'vads_contrib': 'eopayment',
            'vads_page_action': 'PAYMENT', 'vads_trans_date': '20120525093304',
            'vads_ctx_mode': 'TEST', 'vads_validation_mode': '',
            'vads_version': 'V2', 'vads_payment_cards': '', 'signature':
            '5d412498ab523627ec5730a09118f75afa602af5', 'vads_language': 'fr',
            'vads_capture_delay': '', 'vads_currency': '978', 'vads_amount': 100,
            'vads_return_mode': 'NONE'})

    '''
    service_url = "https://paiement.systempay.fr/vads-payment/"

    description = {
        'caption': 'SystemPay, système de paiment du groupe BPCE',
        'parameters': [
            {
                'name': 'normal_return_url',
                'caption': _('Normal return URL'),
                'default': '',
                'required': True,
            },
            {
                'name': 'automatic_return_url',
                'caption': _('Automatic return URL (ignored, must be set in Payzen/SystemPay backoffice)'),
                'required': False,
            },
            {'name': 'service_url',
                'default': service_url,
                'caption': _(u'URL du service de paiment'),
                'help_text': _(u'ne pas modifier si vous ne savez pas'),
                'validation': lambda x: x.startswith('http'),
                'required': True, },
            {'name': 'secret_test',
                'caption': _(u'Secret pour la configuration de TEST'),
                'validation': lambda value: str.isdigit(value),
                'required': True, },
            {'name': 'secret_production',
                'caption': _(u'Secret pour la configuration de PRODUCTION'),
                'validation': lambda value: str.isdigit(value), },
        ]
    }

    for name in ('vads_ctx_mode', VADS_SITE_ID, 'vads_order_info',
                 'vads_order_info2', 'vads_order_info3',
                 'vads_payment_cards', 'vads_payment_config'):
        parameter = PARAMETER_MAP[name]
        x = {'name': name,
             'caption': parameter.description or name,
             'validation': lambda value: parameter.check_value(value),
             'default': parameter.default,
             'required': parameter.needed,
             'help_text': parameter.help_text,
             'max_length': parameter.max_length}
        description['parameters'].append(x)

    def __init__(self, options, logger=None):
        super(Payment, self).__init__(options, logger=logger)
        options = add_vads(options)
        self.options = options

    def request(self, amount, name=None, first_name=None, last_name=None,
                address=None, email=None, phone=None, orderid=None, info1=None,
                info2=None, info3=None, next_url=None, **kwargs):
        '''
           Create the URL string to send a request to SystemPay
        '''
        self.logger.debug('%s amount %s name %s address %s email %s phone %s '
                          'next_url %s info1 %s info2 %s info3 %s kwargs: %s',
                          __name__, amount, name, address, email, phone, info1,
                          info2, info3, next_url, kwargs)
        # amount unit is cents
        amount = '%.0f' % (100 * amount)
        kwargs.update(add_vads({'amount': unicode(amount)}))
        if amount < 0:
            raise ValueError('amount must be an integer >= 0')
        normal_return_url = self.normal_return_url
        if next_url:
            warnings.warn("passing next_url to request() is deprecated, "
                          "set normal_return_url in options", DeprecationWarning)
            normal_return_url = next_url
        if normal_return_url:
            kwargs[VADS_URL_RETURN] = unicode(normal_return_url)
        if name is not None:
            kwargs['vads_cust_name'] = unicode(name)
        if first_name is not None:
            kwargs[VADS_CUST_FIRST_NAME] = unicode(first_name)
        if last_name is not None:
            kwargs[VADS_CUST_LAST_NAME] = unicode(last_name)

        if address is not None:
            kwargs['vads_cust_address'] = unicode(address)
        if email is not None:
            kwargs['vads_cust_email'] = unicode(email)
        if phone is not None:
            kwargs['vads_cust_phone'] = unicode(phone)
        if info1 is not None:
            kwargs['vads_order_info'] = unicode(info1)
        if info2 is not None:
            kwargs['vads_order_info2'] = unicode(info2)
        if info3 is not None:
            kwargs['vads_order_info3'] = unicode(info3)
        if orderid is not None:
            # check orderid format first
            name = 'vads_order_id'
            orderid = unicode(orderid)
            ptype = 'an-'
            p = Parameter(name, ptype, 13, max_length=32)
            if not p.check_value(orderid):
                raise ValueError('%s value %s is not of the type %s' % (name,
                                orderid, ptype))
            kwargs[name] = orderid

        transaction_id = self.transaction_id(6, string.digits, 'systempay',
                                             self.options[VADS_SITE_ID])
        kwargs[VADS_TRANS_ID] = unicode(transaction_id)
        fields = kwargs
        for parameter in PARAMETERS:
            name = parameter.name
            # import default parameters from configuration
            if name not in fields \
                    and name in self.options:
                fields[name] = unicode(self.options[name])
            # import default parameters from module
            if name not in fields and parameter.default is not None:
                if callable(parameter.default):
                    fields[name] = parameter.default()
                else:
                    fields[name] = parameter.default
        check_vads(fields)
        fields[SIGNATURE] = unicode(self.signature(fields))
        self.logger.debug('%s request contains fields: %s', __name__, fields)
        transaction_id = '%s_%s' % (fields[VADS_TRANS_DATE], transaction_id)
        self.logger.debug('%s transaction id: %s', __name__, transaction_id)
        form = Form(
            url=self.service_url,
            method='POST',
            fields=[
                {
                    'type': u'hidden',
                    'name': force_text(field_name),
                    'value': force_text(field_value),
                }
                for field_name, field_value in fields.iteritems()])
        return transaction_id, FORM, form

    def response(self, query_string, **kwargs):
        fields = urlparse.parse_qs(query_string, True)
        if not set(fields) >= set([SIGNATURE, VADS_CTX_MODE, VADS_AUTH_RESULT]):
            raise ResponseError()
        for key, value in fields.iteritems():
            fields[key] = value[0]
        copy = fields.copy()
        bank_status = []
        if VADS_AUTH_RESULT in fields:
            v = copy[VADS_AUTH_RESULT]
            ctx = (v, AUTH_RESULT_MAP.get(v, 'Code inconnu'))
            copy[VADS_AUTH_RESULT] = '%s: %s' % ctx
            bank_status.append(copy[VADS_AUTH_RESULT])
        if VADS_RESULT in copy:
            v = copy[VADS_RESULT]
            ctx = (v, RESULT_MAP.get(v, 'Code inconnu'))
            copy[VADS_RESULT] = '%s: %s' % ctx
            bank_status.append(copy[VADS_RESULT])
            if v == '30':
                if VADS_EXTRA_RESULT in fields:
                    v = fields[VADS_EXTRA_RESULT]
                    if v.isdigit():
                        for parameter in PARAMETERS:
                            if int(v) == parameter.code:
                                s = 'erreur dans le champ %s' % parameter.name
                                copy[VADS_EXTRA_RESULT] = s
                                bank_status.append(copy[VADS_EXTRA_RESULT])
            elif v in ('05', '00'):
                if VADS_EXTRA_RESULT in fields:
                    v = fields[VADS_EXTRA_RESULT]
                    extra_result_name = EXTRA_RESULT_MAP.get(v, 'Code inconnu')
                    copy[VADS_EXTRA_RESULT] = '%s: %s' % (v, extra_result_name)
                    bank_status.append(copy[VADS_EXTRA_RESULT])
        self.logger.debug('checking systempay response on:')
        for key in sorted(fields.keys()):
            self.logger.debug('  %s: %s' % (key, copy[key]))
        signature = self.signature(fields)
        signature_result = signature == fields[SIGNATURE]
        self.logger.debug('signature check: %s <!> %s', signature,
                          fields[SIGNATURE])
        if not signature_result:
            bank_status.append('invalid signature')

        if fields[VADS_AUTH_RESULT] == '00':
            result = PAID
        else:
            result = ERROR
        test = fields[VADS_CTX_MODE] == 'TEST'
        transaction_id = '%s_%s' % (copy[VADS_TRANS_DATE], copy[VADS_TRANS_ID])
        # the VADS_AUTH_NUMBER is the number to match payment in bank logs
        copy[self.BANK_ID] = copy.get(VADS_AUTH_NUMBER, '')
        response = PaymentResponse(
            result=result,
            signed=signature_result,
            bank_data=copy,
            order_id=transaction_id,
            transaction_id=copy.get(VADS_AUTH_NUMBER),
            bank_status=' - '.join(bank_status),
            test=test)
        return response

    def signature(self, fields):
        self.logger.debug('got fields %s to sign' % fields)
        ordered_keys = sorted(
            [key for key in fields.keys() if key.startswith('vads_')])
        self.logger.debug('ordered keys %s' % ordered_keys)
        ordered_fields = [force_byte(fields[key]) for key in ordered_keys]
        secret = getattr(self, 'secret_%s' % fields['vads_ctx_mode'].lower())
        signed_data = '+'.join(ordered_fields)
        signed_data = '%s+%s' % (signed_data, force_byte(secret))
        self.logger.debug(u'generating signature on «%s»', signed_data)
        sign = hashlib.sha1(signed_data).hexdigest()
        self.logger.debug(u'signature «%s»', sign)
        return sign
