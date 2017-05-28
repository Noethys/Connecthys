# -*- coding: utf-8

from collections import OrderedDict
import datetime
import logging
import hashlib
import hmac
from decimal import Decimal, ROUND_DOWN
from Crypto.Signature import PKCS1_v1_5
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA
import urlparse
import urllib
import base64
from gettext import gettext as _
import string
import warnings

from common import (PaymentCommon, PaymentResponse, FORM, PAID, ERROR, Form,
        ORDERID_TRANSACTION_SEPARATOR, ResponseError)

__all__ = ['sign', 'Payment']

PAYBOX_KEY = '''-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDe+hkicNP7ROHUssGNtHwiT2Ew
HFrSk/qwrcq8v5metRtTTFPE/nmzSkRnTs3GMpi57rBdxBBJW5W9cpNyGUh0jNXc
VrOSClpD5Ri2hER/GcNrxVRP7RlWOqB1C03q4QYmwjHZ+zlM4OUhCCAtSWflB4wC
Ka1g88CjFwRw/PB9kwIDAQAB
-----END PUBLIC KEY-----'''

VARS = {
    'PBX_SITE': 'Numéro de site (fourni par Paybox)',
    'PBX_RANG': 'Numéro de rang (fourni par Paybox)',
    'PBX_IDENTIFIANT': 'Identifiant interne (fourni par Paybox)',
    'PBX_TOTAL': 'Montant total de la transaction',
    'PBX_DEVISE': 'Devise de la transaction',
    'PBX_CMD':  'Référence commande côté commerçant',
    'PBX_PORTEUR': 'Adresse E - mail de l’acheteur',
    'PBX_RETOUR': 'Liste des variables à retourner par Paybox',
    'PBX_HASH': 'Type d’algorit hme de hachage pour le calcul de l’empreinte',
    'PBX_TIME': 'Horodatage de la transaction',
    'PBX_HMAC': 'Signature calculée avec la clé secrète',
}

PAYBOX_ERROR_CODES = {
    '00000': 'Opération réussie.',
    '00001': 'La connexion au centre d’autorisation a échoué ou une '
    'erreur interne est survenue. Dans ce cas, il est souhaitable de faire '
    'une tentative sur le site secondaire : tpeweb1.paybox.com.',
    '001xx':  'Paiement refusé par le centre d’autorisation [voir '
    '§12.112.1 Codes réponses du centre d’autorisationCodes réponses du '
    'centre d’autorisation]. En cas d’autorisation de la transaction par '
    'le centre d’autorisation de la banque ou de l’établissement financier '
    'privatif, le code erreur “00100” sera en fait remplacé directement '
    'par “00000”.',
    '00003': 'Erreur Paybox. Dans ce cas, il est souhaitable de faire une '
    'tentative sur le site secondaire FQDN tpeweb1.paybox.com.',
    '00004': 'Numéro de porteur ou cryptogramme visuel invalide.',
    '00006': 'Accès refusé ou site/rang/identifiant incorrect.',
    '00008': 'Date de fin de validité incorrecte.',
    '00009': 'Erreur de création d’un abonnement.',
    '00010': 'Devise inconnue.',
    '00011': 'Montant incorrect.',
    '00015': 'Paiement déjà effectué.',
    '00016': 'Abonné déjà existant (inscription nouvel abonné). Valeur '
    '‘U’ de la variable PBX_RETOUR.',
    '00021': 'Carte non autorisée.',
    '00029': 'Carte non conforme. Code erreur renvoyé lors de la '
    'documentation de la variable « PBX_EMPREINTE ».',
    '00030': 'Temps d’attente > 15 mn par l’internaute/acheteur au niveau '
    'de la page de paiements.',
    '00031': 'Réservé',
    '00032': 'Réservé',
    '00033': 'Code pays de l’adresse IP du navigateur de l’acheteur non '
    'autorisé.',
    '00040': 'Opération sans authentification 3-DSecure, bloquée par le '
    'filtre.',
    '99999': 'Opération en attente de validation par l’émetteur du moyen '
    'de paiement.',
}

ALGOS = {
    'SHA512': hashlib.sha512,
    'SHA256': hashlib.sha256,
    'SHA384': hashlib.sha384,
    'SHA224': hashlib.sha224,
}

URLS = {
    'test':
        'https://preprod-tpeweb.paybox.com/cgi/MYchoix_pagepaiement.cgi',
    'prod':
        'https://tpeweb.paybox.com/cgi/MYchoix_pagepaiement.cgi',
    'backup':
        'https://tpeweb1.paybox.com/cgi/MYchoix_pagepaiement.cgi',
}


def sign(data, key):
    '''Take a list of tuple key, value and sign it by building a string to
       sign.
    '''
    logger = logging.getLogger(__name__)
    algo = None
    logger.debug('signature key %r', key)
    logger.debug('signed data %r', data)
    for k, v in data:
        if k == 'PBX_HASH' and v in ALGOS:
            algo = ALGOS[v]
            break
    assert algo, 'Missing or invalid PBX_HASH'
    tosign = ['%s=%s' % (k, unicode(v).encode('utf-8')) for k, v in data]
    tosign = '&'.join(tosign)
    logger.debug('signed string %r', tosign)
    signature = hmac.new(key, tosign, algo)
    return tuple(data) + (('PBX_HMAC', signature.hexdigest().upper()),)


def verify(data, signature, key=PAYBOX_KEY):
    '''Verify signature using SHA1withRSA by Paybox'''
    key = RSA.importKey(key)
    h = SHA.new(data)
    verifier = PKCS1_v1_5.new(key)
    return verifier.verify(h, signature)


class Payment(PaymentCommon):
    '''Paybox backend for eopayment.

       If you want to handle Instant Payment Notification, you must pass
       provide a automatic_return_url option specifying the URL of the
       callback endpoint.

       Email is mandatory to emit payment requests with paybox.

       IP adresses to authorize:
                                 IN           OUT
           test           195.101.99.73 195.101.99.76
           production     194.2.160.66  194.2.122.158
           backup         195.25.7.146  195.25.7.166
    '''
    callback = None

    description = {
        'caption': _('Paybox'),
        'parameters': [
            {
                'name': 'normal_return_url',
                'caption': _('Normal return URL'),
                'default': '',
                'required': False,
            },
            {
                'name': 'automatic_return_url',
                'caption': _('Automatic return URL'),
                'required': False,
            },
            {
                'name': 'platform',
                'caption': _('Plateforme cible'),
                'default': 'test',
                'validation': lambda x: isinstance(x, basestring) and
                x.lower() in ('test', 'prod'),
            },
            {
                'name': 'site',
                'caption': _('Numéro de site'),
                'required': True,
                'validation': lambda x: isinstance(x, basestring) and
                x.isdigit() and len(x) == 7,
            },
            {
                'name': 'rang',
                'caption': _('Numéro de rang'),
                'required': True,
                'validation': lambda x: isinstance(x, basestring) and
                x.isdigit() and len(x) == 2,
            },
            {
                'name': 'identifiant',
                'caption': _('Identifiant'),
                'required': True,
                'validation': lambda x: isinstance(x, basestring) and
                x.isdigit() and (0 < len(x) < 10),
            },
            {
                'name': 'shared_secret',
                'caption': _('Secret partagé'),
                'validation': lambda x: isinstance(x, str) and
                all(a.lower() in '0123456789ABCDEF' for a in x),
                'required': True,
            },
            {
                'name': 'devise',
                'caption': _('Devise'),
                'default': '978',
                'choices': (
                    ('978', 'Euro'),
                ),
            },
            {
                'name': 'callback',
                'caption': _('Callback URL'),
                'deprecated': True,
            },
        ]
    }

    def request(self, amount, email, name=None, orderid=None, **kwargs):
        d = OrderedDict()
        d['PBX_SITE'] = unicode(self.site)
        d['PBX_RANG'] = unicode(self.rang).strip()[-2:]
        d['PBX_IDENTIFIANT'] = unicode(self.identifiant)
        d['PBX_TOTAL'] = (amount * Decimal(100)).to_integral_value(ROUND_DOWN)
        d['PBX_DEVISE'] = unicode(self.devise)
        transaction_id = kwargs.get('transaction_id') or \
            self.transaction_id(12, string.digits, 'paybox', self.site,
                                self.rang, self.identifiant)
        d['PBX_CMD'] = unicode(transaction_id)
        # prepend order id command reference
        if orderid:
            d['PBX_CMD'] = orderid + ORDERID_TRANSACTION_SEPARATOR + d['PBX_CMD']
        d['PBX_PORTEUR'] = unicode(email)
        d['PBX_RETOUR'] = 'montant:M;reference:R;code_autorisation:A;erreur:E;signature:K'
        d['PBX_HASH'] = 'SHA512'
        d['PBX_TIME'] = kwargs.get('time') or (unicode(datetime.datetime.utcnow().isoformat('T')).split('.')[0]+'+00:00')
        d['PBX_ARCHIVAGE'] = transaction_id
        if self.normal_return_url:
            d['PBX_EFFECTUE'] = self.normal_return_url
            d['PBX_REFUSE'] = self.normal_return_url
            d['PBX_ANNULE'] = self.normal_return_url
            d['PBX_ATTENTE'] = self.normal_return_url
        automatic_return_url = self.automatic_return_url
        if not automatic_return_url and self.callback:
            warnings.warn("callback option is deprecated, "
                          "use automatic_return_url", DeprecationWarning)
            automatic_return_url = self.callback
        if automatic_return_url:
            d['PBX_REPONDRE_A'] = unicode(automatic_return_url)
        d = d.items()
        d = sign(d, self.shared_secret.decode('hex'))
        url = URLS[self.platform]
        fields = []
        for k, v in d:
            fields.append({
                'type': u'hidden',
                'name': unicode(k),
                'value': unicode(v),
            })
        form = Form(url, 'POST', fields, submit_name=None,
                    submit_value=u'Envoyer', encoding='utf-8')
        return transaction_id, FORM, form

    def response(self, query_string, callback=False, **kwargs):
        d = urlparse.parse_qs(query_string, True, False)
        if not set(d) >= set(['erreur', 'reference']):
            raise ResponseError()
        signed = False
        if 'signature' in d:
            sig = d['signature'][0]
            sig = base64.b64decode(sig)
            data = []
            if callback:
                for key in ('montant', 'reference', 'code_autorisation',
                            'erreur'):
                    data.append('%s=%s' % (key, urllib.quote(d[key][0])))
            else:
                for key, value in urlparse.parse_qsl(query_string, True, True):
                    if key == 'signature':
                        break
                    data.append('%s=%s' % (key, urllib.quote(value)))
            data = '&'.join(data)
            signed = verify(data, sig)
        if d['erreur'][0] == '00000':
            result = PAID
        else:
            result = ERROR
        for l in (5, 3):
            prefix = d['erreur'][0][:l]
            suffix = 'x' * (5-l)
            bank_status = PAYBOX_ERROR_CODES.get(prefix + suffix)
            if bank_status is not None:
                break
        orderid = d['reference'][0]
        # decode order id from returned reference
        if ORDERID_TRANSACTION_SEPARATOR in orderid:
            orderid, transaction_id = orderid.split(ORDERID_TRANSACTION_SEPARATOR, 1)
        return PaymentResponse(
            order_id=orderid,
            signed=signed,
            bank_data=d,
            result=result,
            bank_status=bank_status)
