# -*- coding: utf-8 -*-
import hashlib
import string
import urlparse
from decimal import Decimal, ROUND_HALF_UP

from common import (PaymentCommon, PaymentResponse, FORM, CANCELLED, PAID,
        ERROR, Form, DENIED, ACCEPTED, ORDERID_TRANSACTION_SEPARATOR,
        ResponseError, force_byte, force_text)
def N_(message): return message

ENVIRONMENT_TEST = 'TEST'
ENVIRONMENT_TEST_URL = 'https://secure.ogone.com/ncol/test/orderstandard.asp'
ENVIRONMENT_PROD = 'PROD'
ENVIRONMENT_PROD_URL = 'https://secure.ogone.com/ncol/prod/orderstandard.asp'
ENVIRONMENT = [ENVIRONMENT_TEST, ENVIRONMENT_PROD]

SHA_IN_PARAMS = """
ACCEPTANCE
ACCEPTURL
ADDMATCH
ADDRMATCH
AIACTIONNUMBER
AIAGIATA
AIAIRNAME
AIAIRTAX
AIBOOKIND*XX*
AICARRIER*XX*
AICHDET
AICLASS*XX*
AICONJTI
AIDEPTCODE
AIDESTCITY*XX*
AIDESTCITYL*XX*
AIEXTRAPASNAME*XX*
AIEYCD
AIFLDATE*XX*
AIFLNUM*XX*
AIGLNUM
AIINVOICE
AIIRST
AIORCITY*XX*
AIORCITYL*XX*
AIPASNAME
AIPROJNUM
AISTOPOV*XX*
AITIDATE
AITINUM
AITINUML*XX*
AITYPCH
AIVATAMNT
AIVATAPPL
ALIAS
ALIASOPERATION
ALIASPERSISTEDAFTERUSE
ALIASUSAGE
ALLOWCORRECTION
AMOUNT
AMOUNT*XX*
AMOUNTHTVA
AMOUNTTVA
ARP_TRN
BACKURL
BATCHID
BGCOLOR
BLVERNUM
BIC
BIN
BRAND
BRANDVISUAL
BUTTONBGCOLOR
BUTTONTXTCOLOR
CANCELURL
CARDNO
CATALOGURL
CAVV_3D
CAVVALGORITHM_3D
CERTID
CHECK_AAV
CIVILITY
CN
COM
COMPLUS
CONVCCY
COSTCENTER
COSTCODE
CREDITCODE
CREDITDEBIT
CUID
CURRENCY
CVC
CVCFLAG
DATA
DATATYPE
DATEIN
DATEOUT
DBXML
DCC_COMMPERC
DCC_CONVAMOUNT
DCC_CONVCCY
DCC_EXCHRATE
DCC_EXCHRATETS
DCC_INDICATOR
DCC_MARGINPERC
DCC_REF
DCC_SOURCE
DCC_VALID
DECLINEURL
DELIVERYDATE
DEVICE
DISCOUNTRATE
DISPLAYMODE
ECI
ECI_3D
ECOM_BILLTO_COMPANY
ECOM_BILLTO_POSTAL_CITY
ECOM_BILLTO_POSTAL_COUNTRYCODE
ECOM_BILLTO_POSTAL_COUNTY
ECOM_BILLTO_POSTAL_NAME_FIRST
ECOM_BILLTO_POSTAL_NAME_LAST
ECOM_BILLTO_POSTAL_NAME_PREFIX
ECOM_BILLTO_POSTAL_POSTALCODE
ECOM_BILLTO_POSTAL_STREET_LINE1
ECOM_BILLTO_POSTAL_STREET_LINE2
ECOM_BILLTO_POSTAL_STREET_LINE3
ECOM_BILLTO_POSTAL_STREET_NUMBER
ECOM_BILLTO_TELECOM_MOBILE_NUMBER
ECOM_BILLTO_TELECOM_PHONE_NUMBER
ECOM_CONSUMERID
ECOM_CONSUMER_GENDER
ECOM_CONSUMEROGID
ECOM_CONSUMERORDERID
ECOM_CONSUMERUSERALIAS
ECOM_CONSUMERUSERPWD
ECOM_CONSUMERUSERID
ECOM_ESTIMATEDDELIVERYDATE
ECOM_ESTIMATEDELIVERYDATE
ECOM_PAYMENT_CARD_EXPDATE_MONTH
ECOM_PAYMENT_CARD_EXPDATE_YEAR
ECOM_PAYMENT_CARD_NAME
ECOM_PAYMENT_CARD_VERIFICATION
ECOM_SHIPMETHOD
ECOM_SHIPMETHODDETAILS
ECOM_SHIPMETHODSPEED
ECOM_SHIPMETHODTYPE
ECOM_SHIPTO_COMPANY
ECOM_SHIPTO_DOB
ECOM_SHIPTO_ONLINE_EMAIL
ECOM_SHIPTO_POSTAL_CITY
ECOM_SHIPTO_POSTAL_COUNTRYCODE
ECOM_SHIPTO_POSTAL_COUNTY
ECOM_SHIPTO_POSTAL_NAME_FIRST
ECOM_SHIPTO_POSTAL_NAME_LAST
ECOM_SHIPTO_POSTAL_NAME_PREFIX
ECOM_SHIPTO_POSTAL_POSTALCODE
ECOM_SHIPTO_POSTAL_STATE
ECOM_SHIPTO_POSTAL_STREET_LINE1
ECOM_SHIPTO_POSTAL_STREET_LINE2
ECOM_SHIPTO_POSTAL_STREET_NUMBER
ECOM_SHIPTO_TELECOM_FAX_NUMBER
ECOM_SHIPTO_TELECOM_MOBILE_NUMBER
ECOM_SHIPTO_TELECOM_PHONE_NUMBER
ECOM_SHIPTO_TVA
ED
EMAIL
EXCEPTIONURL
EXCLPMLIST
EXECUTIONDATE*XX*
FACEXCL*XX*
FACTOTAL*XX*
FIRSTCALL
FLAG3D
FONTTYPE
FORCECODE1
FORCECODE2
FORCECODEHASH
FORCEPROCESS
FORCETP
FP_ACTIV
GENERIC_BL
GIROPAY_ACCOUNT_NUMBER
GIROPAY_BLZ
GIROPAY_OWNER_NAME
GLOBORDERID
GUID
HDFONTTYPE
HDTBLBGCOLOR
HDTBLTXTCOLOR
HEIGHTFRAME
HOMEURL
HTTP_ACCEPT
HTTP_USER_AGENT
INCLUDE_BIN
INCLUDE_COUNTRIES
INITIAL_REC_TRN
INVDATE
INVDISCOUNT
INVLEVEL
INVORDERID
ISSUERID
IST_MOBILE
ITEM_COUNT
ITEMATTRIBUTES*XX*
ITEMCATEGORY*XX*
ITEMCOMMENTS*XX*
ITEMDESC*XX*
ITEMDISCOUNT*XX*
ITEMFDMPRODUCTCATEG*XX*
ITEMID*XX*
ITEMNAME*XX*
ITEMPRICE*XX*
ITEMQUANT*XX*
ITEMQUANTORIG*XX*
ITEMUNITOFMEASURE*XX*
ITEMVAT*XX*
ITEMVATCODE*XX*
ITEMWEIGHT*XX*
LANGUAGE
LEVEL1AUTHCPC
LIDEXCL*XX*
LIMITCLIENTSCRIPTUSAGE
LINE_REF
LINE_REF1
LINE_REF2
LINE_REF3
LINE_REF4
LINE_REF5
LINE_REF6
LIST_BIN
LIST_COUNTRIES
LOGO
MANDATEID
MAXITEMQUANT*XX*
MERCHANTID
MODE
MTIME
MVER
NETAMOUNT
OPERATION
ORDERID
ORDERSHIPCOST
ORDERSHIPMETH
ORDERSHIPTAX
ORDERSHIPTAXCODE
ORIG
OR_INVORDERID
OR_ORDERID
OWNERADDRESS
OWNERADDRESS2
OWNERCTY
OWNERTELNO
OWNERTELNO2
OWNERTOWN
OWNERZIP
PAIDAMOUNT
PARAMPLUS
PARAMVAR
PAYID
PAYMETHOD
PM
PMLIST
PMLISTPMLISTTYPE
PMLISTTYPE
PMLISTTYPEPMLIST
PMTYPE
POPUP
POST
PSPID
PSWD
RECIPIENTACCOUNTNUMBER
RECIPIENTDOB
RECIPIENTLASTNAME
RECIPIENTZIP
REF
REFER
REFID
REFKIND
REF_CUSTOMERID
REF_CUSTOMERREF
REGISTRED
REMOTE_ADDR
REQGENFIELDS
RNPOFFERT
RTIMEOUT
RTIMEOUTREQUESTEDTIMEOUT
SCORINGCLIENT
SEQUENCETYPE
SETT_BATCH
SID
SIGNDATE
STATUS_3D
SUBSCRIPTION_ID
SUB_AM
SUB_AMOUNT
SUB_COM
SUB_COMMENT
SUB_CUR
SUB_ENDDATE
SUB_ORDERID
SUB_PERIOD_MOMENT
SUB_PERIOD_MOMENT_M
SUB_PERIOD_MOMENT_WW
SUB_PERIOD_NUMBER
SUB_PERIOD_NUMBER_D
SUB_PERIOD_NUMBER_M
SUB_PERIOD_NUMBER_WW
SUB_PERIOD_UNIT
SUB_STARTDATE
SUB_STATUS
TAAL
TAXINCLUDED*XX*
TBLBGCOLOR
TBLTXTCOLOR
TID
TITLE
TOTALAMOUNT
TP
TRACK2
TXTBADDR2
TXTCOLOR
TXTOKEN
TXTOKENTXTOKENPAYPAL
TXSHIPPING
TXSHIPPINGLOCATIONPROFILE
TXURL
TXVERIFIER
TYPE_COUNTRY
UCAF_AUTHENTICATION_DATA
UCAF_PAYMENT_CARD_CVC2
UCAF_PAYMENT_CARD_EXPDATE_MONTH
UCAF_PAYMENT_CARD_EXPDATE_YEAR
UCAF_PAYMENT_CARD_NUMBER
USERID
USERTYPE
VERSION
WBTU_MSISDN
WBTU_ORDERID
WEIGHTUNIT
WIN3DS
WITHROOT
""".split()

SHA_OUT_PARAMS = """
AAVADDRESS
AAVCHECK
AAVMAIL
AAVNAME
AAVPHONE
AAVZIP
ACCEPTANCE
ALIAS
AMOUNT
BIC
BIN
BRAND
CARDNO
CCCTY
CN
COLLECTOR_BIC
COLLECTOR_IBAN
COMPLUS
CREATION_STATUS
CREDITDEBIT
CURRENCY
CVCCHECK
DCC_COMMPERCENTAGE
DCC_CONVAMOUNT
DCC_CONVCCY
DCC_EXCHRATE
DCC_EXCHRATESOURCE
DCC_EXCHRATETS
DCC_INDICATOR
DCC_MARGINPERCENTAGE
DCC_VALIDHOURS
DEVICEID
DIGESTCARDNO
ECI
ED
EMAIL
ENCCARDNO
FXAMOUNT
FXCURRENCY
IP
IPCTY
MANDATEID
MOBILEMODE
NBREMAILUSAGE
NBRIPUSAGE
NBRIPUSAGE_ALLTX
NBRUSAGE
NCERROR
ORDERID
PAYID
PAYMENT_REFERENCE
PM
SCO_CATEGORY
SCORING
SEQUENCETYPE
SIGNDATE
STATUS
SUBBRAND
SUBSCRIPTION_ID
TRXDATE
VC"""

class Payment(PaymentCommon):
    # See http://payment-services.ingenico.com/fr/fr/ogone/support/guides/integration%20guides/e-commerce
    description = {
        'caption': N_('Système de paiement Ogone / Ingenico Payment System e-Commerce'),
        'parameters': [
            {
                'name': 'normal_return_url',
                'caption': N_('Normal return URL'),
                'default': '',
                'required': True,
            },
            {
                'name': 'automatic_return_url',
                'caption': N_('Automatic return URL (ignored, must be set in Ogone backoffice)'),
                'required': False,
            },
            {'name': 'environment',
                'default': ENVIRONMENT_TEST,
                'caption': N_(u'Environnement'),
                'choices': ENVIRONMENT,
            },
            {'name': 'pspid',
                'caption': N_(u"Nom d'affiliation dans le système"),
                'required': True,
            },
            {'name': 'language',
                'caption': N_(u'Langage'),
                'default': 'fr_FR',
                'choices': (('fr_FR', N_('français')),),
            },
            {'name': 'hash_algorithm',
                'caption': N_(u'Algorithme de hachage'),
                'default': 'sha1',
            },
            {'name': 'sha_in',
                'caption': N_(u'Clé SHA-IN'),
                'required': True,
            },
            {'name': 'sha_out',
                'caption': N_(u'Clé SHA-OUT'),
                'required': True,
            },
            {'name': 'currency',
                'caption': N_(u'Monnaie'),
                'default': 'EUR',
                'choices': ('EUR',),
            },
        ]
    }

    def sha_sign(self, algo, key, params, keep):
        '''Ogone signature algorithm of query string'''
        values = params.items()
        values = [(a.upper(), b) for a, b in values]
        values = sorted(values)
        values = [u'%s=%s' % (a, b) for a, b in values if a in keep]
        tosign = key.join(values)
        tosign += key
        tosign = force_byte(tosign)
        hashing = getattr(hashlib, algo)
        return hashing(tosign).hexdigest().upper()

    def sha_sign_in(self, params):
        return self.sha_sign(self.hash_algorithm, self.sha_in, params, SHA_IN_PARAMS)

    def sha_sign_out(self, params):
        return self.sha_sign(self.hash_algorithm, self.sha_out, params, SHA_OUT_PARAMS)

    def get_request_url(self):
        if self.environment == ENVIRONMENT_TEST:
            return ENVIRONMENT_TEST_URL
        if self.environment == ENVIRONMENT_PROD:
            return ENVIRONMENT_PROD_URL
        raise NotImplementedError('unknown environment %s' % self.environment)

    def request(self, amount, orderid=None, name=None, email=None,
            language=None, description=None, **kwargs):

        reference = self.transaction_id(20, string.digits + string.ascii_letters)

        # prepend order id in payment reference
        if orderid:
            if len(orderid) > 24:
                raise ValueError('orderid length exceeds 25 characters')
            reference = orderid + ORDERID_TRANSACTION_SEPARATOR + self.transaction_id(29-len(orderid), string.digits + string.ascii_letters)
        language = language or self.language
        # convertir en centimes
        amount = Decimal(amount) * 100
        # arrondi comptable francais
        amount = amount.quantize(Decimal('1.'), rounding=ROUND_HALF_UP)
        params = {
                'AMOUNT': unicode(amount),
                'ORDERID': reference,
                'PSPID': self.pspid,
                'LANGUAGE': language,
                'CURRENCY': self.currency,
        }
        if self.normal_return_url:
            params['ACCEPTURL'] = self.normal_return_url
            params['BACKURL'] = self.normal_return_url
            params['CANCELURL'] = self.normal_return_url
            params['DECLINEURL'] = self.normal_return_url
            params['EXCEPTIONURL'] = self.normal_return_url
        if name:
            params['CN'] = name
        if email:
            params['EMAIL'] = email
        if description:
            params['COM'] = description
        for key, value in kwargs.iteritems():
            params[key.upper()] = value
        params['SHASIGN'] = self.sha_sign_in(params)
        # uniformize all values to UTF-8 string
        for key in params:
            params[key] = force_text(params[key])
        url = self.get_request_url()
        form = Form(
                url=url,
                method='POST',
                fields=[{'type': 'hidden',
                         'name': key,
                         'value': params[key]} for key in params])
        return reference, FORM, form

    def response(self, query_string, **kwargs):
        params = urlparse.parse_qs(query_string, True)
        params = dict((key.upper(), params[key][0]) for key in params)
        if not set(params) >= set(['ORDERID', 'PAYID', 'STATUS', 'NCERROR']):
            raise ResponseError()

        # uniformize iso-8859-1 encoded values
        for key in params:
            params[key] = force_text(params[key], 'iso-8859-1')
        reference = params['ORDERID']
        transaction_id = params['PAYID']
        status = params['STATUS']
        error = params['NCERROR']
        signed = False
        if self.sha_in:
            signature = params.get('SHASIGN')
            expected_signature = self.sha_sign_out(params)
            signed = signature == expected_signature
            print 'signed', signature
            print 'expected', expected_signature
        if status == '1':
            result = CANCELLED
        elif status == '2':
            result = DENIED
        elif status == '5':
            result = ACCEPTED
        elif status == '9':
            result = PAID
        else:
            self.logger.error('response STATUS=%s NCERROR=%s NCERRORPLUS=%s',
                    status, error, params.get('NCERRORPLUS', ''))
            result = ERROR
        # extract reference from received order id
        if ORDERID_TRANSACTION_SEPARATOR in reference:
            reference, transaction_id = reference.split(ORDERID_TRANSACTION_SEPARATOR, 1)
        return PaymentResponse(
                result=result,
                signed=signed,
                bank_data=params,
                order_id=reference,
                transaction_id=transaction_id)
