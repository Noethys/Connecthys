#!/usr/bin/env python
# -*- coding: utf-8 -*-
#--------------------------------------------------------------
# Application :    Connecthys, le portail internet de Noethys
# Site internet :  www.noethys.com
# Auteur:          Ivan LUCAS
# Copyright:       (c) 2010-16 Ivan LUCAS
# Licence:         Licence GNU GPL
#--------------------------------------------------------------

from application import app, models
from flask import json, Response
import datetime


def Exportation(secret=0):
    """ Exportation des données vers le serveur """
    # Codage et vérification de la clé de sécurité
    secret_key = str(datetime.datetime.now().strftime("%Y%m%d"))
    for caract in app.config['SECRET_KEY'] :
        if caract in "0123456789" :
            secret_key += caract
    secret_key = int(secret_key) 
    
    if secret_key != secret :
        return u"Erreur de clé de sécurité"
    
    liste_actions = models.Action.query.all()
    
    # Transformation de chaque enregistrement en dict
    liste_dict_actions = []
    for action in liste_actions :
        liste_dict_actions.append(action.as_dict())

    # Encodage des champs spéciaux (dates...)
    def Encoder(obj):
        """JSON encoder function for SQLAlchemy special classes."""
        if isinstance(obj, datetime.date):
            return str(obj)

    # Renvoie le JSON
    js = json.dumps(liste_dict_actions, default=Encoder)
    resp = Response(js, status=200, mimetype='application/json', content_type='application/json; charset=utf-8')
    return resp