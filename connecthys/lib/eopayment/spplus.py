# -*- coding: utf-8 -*-
from decimal import Decimal
import binascii
from gettext import gettext as _
import hmac
import hashlib
import urlparse
import urllib
import string
import datetime as dt
import logging
import re
import warnings

import Crypto.Cipher.DES
from common import (PaymentCommon, URL, PaymentResponse, RECEIVED, ACCEPTED,
        PAID, ERROR, ResponseError)

def N_(message): return message

__all__ = ['Payment']

KEY_DES_KEY = '\x45\x1f\xba\x4f\x4c\x3f\xd4\x97'
IV = '\x30\x78\x30\x62\x2c\x30\x78\x30'
REFERENCE = 'reference'
ETAT = 'etat'
SPCHECKOK = 'spcheckok'
LOGGER = logging.getLogger(__name__)
REFSFP = 'refsfp'

# Pour un paiement comptant la chaine des états est: 1 -> 4 -> 10, seul l'état
# 10 garanti le paiement
SPPLUS_RESPONSE_CODES = {
    '1': 'Autorisation de paiement acceptée',
    '2': 'Autorisation de paiement refusée',
    '4': 'Echéance du paiement acceptée et en attente de remise',
    '5': 'Echéance du paiement refusée',
    '6': 'Paiement par chèque accepté',
    '8': 'Chèque encaissé',
    '10': 'Paiement terminé',
    '11': 'Echéance du paiement annulée par le commerçant',
    '12': 'Abandon de l\’internaute',
    '15': 'Remboursement enregistré',
    '16': 'Remboursement annulé',
    '17': 'Remboursement accepté',
    '20': 'Echéance du paiement avec un impayé',
    '21': 'Echéance du paiement avec un impayé et en attente de validation des services SP PLUS',
    '30': 'Echéance du paiement remisée',
    '99': 'Paiement de test en production',
}

VALID_STATE = ('1', '4', '10')
ACCEPTED_STATE = ('1', '4')
PAID_STATE = ('10',)
TEST_STATE = ('99',)


def decrypt_ntkey(ntkey):
    key = binascii.unhexlify(ntkey.replace(' ',''))
    return decrypt_key(key)

def decrypt_key(key):
    CIPHER = Crypto.Cipher.DES.new(KEY_DES_KEY, Crypto.Cipher.DES.MODE_CBC, IV)
    return CIPHER.decrypt(key)

def extract_values(query_string):
    kvs = query_string.split('&')
    result = []
    for kv in kvs:
        k, v = kv.split('=', 1)
        if k != 'hmac':
            result.append(v)
    return ''.join(result)

def sign_ntkey_query(ntkey, query):
    key = decrypt_ntkey(ntkey)
    data_to_sign = extract_values(query)
    return hmac.new(key[:20], data_to_sign, hashlib.sha1).hexdigest().upper()

PAIEMENT_FIELDS = [ 'siret', REFERENCE, 'langue', 'devise', 'montant',
    'taxe', 'validite' ]

def sign_url_paiement(ntkey, query):
    if '?' in query:
        query = query[query.index('?')+1:]
    key = decrypt_ntkey(ntkey)
    data = urlparse.parse_qs(query, True)
    fields = [data.get(field,[''])[0] for field in PAIEMENT_FIELDS]
    data_to_sign = ''.join(fields)
    return hmac.new(key[:20], data_to_sign, hashlib.sha1).hexdigest().upper()

ALPHANUM = string.letters + string.digits
SERVICE_URL = "https://www.spplus.net/paiement/init.do"

class Payment(PaymentCommon):
    description = {
            'caption': "SPPlus payment service of French bank Caisse d'epargne",
            'parameters': [
                {
                    'name': 'normal_return_url',
                    'caption': N_('Normal return URL'),
                    'default': '',
                    'required': True,
                },
                {
                    'name': 'automatic_return_url',
                    'caption': N_('Automatic return URL'),
                    'required': False,
                },
                {   'name': 'cle',
                    'caption': 'Secret key, a 40 digits hexadecimal number',
                    'regexp': re.compile('^ *((?:[a-fA-F0-9] *){40}) *$')
                },
                {   'name': 'siret',
                    'caption': 'Siret of the entreprise augmented with the '
                        'site number, example: 00000000000001-01',
                    'regexp': re.compile('^ *(\d{14}-\d{2}) *$')
                },
                {   'name': 'langue',
                    'caption': 'Language of the customers',
                    'default': 'FR',
                },
                {   'name': 'taxe',
                    'caption': 'Taxes',
                    'default': '0.00'
                },
                {   'name': 'modalite',
                    'caption': '1x, 2x, 3x, xx, nx (if multiple separated by "/")',
                    'default': '1x',
                },
                {   'name': 'moyen',
                    'caption': 'AUR, AMX, CBS, CGA, '
                        'CHK, DIN, PRE (if multiple separate by "/")',
                    'default': 'CBS',
                },
            ]
    }
    devise = '978'

    def request(self, amount, name=None, address=None, email=None, phone=None,
            orderid=None, info1=None, info2=None, info3=None, next_url=None,
            logger=LOGGER, **kwargs):
        logger.debug('requesting spplus payment with montant %s email=%s' % (amount, email))
        reference = self.transaction_id(20, ALPHANUM, 'spplus', self.siret)
        validite = dt.date.today()+dt.timedelta(days=1)
        validite = validite.strftime('%d/%m/%Y')
        fields = { 'siret': self.siret,
                'devise': self.devise,
                'langue': self.langue,
                'taxe': self.taxe,
                'montant': str(Decimal(amount)),
                REFERENCE: orderid or reference,
                'validite': validite,
                'version': '1',
                'modalite': self.modalite,
                'moyen': self.moyen }
        if email:
            fields['email'] = email
        normal_return_url = self.normal_return_url
        if next_url and not normal_return_url:
            warnings.warn("passing next_url to request() is deprecated, "
                          "set normal_return_url in options", DeprecationWarning)
            normal_return_url = next_url
        if normal_return_url:
            if (not normal_return_url.startswith('http://') \
                    and not normal_return_url.startswith('https://')) \
                       or '?' in normal_return_url:
                   raise ValueError('normal_return_url must be an absolute URL without parameters')
            fields['urlretour'] = normal_return_url
        logger.debug('sending fields %s' % fields)
        query = urllib.urlencode(fields)
        url = '%s?%s&hmac=%s' % (SERVICE_URL, query, sign_url_paiement(self.cle,
            query))
        logger.debug('full url %s' % url)
        return reference, URL, url

    def response(self, query_string, logger=LOGGER, **kwargs):
        form = urlparse.parse_qs(query_string)
        if not set(form) >= set([REFERENCE, ETAT, REFSFP]):
            raise ResponseError()
        for key, value in form.iteritems():
            form[key] = value[0]
        logger.debug('received query_string %s' % query_string)
        logger.debug('parsed as %s' % form)
        reference = form.get(REFERENCE)
        bank_status = []
        signed = False
        form[self.BANK_ID] = form.get(REFSFP)
        etat = form.get('etat')
        status = '%s: %s' % (etat, SPPLUS_RESPONSE_CODES.get(etat, 'Unknown code'))
        logger.debug('status is %s', status)
        bank_status.append(status)
        if 'hmac' in form:
            try:
                signed_data, signature = query_string.rsplit('&', 1)
                _, hmac = signature.split('=', 1)
                logger.debug('got signature %s' % hmac)
                computed_hmac = sign_ntkey_query(self.cle, signed_data)
                logger.debug('computed signature %s' % computed_hmac)
                signed = hmac == computed_hmac
                if not signed:
                    bank_status.append('invalid signature')
            except ValueError:
                bank_status.append('invalid signature')

        test = False
        if etat in PAID_STATE:
            result = PAID
        elif etat in ACCEPTED_STATE:
            result = ACCEPTED
        elif etat in VALID_STATE:
            result = RECEIVED
        elif etat in TEST_STATE:
            result = RECEIVED # what else ?
            test = True
        else:
            result = ERROR

        response = PaymentResponse(
                result=result,
                signed=signed,
                bank_data=form,
                order_id=reference,
                transaction_id=form[self.BANK_ID],
                bank_status=' - '.join(bank_status),
                return_content=SPCHECKOK,
                test=test)
        return response


if __name__ == '__main__':
    import sys

    ntkey = '58 6d fc 9c 34 91 9b 86 3f fd 64 63 c9 13 4a 26 ba 29 74 1e c7 e9 80 79'
    if len(sys.argv) == 2:
        print sign_url_paiement(ntkey, sys.argv[1])
        print sign_ntkey_query(ntkey, sys.argv[1])
    elif len(sys.argv) > 2:
        print sign_url_paiement(sys.argv[1], sys.argv[2])
        print sign_ntkey_query(sys.argv[1], sys.argv[2])
