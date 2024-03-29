#!/usr/bin/env python
# -*- coding: utf-8 -*-
#--------------------------------------------------------------
# Application :    Connecthys, le portail internet de Noethys
# Site internet :  www.noethys.com
# Auteur:          Ivan LUCAS
# Copyright:       (c) 2010-16 Ivan LUCAS
# Licence:         Licence GNU GPL
#--------------------------------------------------------------

from application import app, db, models
from flask import json, Response
import datetime, os
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
    
    # Mémorise la date de la dernière synchro
    maintenant_str = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")
    m = models.Parametre.query.filter_by(nom="derniere_synchro").first()
    if m == None :
        m = models.Parametre(nom="derniere_synchro", parametre=maintenant_str)
        db.session.add(m)
    else :
        m.parametre = maintenant_str
    db.session.commit()

    # Nettoyage du répertoire des pièces
    if os.path.isdir(app.REP_PIECES):
        liste_pieces = os.listdir(app.REP_PIECES)
        if liste_pieces:
            # Nettoyage des pièces validées
            liste_actions = models.Action.query.filter(models.Action.categorie=="pieces", models.Action.ventilation==None, datetime.datetime.now() > (models.Action.horodatage + datetime.timedelta(days=0)), models.Action.etat=="validation").all()
            for action in liste_actions:
                nom_fichier = action.GetParametres().get("chemin", None)
                if nom_fichier:
                    chemin_fichier = os.path.join(app.REP_PIECES, nom_fichier)
                    if os.path.isfile(chemin_fichier):
                        app.logger.debug("Suppression de la piece %s" % nom_fichier)
                        os.remove(chemin_fichier)
                        action.ventilation = "suppr"
            db.session.commit()

            # Nettoyage des anciennes pièces qui traînent
            for nom_fichier in liste_pieces:
                try:
                    chemin_fichier = os.path.join(app.REP_PIECES, nom_fichier)
                    modif_date = datetime.datetime.fromtimestamp(os.path.getmtime(chemin_fichier)).date()
                    if modif_date < datetime.date.today() - datetime.timedelta(days=365):
                        os.remove(chemin_fichier)
                except Exception as err:
                    pass

    # Encodage des champs spéciaux (dates...)
    def Encoder(obj):
        """JSON encoder function for SQLAlchemy special classes."""
        if isinstance(obj, datetime.date):
            return str(obj)

    # Renvoie le JSON
    js = json.dumps(liste_dict_actions, default=Encoder)
    resp = Response(js, status=200, mimetype='application/json', content_type='application/json; charset=utf-8')
    return resp