# -*- coding: utf-8 -*-

from decimal import Decimal, ROUND_DOWN
from common import (PaymentCommon, PaymentResponse, URL, PAID, DENIED,
        CANCELLED, ERROR, ResponseError)
from urllib import urlencode
from urlparse import parse_qs
from gettext import gettext as _
import logging
import warnings

from systempayv2 import isonow

__all__ = ['Payment']

TIPI_URL = 'http://www.jepaiemesserviceslocaux.dgfip.finances.gouv.fr' \
        '/tpa/paiement.web'
LOGGER = logging.getLogger(__name__)

class Payment(PaymentCommon):
    '''Produce requests for and verify response from the TIPI online payment
    processor from the French Finance Ministry.

    '''

    description = {
            'caption': 'TIPI, Titres Payables par Internet',
            'parameters': [
                {
                    'name': 'numcli',
                    'caption': _(u'Numéro client'),
                    'help_text': _(u'un numéro à 6 chiffres communiqué par l’administrateur TIPI'),
                    'validation': lambda s: str.isdigit(s) and (0 < int(s) < 1000000),
                    'required': True,
                },
                {
                    'name': 'service_url',
                    'default': TIPI_URL,
                    'caption': _(u'URL du service TIPI'),
                    'help_text': _(u'ne pas modifier si vous ne savez pas'),
                    'validation': lambda x: x.startswith('http'),
                    'required': True,
                },
                {
                    'name': 'normal_return_url',
                    'caption': _('Normal return URL (unused by TIPI)'),
                    'required': False,
                },
                {
                    'name': 'automatic_return_url',
                    'caption': _('Automatic return URL'),
                    'required': True,
                },
                {
                    'name': 'saisie',
                    'caption': _('Payment type'),
                    'required': True,
                    'default': 'T',
                },
            ],
    }

    def request(self, amount, next_url=None, exer=None, orderid=None,
            refdet=None, objet=None, email=None, saisie=None, **kwargs):
        try:
            montant = Decimal(amount)
            if Decimal('0') > montant > Decimal('9999.99'):
                raise ValueError('MONTANT > 9999.99 euros')
            montant = montant*Decimal('100')
            montant = montant.to_integral_value(ROUND_DOWN)
        except ValueError:
            raise ValueError('MONTANT invalid format, must be '
                    'a decimal integer with less than 4 digits '
                    'before and 2 digits after the decimal point '
                    ', here it is %s' % repr(amount))

        automatic_return_url = self.automatic_return_url
        if next_url and not automatic_return_url:
            warnings.warn("passing next_url to request() is deprecated, "
                          "set automatic_return_url in options", DeprecationWarning)
            automatic_return_url = next_url
        if automatic_return_url is not None:
            if not isinstance(automatic_return_url, str) or \
                not automatic_return_url.startswith('http'):
                raise ValueError('URLCL invalid URL format')
        try:
            if exer is not None:
                exer = int(exer)
                if exer > 9999:
                    raise ValueError()
        except ValueError:
            raise ValueError('EXER format invalide')
        try:
            refdet = orderid or refdet
            refdet = str(refdet)
            if 6 > len(refdet) > 30:
                raise ValueError('len(REFDET) < 6 or > 30')
        except Exception, e:
            raise ValueError('REFDET format invalide, %r' % refdet, e)
        if objet is not None:
            try:
                objet = str(objet)
            except Exception, e:
                raise ValueError('OBJET must be a string', e)
            if not objet.replace(' ','').isalnum():
                raise ValueError('OBJECT must only contains '
                        'alphanumeric characters, %r' % objet)
            if len(objet) > 99:
                raise ValueError('OBJET length must be less than 100')
        try:
            mel = str(email)
            if '@' not in mel:
                raise ValueError('no @ in MEL')
            if not (6 <= len(mel) <= 80):
                raise ValueError('len(MEL) is invalid, must be between 6 and 80')
        except Exception, e:
            raise ValueError('MEL is not a valid email, %r' % mel, e)

        saisie = saisie or self.saisie

        if saisie not in ('M', 'T', 'X', 'A'):
            raise ValueError('SAISIE invalid format, %r, must be M, T, X or A' % saisie)

        iso_now = isonow()
        transaction_id = '%s_%s' % (iso_now, refdet)
        if objet:
            #objet = objet[:100-len(iso_now)-2] + ' ' + iso_now
             objet = objet[:100-len(transaction_id)-2] + ' ' + transaction_id
        else:
            objet = transaction_id
        params = {
                'numcli': self.numcli,
                'refdet': refdet,
                'montant': montant,
                'mel': mel,
                'saisie': saisie,
                'objet': objet,
        }
        if exer:
            params['exer'] = exer
        if automatic_return_url:
            params['urlcl'] = automatic_return_url
        url = '%s?%s' % (self.service_url, urlencode(params))
        return transaction_id, URL, url

    def response(self, query_string, **kwargs):
        fields = parse_qs(query_string, True)
        if not set(fields) >= set(['refdet', 'resultrans']):
            raise ResponseError()
        for key, value in fields.iteritems():
            fields[key] = value[0]
        refdet = fields.get('refdet')
        if refdet is None:
            raise ValueError('refdet is missing')
        if 'objet' in fields:
            iso_now = fields['objet']
        else:
            iso_now = isonow()
        transaction_id = '%s_%s' % (iso_now, refdet)

        result = fields.get('resultrans')
        if result == 'P':
            result = PAID
            bank_status = ''
        elif result == 'R':
            result = DENIED
            bank_status = 'refused'
        elif result == 'A':
            result = CANCELLED
            bank_status = 'canceled'
        else:
            bank_status = 'wrong return: %r' % result
            result = ERROR

        test = fields.get('saisie') == 'T'

        return PaymentResponse(
                result=result,
                bank_status=bank_status,
                signed=True,
                bank_data=fields,
                transaction_id=transaction_id,
                test=test)

if __name__ == '__main__':
    p = Payment({'numcli': '12345'})
    print p.request(amount=Decimal('123.12'),
            exer=9999,
            refdet=999900000000999999,
            objet='test bog',
            email='test@test.test',
            urlcl='http://127.0.0.1/tipi_urlcl',
            saisie='T')
    print p.response('objet=test bog&montant=12312&saisie=T&mel=test%40test.test&numcli=12345&exer=9999&refdet=999900000000999999&resultrans=P')
