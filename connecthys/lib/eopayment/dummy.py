import urllib
import string
import logging
import warnings

def N_(message): return message

try:
    from cgi import parse_qs
except ImportError:
    from urlparse import parse_qs

from common import PaymentCommon, URL, PaymentResponse, PAID, ERROR, ResponseError

__all__ = [ 'Payment' ]

SERVICE_URL = 'http://dummy-payment.demo.entrouvert.com/'
ALPHANUM = string.letters + string.digits
LOGGER = logging.getLogger(__name__)

class Payment(PaymentCommon):
    '''
       Dummy implementation of the payment interface.

       It is used with a dummy implementation of a bank payment service that
       you can find on:

           http://dummy-payment.demo.entrouvert.com/

       You must pass the following keys inside the options dictionnary:
        - dummy_service_url, the URL of the dummy payment service, it defaults
          to the one operated by Entr'ouvert.
        - automatic_return_url: where to POST to notify the service of a
          payment
        - origin: a human string to display to the user about the origin of
          the request.
        - siret: an identifier for the eCommerce site, fake.
        - normal_return_url: the return URL for the user (can be overriden on a
          per request basis).
    '''
    description = {
            'caption': 'Dummy payment backend',
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
                {   'name': 'dummy_service_url',
                    'caption': 'URL of the dummy payment service',
                    'default': SERVICE_URL,
                    'type': str,
                },
                {   'name': 'origin',
                    'caption': 'name of the requesting service, '
                               'to present in the user interface',
                    'type': str,

                },
                {   'name': 'siret',
                    'caption': 'dummy siret parameter',
                    'type': str,
                },
                {   'name': 'consider_all_response_signed',
                    'caption': 'All response will be considered as signed '
                         '(to test payment locally for example, as you '
                         'cannot received the signed callback)',
                    'type': bool,
                    'default': False,
                },
                {   'name': 'direct_notification_url',
                    'caption': 'direct notification url (replaced by automatic_return_url)',
                    'type': str,
                    'deprecated': True,
                },
                {   'name': 'next_url (replaced by normal_return_url)',
                    'caption': 'Return URL for the user',
                    'type': str,
                    'deprecated': True,
                },
            ],
    }

    def request(self, amount, name=None, address=None, email=None, phone=None,
            orderid=None, info1=None, info2=None, info3=None, next_url=None, **kwargs):
        self.logger.debug('%s amount %s name %s address %s email %s phone %s'
                ' next_url %s info1 %s info2 %s info3 %s kwargs: %s',
                __name__, amount, name, address, email, phone, info1, info2, info3, next_url, kwargs)
        transaction_id = self.transaction_id(30, ALPHANUM, 'dummy', self.siret)
        normal_return_url = self.normal_return_url
        if next_url and not normal_return_url:
            warnings.warn("passing next_url to request() is deprecated, "
                          "set normal_return_url in options", DeprecationWarning)
            normal_return_url = next_url
        automatic_return_url = self.automatic_return_url
        if self.direct_notification_url and not automatic_return_url:
            warnings.warn("direct_notification_url option is deprecated, "
                          "use automatic_return_url", DeprecationWarning)
            automatic_return_url = self.direct_notification_url
        query = {
                'transaction_id': transaction_id,
                'siret': self.siret,
                'amount': amount,
                'email': email,
                'return_url': normal_return_url or '',
                'direct_notification_url': automatic_return_url or '',
                'origin': self.origin
        }
        query.update(dict(name=name, address=address, email=email, phone=phone,
            orderid=orderid, info1=info1, info2=info2, info3=info3))
        for key in query.keys():
            if query[key] is None:
                del query[key]
        url = '%s?%s' % (SERVICE_URL, urllib.urlencode(query))
        return transaction_id, URL, url

    def response(self, query_string, logger=LOGGER, **kwargs):
        form = parse_qs(query_string)
        if not 'transaction_id' in form:
            raise ResponseError()
        transaction_id = form.get('transaction_id',[''])[0]
        form[self.BANK_ID] = transaction_id

        signed = 'signed' in form
        if signed:
            content = 'signature ok'
        else:
            content = None
        signed = signed or self.consider_all_response_signed
        result = PAID if 'ok' in form else ERROR

        response = PaymentResponse(result=result,
                signed=signed,
                bank_data=form,
                return_content=content,
                order_id=transaction_id,
                transaction_id=transaction_id,
                bank_status=form.get('reason'),
                test=True)
        return response

    def validate(self, amount, bank_data, **kwargs):
        return {}

    def cancel(self, amount, bank_data, **kwargs):
        return {}

if __name__ == '__main__':
    options = {
            'direct_notification_url': 'http://example.com/direct_notification_url',
            'siret': '1234',
            'origin': 'Mairie de Perpette-les-oies'
    }
    p = Payment(options)
    retour = 'http://example.com/retour?amount=10.0&direct_notification_url=http%3A%2F%2Fexample.com%2Fdirect_notification_url&email=toto%40example.com&transaction_id=6Tfw2e1bPyYnz7CedZqvdHt7T9XX6T&return_url=http%3A%2F%2Fexample.com%2Fretour&nok=1'
    r = p.response(retour.split('?',1)[1])
    assert not r[0]
    assert r[1] == '6Tfw2e1bPyYnz7CedZqvdHt7T9XX6T'
    assert r[3] is None
    retour = 'http://example.com/retour?amount=10.0&direct_notification_url=http%3A%2F%2Fexample.com%2Fdirect_notification_url&email=toto%40example.com&transaction_id=6Tfw2e1bPyYnz7CedZqvdHt7T9XX6T&return_url=http%3A%2F%2Fexample.com%2Fretour&ok=1&signed=1'
    r = p.response(retour.split('?',1)[1])
    assert r[0]
    assert r[1] == '6Tfw2e1bPyYnz7CedZqvdHt7T9XX6T'
    assert r[3] == 'signature ok'
