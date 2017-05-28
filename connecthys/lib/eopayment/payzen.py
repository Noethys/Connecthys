from copy import deepcopy

from . import systempayv2

__all__ = ['Payment']

class Payment(systempayv2.Payment):
    service_url = 'https://secure.payzen.eu/vads-payment/'

    description = deepcopy(systempayv2.Payment.description)
    description['caption'] = 'PayZen'
    for param in description['parameters']:
        if param['name'] == 'service_url':
            param['default'] = service_url
            break
