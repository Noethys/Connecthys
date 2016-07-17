#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config_application(object):
     SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'data.db')
     SQLALCHEMY_TRACK_MODIFICATIONS = True
     SQLALCHEMY_ECHO = False
     SECRET_KEY = "secret_key"
     WTF_CSRF_ENABLED = True
     DEBUG = True

class Config_utilisateur(object):
     SKIN = "skin-blue"
     IMAGE_FOND = u"plage.jpg"
     ORGANISATEUR_IMAGE_ROND = False
     ORGANISATEUR_NOM = u"Structure Noethys"
     ORGANISATEUR_RUE = u"10 rue des tests"
     ORGANISATEUR_CP = u"29200"
     ORGANISATEUR_VILLE = u"BREST"
     ORGANISATEUR_TEL = u"02.98.01.02.03."
     ORGANISATEUR_FAX = u"02.98.01.02.03."
     ORGANISATEUR_EMAIL = u"noethys@test.com"
     ORGANISATEUR_IMAGE = u"logo.png"
     RECEVOIR_DOCUMENT_EMAIL = True
     RECEVOIR_DOCUMENT_POSTE = True
     RECEVOIR_DOCUMENT_RETIRER = True
     RECEVOIR_DOCUMENT_RETIRER_LIEU = u"à l'accueil de la structure"
     PAIEMENT_EN_LIGNE_ACTIF = True
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
     CONTACT_AFFICHER = True
     MENTIONS_AFFICHER = True
     AIDE_AFFICHER = True
