#!/usr/bin/env python
# -*- coding: utf-8 -*-
#--------------------------------------------------------------
# Application :    Connecthys, le portail internet de Noethys
# Site internet :  www.noethys.com
# Auteur:          Ivan LUCAS
# Copyright:       (c) 2010-16 Ivan LUCAS
# Licence:         Licence GNU GPL
#--------------------------------------------------------------


import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config_application(object):
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    SQLALCHEMY_ECHO = False
    SECRET_KEY = "super-secret"
    WTF_CSRF_ENABLED = True
    DEBUG = True

class Config_utilisateur(object):
    SKIN = "skin-blue" # blue, black, green, purple, red, yellow
    IMAGE_FOND = "plage.jpg"
    ORGANISATEUR_NOM = u"Centre de Loisirs de Noethys"
    ORGANISATEUR_RUE = u"10 Rue des tests"
    ORGANISATEUR_CP = u"29200"
    ORGANISATEUR_VILLE = u"BREST"
    ORGANISATEUR_TEL = u"02.90.12.34.56."
    ORGANISATEUR_FAX = None
    ORGANISATEUR_EMAIL = "organisateur@test.fr"
    ORGANISATEUR_IMAGE = 'logo.png'
    ORGANISATEUR_IMAGE_ROND = False
    PAIEMENT_EN_LIGNE_ACTIF = True
    RECEVOIR_DOCUMENT_EMAIL = True
    RECEVOIR_DOCUMENT_POSTE = True
    RECEVOIR_DOCUMENT_RETIRER = True
    RECEVOIR_DOCUMENT_RETIRER_LIEU = u"à l'accueil de la structure"

