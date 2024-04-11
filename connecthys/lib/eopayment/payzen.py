# eopayment - online payment library
# Copyright (C) 2011-2020 Entr'ouvert
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


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
