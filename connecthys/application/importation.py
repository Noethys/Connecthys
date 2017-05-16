#!/usr/bin/env python
# -*- coding: utf-8 -*-
#--------------------------------------------------------------
# Application :    Connecthys, le portail internet de Noethys
# Site internet :  www.noethys.com
# Auteur:          Ivan LUCAS
# Copyright:       (c) 2010-16 Ivan LUCAS
# Licence:         Licence GNU GPL
#--------------------------------------------------------------

import time
import os
import os.path
basedir = os.path.abspath(os.path.dirname(__file__))

from application import db, app, models

if app.config["PREFIXE_TABLES"] == "" :
    PREFIXE_TABLES = ""
else :
    PREFIXE_TABLES = app.config["PREFIXE_TABLES"] + "_"

        
from sqlalchemy import create_engine, MetaData, Table, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from cryptage import IMPORT_AES, DecrypterFichier


def make_session(connection_string):
    engine = create_engine(connection_string, echo=False, convert_unicode=True)
    Session = sessionmaker(bind=engine,autocommit=False)
    return Session(), engine

def quick_mapper(table):
    Base = declarative_base()
    class GenericMapper(Base):
        __table__ = table
    return GenericMapper

def Importation(secret=0):
    """ Importation des données depuis le serveur """
    
    # Vérifie que le fichier d'import existe bien (vérification du code secret)
    nomFichier = os.path.join(basedir, "data/import_%d.crypt" % secret)
    if not os.path.isfile(nomFichier):
        return "fichier crypt inexistant"
        
    # Décryptage du fichier
    if IMPORT_AES == False :
        return "AES non disponible"
    
    cryptage_mdp = app.config['SECRET_KEY'][:10]
    nomFichierZIP = nomFichier.replace(".crypt", ".zip")
    resultat = DecrypterFichier(nomFichier, nomFichierZIP, cryptage_mdp)
    os.remove(nomFichier)
        
    # Décompression du fichier
    import zipfile
    if zipfile.is_zipfile(nomFichierZIP) == False :
        return "Le fichier n'est pas une archive valide"        
    
    nomFichierDB = nomFichierZIP.replace(".zip", ".db")
    fichierZip = zipfile.ZipFile(nomFichierZIP, "r")
    buffer = fichierZip.read(os.path.basename(nomFichierDB))
    
    f = open(nomFichierDB, "wb")
    f.write(buffer)
    f.close()
    fichierZip.close()
    os.remove(nomFichierZIP)

    # Importation des données
    from_db = "sqlite:///" + os.path.join(basedir, "data/" + os.path.basename(nomFichierDB))
    to_db = app.config['SQLALCHEMY_DATABASE_URI']
        
    # Ouvertures des bases
    source, sengine = make_session(from_db)
    smeta = MetaData(bind=sengine)
    destination = db.session
    dengine = db.engine
    dmeta = MetaData(bind=dengine)
    
    # Traitement de la table des paramètres
    #app.logger.debug("Traitement de la table parametres...")
    liste_parametres_destination = destination.query(models.Parametre).all()
    dict_parametres_destination = {}
    for parametre in liste_parametres_destination :
        dict_parametres_destination[parametre.nom] = parametre
    
    liste_parametres_source = source.query(models.Parametre).all()
    for parametre in liste_parametres_source :
        if dict_parametres_destination.has_key(parametre.nom) :
            # Modification si besoin d'un paramètre existant
            if dict_parametres_destination[parametre.nom].parametre != parametre.parametre :
                dict_parametres_destination[parametre.nom].parametre = parametre.parametre
        else :
            # Saisie d'un nouveau paramètre
            destination.add(models.Parametre(nom=parametre.nom, parametre=parametre.parametre))
    
    destination.commit()    
     
    # Traitement de la table users
    app.logger.debug("Traitement de la table users...")
    
    liste_users_destination = destination.query(models.User).all()
    dict_users_destination = {"familles" : {}, "utilisateurs" : {}}
    for user in liste_users_destination :
        if user.IDfamille != None :
            dict_users_destination["familles"][user.IDfamille] = user
        if user.IDutilisateur != None :
            dict_users_destination["utilisateurs"][user.IDutilisateur] = user
    
    liste_users_source = source.query(models.User).all()
    liste_destination = []
    for user_source in liste_users_source :
        user_destination = None
        
        # Recherche si l'user existe déjà dans la base destination
        if user_source.IDfamille != None :
            if dict_users_destination["familles"].has_key(user_source.IDfamille) :
                user_destination = dict_users_destination["familles"][user_source.IDfamille]
        if user_source.IDutilisateur != None :
            if dict_users_destination["utilisateurs"].has_key(user_source.IDutilisateur) :
                user_destination = dict_users_destination["utilisateurs"][user_source.IDutilisateur]
        
        # Si l'user existe déjà, on le modifie si besoin
        if user_destination != None :
            if user_destination.identifiant != user_source.identifiant : user_destination.identifiant = user_source.identifiant
            if user_destination.password != user_source.password : user_destination.password = user_source.password
            if user_destination.nom != user_source.nom : user_destination.nom = user_source.nom
            if user_destination.email != user_source.email : user_destination.email = user_source.email
            if user_destination.actif != user_source.actif : user_destination.actif = user_source.actif
            if user_destination.session_token != user_source.session_token : user_destination.session_token = user_source.session_token
            
        # Si l'utilisateur n'existe pas, on le créé :
        if user_destination == None :
            destination.add(models.User(identifiant=user_source.identifiant, cryptpassword=user_source.password, nom=user_source.nom, email=user_source.email,  \
                                                        role=user_source.role, IDfamille=user_source.IDfamille, IDutilisateur=user_source.IDutilisateur, actif=user_source.actif, \
                                                        session_token=user_source.session_token))
    
    app.logger.debug("Enregistrement de la table users...")

    destination.commit()    
    
    app.logger.debug("Fin de traitement de la table users.")

    # Liste des autres tables à transférer
    app.logger.debug("Traitement des autres tables...")
    tables = [
        "cotisations_manquantes", "factures", "types_pieces", "pieces_manquantes",
        "reglements", "consommations", "periodes", "ouvertures", "unites", "inscriptions",
        "groupes", "activites", "individus", "messages", "regies",
        ]
    
    # Recherche si des actions sont présentes
    nbre_actions_destination = destination.query(func.count(models.Action.IDaction)).scalar()
    
    if nbre_actions_destination == 0 :
        # S'il n'y a aucune actions présentes, on importe toute la table Actions de la source
        tables.append("actions")
    else :
        # Sinon, on importe uniquement l'état des actions
        liste_actions_source = source.query(models.Action).all() 
        
        for action in liste_actions_source :
            
            # Update
            table_actions_destination = Table('%sportail_actions' % PREFIXE_TABLES, dmeta, autoload=True)
            u = table_actions_destination.update()
            u = u.values({"etat" : action.etat, "traitement_date" : action.traitement_date, "reponse" : action.reponse})
            u = u.where(table_actions_destination.c.ref_unique == action.ref_unique)
            dengine.execute(u)
        
    destination.commit()
    
    # Suppression des tables
    for nom_table in tables:
        try :
            dengine.execute("DROP TABLE %s" % "%sportail_%s" % (PREFIXE_TABLES, nom_table))
        except :
            pass
            
    app.logger.debug("Suppression des tables ok.")
    
    # Création des tables
    db.create_all()

    # Remplissage des tables (ordre spécial)
    app.logger.debug("Remplissage des autres tables...")
    
    tables = [
        "activites", "unites", "cotisations_manquantes", "factures", "types_pieces", "pieces_manquantes",
        "reglements", "individus", "groupes", "inscriptions", "consommations", "periodes", "ouvertures", "messages", "regies",
        ]
    
    if "mysql" in to_db :
        dengine.execute("SET foreign_key_checks = 0;")
    
    for nom_table in tables:
        dtable = Table("%sportail_%s" % (PREFIXE_TABLES, nom_table), dmeta, autoload=True)
        stable = Table("portail_%s" % nom_table, smeta, autoload=True)
        NewRecord = quick_mapper(stable)
        columns = stable.columns.keys()
        data = source.query(stable).all()
        listeDonnees = []
        for record in data :
            data = dict([(str(column), getattr(record, column)) for column in columns])
            listeDonnees.append(data) 
        
        if len(listeDonnees) > 0 :
            dengine.execute(dtable.insert(), listeDonnees)
    
    # Commit de l'importation des tables
    destination.commit()
    
    if "mysql" in to_db :
        dengine.execute("SET foreign_key_checks = 1;")
    
    # Fermeture et suppression de la base d'import
    source.close()
    os.remove(os.path.join(basedir, "data/" + os.path.basename(nomFichierDB)))
    
    app.logger.debug("Fin de l'importation.")
    
    return True
