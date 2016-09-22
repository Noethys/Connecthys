#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config_application(object):
     SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'data.db')
     SQLALCHEMY_TRACK_MODIFICATIONS = True
     SQLALCHEMY_ECHO = False
     SECRET_KEY = "wA1cb1CVV9yyx693A7199YYb6hm8B3A2Wc4yfm84"
     WTF_CSRF_ENABLED = True
     DEBUG = True

class Config_utilisateur(object):
     IDfichier = "20141215142702EMX"
     SKIN = "skin-blue"
     IMAGE_FOND = u""
     ORGANISATEUR_IMAGE_ROND = False
     ORGANISATEUR_NOM = u"Association Goutatou"
     ORGANISATEUR_RUE = u"6 bis rue des clos"
     ORGANISATEUR_CP = u"51390"
     ORGANISATEUR_VILLE = u"PARGNY LES REIMS"
     ORGANISATEUR_TEL = u"03.26.05.87.25."
     ORGANISATEUR_FAX = u""
     ORGANISATEUR_EMAIL = u"goutatou@orange.fr"
     ORGANISATEUR_IMAGE = u"logo.png"
     RECEVOIR_DOCUMENT_EMAIL = True
     RECEVOIR_DOCUMENT_POSTE = True
     RECEVOIR_DOCUMENT_RETIRER = True
     RECEVOIR_DOCUMENT_RETIRER_LIEU = u"à l'accueil de la structure"
     PAIEMENT_EN_LIGNE_ACTIF = False
     ACTIVITES_AFFICHER = True
     ACTIVITES_AUTORISER_INSCRIPTION = True
     RESERVATIONS_AFFICHER = True
     FACTURES_AFFICHER = True
     FACTURES_DEMANDE_FACTURE = True
     REGLEMENTS_AFFICHER = True
     REGLEMENTS_DEMANDE_RECU = True
     PIECES_AFFICHER = True
     PIECES_AUTORISER_TELECHARGEMENT = True
     COTISATIONS_AFFICHER = True
     HISTORIQUE_AFFICHER = True
     HISTORIQUE_DELAI = 0
     CONTACT_AFFICHER = True
     MENTIONS_AFFICHER = True
     AIDE_AFFICHER = True
