#!/usr/bin/env python
# -*- coding: utf-8 -*-
#--------------------------------------------------------------
# Application :    Connecthys, le portail internet de Noethys
# Site internet :  www.noethys.com
# Auteur:          Ivan LUCAS
# Copyright:       (c) 2010-16 Ivan LUCAS
# Licence:         Licence GNU GPL
#--------------------------------------------------------------

try :
    from Crypto.Cipher import AES
    from Crypto import Random
    IMPORT_AES = True
except:
    print 'Application: Crypto.Cipher.AES non disponible'
    IMPORT_AES = False
    
import hashlib
import pickle
import sys
import base64


class CypherText:
    __doc__ = """
    This in an encrypted file. It uses PyCrypt: 
    http://reachme.web.googlepages.com/pycrypt 
    """
    def __init__(self):
        self.__ProjectWebpage = ' http://reachme.web.googlepages.com/pycrypt '
        self.__ProgramVersion = ' 0.2 '
        self.__CypherText = ''
        self.__trailLen = 0

    def getCypherText(self):
        return self.__CypherText

    def setCypherText(self, CText):
        self.__CypherText = CText

    def setTrail(self, TLen):
        self.__trailLen = TLen

    def getTrail(self):
        return self.__trailLen

def hashPassword_MD5(Password):
    m = hashlib.md5()
    m.update(Password)
    return m.hexdigest()

def read_keys_from_file():
    f = open('./keys.txt','r')
    key = ''

    for line in f.readlines():
        if line.find('PUBLIC_KEY = ') != -1:
            key = line.strip('PUBLIC_KEY = ')

    if key == '' or len(key) != 32:
        return -1
    else:
        return key

def encrypt(message, key):
    TrailLen = 0
    #AES requires blocks of 16
    while (len(message) % 16) != 0:
        message  = message + '_'
        TrailLen = TrailLen + 1

    CypherOut = CypherText()
    CypherOut.setTrail(TrailLen)

    cryptu = AES.new(key, AES.MODE_ECB)

    #Try to delete the key from memory
    key = hashPassword_MD5('PYCRYPT_ERASE_')

    CypherOut.setCypherText( cryptu.encrypt(message) )
    return CypherOut

def decrypt(ciphertext, key):
    cryptu = AES.new(key, AES.MODE_ECB)

    #Try to delete the key from memory
    key = hashPassword_MD5('PYCRYPT_ERASE_')

    message_n_trail = cryptu.decrypt(ciphertext.getCypherText())
    return message_n_trail[0:len(message_n_trail) - ciphertext.getTrail()]

def cryptFile(filename_in, filename_out, key):
    fr = open(filename_in, 'rb')
    fileContent = fr.read()
    cyphertext = encrypt(fileContent, key )
    fw = open(filename_out, 'wb')
    pickle.dump( cyphertext, fw, -1 )

def decryptFile(filename_in, filename_out, key):
    fr = open(filename_in, 'rb')
    cyphertext = pickle.load(fr)
    message = decrypt(cyphertext, key)
    fw = open(filename_out, 'wb')
    fw.write(message)


def checkProgArgs(method, filename_in, filename_out, password):
    if (method != 'encrypt') and (method != 'decrypt'):
        print 'ERROR: invalid method: ' + method
        sys.exit(-1)

    #Should it be allowed?
    """
    if filename_in == filename_out:
        print 'ERROR: filename_in == filename_out.'
        sys.exit(-1)
    """

    #++check the existense of filename_in and inexistence of filename_out
    return 0

def CrypterFichier(fichierDecrypte="", fichierCrypte="", motdepasse=""):
    cryptFile(fichierDecrypte, fichierCrypte, hashPassword_MD5(motdepasse))

def DecrypterFichier(fichierCrypte="", fichierDecrypte="", motdepasse=""):
    decryptFile(fichierCrypte, fichierDecrypte, hashPassword_MD5(motdepasse))



# ----------- Cryptage d'un simple texte unicode ------------

class AESCipher(object):
    """
    A classical AES Cipher. Can use any size of data and any size of password thanks to padding.
    Also ensure the coherence and the type of the data with a unicode to byte converter.
    """
    def __init__(self, key, bs=32, prefixe=None):
        self.bs = bs
        self.key = hashlib.sha256(AESCipher.str_to_bytes(key)).digest()
        self.prefixe = prefixe

    @staticmethod
    def str_to_bytes(data):
        u_type = type(b''.decode('utf8'))
        if isinstance(data, u_type):
            return data.encode('utf8')
        return data

    def _pad(self, s):
        return s + (self.bs - len(s) % self.bs) * AESCipher.str_to_bytes(chr(self.bs - len(s) % self.bs))

    @staticmethod
    def _unpad(s):
        return s[:-ord(s[len(s)-1:])]

    def encrypt(self, raw):
        if raw == None :
            return None
        raw = self._pad(AESCipher.str_to_bytes(raw))
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        texte = base64.b64encode(iv + cipher.encrypt(raw)).decode('utf-8')
        if self.prefixe != None :
            texte = self.prefixe + texte
        return texte

    def decrypt(self, enc):
        if enc == None :
            return None
        if self.prefixe != None :
            if enc.startswith(self.prefixe) == False :
                return enc
            else :
                enc = enc[len(self.prefixe):]
        enc = base64.b64decode(enc)
        iv = enc[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return self._unpad(cipher.decrypt(enc[AES.block_size:])).decode('utf-8')
