# -*- coding: utf-8 -*-

import logging

from common import (URL, HTML, FORM, RECEIVED, ACCEPTED, PAID, DENIED,
                    CANCELED, CANCELLED, ERROR, ResponseError, force_text)

__all__ = ['Payment', 'URL', 'HTML', 'FORM', 'SIPS',
'SYSTEMPAY', 'SPPLUS', 'TIPI', 'TIPIREGIE', 'DUMMY', 'get_backend', 'RECEIVED', 'ACCEPTED',
'PAID', 'DENIED', 'CANCELED', 'CANCELLED', 'ERROR', 'get_backends']

SIPS = 'sips'
SIPS2 = 'sips2'
SYSTEMPAY = 'systempayv2'
SPPLUS = 'spplus'
TIPI = 'tipi'
TIPIREGIE = 'tipi_regie'
DUMMY = 'dummy'
OGONE = 'ogone'
PAYBOX = 'paybox'
PAYZEN = 'payzen'

logger = logging.getLogger(__name__)

def get_backend(kind):
    '''Resolve a backend name into a module object'''
    module = __import__(kind, globals(), locals(), [])
    return module.Payment

__BACKENDS = [ DUMMY, SIPS, SIPS2, SYSTEMPAY, SPPLUS, OGONE, PAYBOX, PAYZEN, TIPI, TIPIREGIE ]

def get_backends():
    '''Return a dictionnary mapping existing eopayment backends name to their
       description.

          >>> get_backends()['dummy'].description['caption']
          'Dummy payment backend'

    '''
    return dict((backend, get_backend(backend)) for backend in __BACKENDS)

class Payment(object):
    '''
       Interface to credit card online payment servers of French banks. The
       only use case supported for now is a unique automatic payment.

           >>> spplus_options = { \
                   'cle': '58 6d fc 9c 34 91 9b 86 3f fd 64 ' \
                          '63 c9 13 4a 26 ba 29 74 1e c7 e9 80 79', \
                   'siret': '00000000000001-01', \
               }
           >>> p = Payment(kind=SPPLUS, options=spplus_options)
           >>> transaction_id, kind, data = p.request('10.00', email='bob@example.com')
           >>> print (transaction_id, kind, data) # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
           ('...', 1, 'https://www.spplus.net/paiement/init.do?...')

       Supported backend of French banks are:

        - sips, for BNP, Banque Populaire (before 2010), CCF, HSBC, Crédit
          Agricole, La Banque Postale, LCL, Société Générale and Crédit du
          Nord.
        - spplus for Caisse d'épargne
        - systempay for Banque Populaire (after 2010)

       For SIPs you also need the bank provided middleware especially the two
       executables, request and response, as the protocol from ATOS/SIPS is not
       documented. For the other backends the modules are autonomous.

       Each backend need some configuration parameters to be used, the
       description of the backend list those parameters. The description
       dictionary can be used to generate configuration forms.

           >>> d = get_backend(SPPLUS).description
           >>> print d['caption']
           SPPlus payment service of French bank Caisse d'epargne
           >>> print [p['name'] for p in d['parameters']] # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
           ['cle', ..., 'moyen']
           >>> print d['parameters'][0]['caption']
           Secret key, a 40 digits hexadecimal number

    '''

    def __init__(self, kind, options, logger=None):
        self.kind = kind
        self.backend = get_backend(kind)(options, logger=logger)

    def request(self, amount, **kwargs):
        '''Request a payment to the payment backend.

          Arguments:
          amount -- the amount of money to ask
          email -- the email of the customer (optional)
          usually redundant with the hardwired settings in the bank
          configuration panel. At this url you must use the Payment.response
          method to analyze the bank returned values.

          It returns a triple of values, (transaction_id, kind, data):
            - the first gives a string value to later match the payment with
              the invoice,
            - kind gives the type of the third value, payment.URL or
              payment.HTML or payment.FORM,
            - the third is the URL or the HTML form to contact the payment
              server, which must be sent to the customer browser.
        '''
        logger.debug(u'%r' %  kwargs)
        for param in kwargs:
            # encode all input params to unicode
            kwargs[param] = force_text(kwargs[param])
        return self.backend.request(amount, **kwargs)

    def response(self, query_string, **kwargs):
        '''
          Process a response from the Bank API. It must be used on the URL
          where the user browser of the payment server is going to post the
          result of the payment. Beware it can happen multiple times for the
          same payment, so you MUST support multiple notification of the same
          event, i.e. it should be idempotent. For example if you already
          validated some invoice, receiving a new payment notification for the
          same invoice should alter this state change.

          Beware that when notified directly by the bank (and not through the
          customer browser) no applicative session will exist, so you should
          not depend on it in your handler.

          Arguments:
          query_string -- the URL encoded form-data from a GET or a POST

          It returns a quadruplet of values:

             (result, transaction_id, bank_data, return_content)

           - result is a boolean stating whether the transaction worked, use it
             to decide whether to act on a valid payment,
           - the transaction_id return the same id than returned by request
             when requesting for the payment, use it to find the invoice or
             transaction which is linked to the payment,
           - bank_data is a dictionnary of the data sent by the bank, it should
             be logged for security reasons,
           - return_content, if not None you must return this content as the
             result of the HTTP request, it's used when the bank is calling
             your site as a web service.

        '''
        return self.backend.response(query_string, **kwargs)

    def cancel(self, amount, bank_data, **kwargs):
        '''
           Cancel or edit the amount of a transaction sent to the bank.

           Arguments:
           - amount -- the amount of money to cancel
           - bank_data -- the transaction dictionary received from the bank
        '''
        return self.backend.cancel(amount, bank_data, **kwargs)

    def validate(self, amount, bank_data, **kwargs):
        '''
           Validate and trigger the transmission of a transaction to the bank.

           Arguments:
           - amount -- the amount of money
           - bank_data -- the transaction dictionary received from the bank
        '''
        return self.backend.validate(amount, bank_data, **kwargs)
