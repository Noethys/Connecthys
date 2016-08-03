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
from sqlalchemy import func


def Exportation(secret=0, last=0):
    """ Exportation des données vers le serveur """
    # Codage et vérification de la clé de sécurité
    secret_key = str(datetime.datetime.now().strftime("%Y%m%d"))
    for caract in app.config['SECRET_KEY'] :
        if caract in "0123456789" :
            secret_key += caract
    secret_key = int(secret_key) 
    
    if secret_key != secret :
        return u"Erreur de clé de sécurité"
    
    if last == 0 :
        liste_actions = models.Action.query.filter(models.Action.etat != "suppression").all()
    else :
        # Lecture de l'horodatage et de l'IDfamille envoyés à travers le last
        last = str(last)
        horodatage = datetime.datetime(int(last[0:4]), int(last[4:6]), int(last[6:8]), int(last[8:10]), int(last[10:12]), int(last[12:14]), int(last[14:20]))
        IDfamille = int(last[-6:])
        
        # Recherche de la dernière action téléchargée
        #last_action = models.Action.query.filter(func.strftime('%Y-%m-%d', models.Action.horodatage) == str(horodatage.date()), func.strftime('%H:%M:%S', models.Action.horodatage) == str(horodatage.time()), models.Action.IDfamille==IDfamille).first()
        last_action = models.Action.query.filter(models.Action.ref_unique == last).first()
        
        if last_action != None :
            liste_actions = models.Action.query.filter(models.Action.IDaction > last_action.IDaction, models.Action.etat == "attente").order_by(models.Action.IDaction).all()
        else :
            liste_actions = models.Action.query.filter(models.Action.horodatage > horodatage, models.Action.etat == "attente").order_by(models.Action.IDaction).all()
        
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