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
    Session = sessionmaker(bind=engine)
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
    destination, dengine = make_session(to_db)
    dmeta = MetaData(bind=dengine)
    
    # Liste des tables à transférer
    tables = [
        "cotisations_manquantes", "factures", "types_pieces", "users", "pieces_manquantes",
        "reglements", "consommations", "periodes", "ouvertures", "unites", "inscriptions",
        "groupes", "activites", "individus",
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
            u = u.values({"etat" : action.etat, "traitement_date" : action.traitement_date})
            u = u.where(table_actions_destination.c.ref_unique == action.ref_unique)
            dengine.execute(u)
        
        destination.commit()
    
    # Suppression des tables
    for nom_table in tables:
        try :
            dengine.execute("DROP TABLE %s" % "%sportail_%s" % (PREFIXE_TABLES, nom_table))
        except :
            pass
        
    # Création des tables
    db.create_all()

    # Remplissage des tables (ordre spécial)
    tables = [
        "activites", "unites", "cotisations_manquantes", "factures", "types_pieces", "users", "pieces_manquantes",
        "reglements", "individus", "groupes", "inscriptions", "consommations", "periodes", "ouvertures", 
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
            
        dengine.execute(dtable.insert(), listeDonnees)
    
    # Commit de l'importation des tables
    destination.commit()
    
    if "mysql" in to_db :
        dengine.execute("SET foreign_key_checks = 1;")
    
    # Fermeture et suppression de la base d'import
    source.close()
    os.remove(os.path.join(basedir, "data/" + os.path.basename(nomFichierDB)))
    
    
    return True
