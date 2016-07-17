#!/usr/bin/env python
# -*- coding: utf-8 -*-
#--------------------------------------------------------------
# Application :    Connecthys, le portail internet de Noethys
# Site internet :  www.noethys.com
# Auteur:          Ivan LUCAS
# Copyright:       (c) 2010-16 Ivan LUCAS
# Licence:         Licence GNU GPL
#--------------------------------------------------------------

import datetime
from models import *


def Creation_donnees_fictives():
    """ Création de données fictives pour les tests """
    # Création d'un utilisateur
    m = User(identifiant='demo', decryptpassword="demo", nom='PALLIER Jean-Michel et Marie', email='test@test.com', role="famille", IDfamille=1)
    db.session.add(m)
    
    # Création de factures
    m = Facture(IDfacture=1, IDfamille=1, numero="000001", date_edition=datetime.date(2016, 2, 1), date_debut=datetime.date(2016, 1, 1),\
                date_fin=datetime.date(2016, 1, 31), montant=100.0, montant_regle=90.0, montant_solde=10.0)
    db.session.add(m)

    m = Facture(IDfacture=2, IDfamille=1, numero="000002", date_edition=datetime.date(2016, 3, 1), date_debut=datetime.date(2016, 2, 1),\
                date_fin=datetime.date(2016, 2, 28), montant=50.0, montant_regle=50.0, montant_solde=0.0)
    db.session.add(m)

    m = Facture(IDfacture=3, IDfamille=1, numero="000003", date_edition=datetime.date(2016, 4, 1), date_debut=datetime.date(2016, 3, 1),\
                date_fin=datetime.date(2016, 3, 31), montant=30.0, montant_regle=15.0, montant_solde=15.0)
    db.session.add(m)
        
    # Création de règlements
    m = Reglement(IDreglement=1, IDfamille=1, date=datetime.date(2016, 6, 7), mode=u"Chèque", \
                    numero="xxx2341", montant=10.0, date_encaissement=None)
    db.session.add(m)

    m = Reglement(IDreglement=2, IDfamille=1, date=datetime.date(2016, 6, 8), mode=u"Espèces", \
                    numero="xxx2342", montant=20.0, date_encaissement=datetime.date(2016, 6, 9))
    db.session.add(m)

    m = Reglement(IDreglement=3, IDfamille=1, date=datetime.date(2016, 6, 9), mode=u"Chèque", \
                    numero="xxx2343", montant=30.0, date_encaissement=None)
    db.session.add(m)

    # Création de pièces manquantes
    m = Piece_manquante(IDfamille=1, IDtype_piece=1, IDindividu=None, nom=u"Fiche famille")
    db.session.add(m)

    m = Piece_manquante(IDfamille=1, IDtype_piece=2, IDindividu=1, nom=u"Fiche sanitaire de Noémie")
    db.session.add(m)
    
    m = Piece_manquante(IDfamille=1, IDtype_piece=2, IDindividu=2, nom=u"Fiche sanitaire de Kévin")
    db.session.add(m)
    
    # Création de types de pièces
    m = Type_piece(IDtype_piece=1, nom=u"Fiche famille", public="famille", fichier="piece1.pdf")
    db.session.add(m)

    m = Type_piece(IDtype_piece=2, nom=u"Fiche sanitaire", public="individu", fichier="piece1.pdf")
    db.session.add(m)
    
    m = Type_piece(IDtype_piece=3, nom=u"Certificat médical", public="individu", fichier="piece1.pdf")
    db.session.add(m)

    # Création des cotisations manquantes
    m = Cotisation_manquante(IDfamille=1, IDindividu=None, IDtype_cotisation=1, nom=u"Cotisation familiale")
    db.session.add(m)

    # Création des activités
    m = Activite(IDactivite=1, nom=u"Accueil de loisirs", unites_multiples=0)
    db.session.add(m)

    m = Activite(IDactivite=2, nom=u"Garderie périscolaire", unites_multiples=1)
    db.session.add(m)

    # Création des groupes
    m = Groupe(IDgroupe=1, nom=u"3-6 ans", IDactivite=1, ordre=1)
    db.session.add(m)

    m = Groupe(IDgroupe=2, nom=u"6-12 ans", IDactivite=1, ordre=2)
    db.session.add(m)
    
    m = Groupe(IDgroupe=3, nom=u"Groupe unique", IDactivite=2, ordre=1)
    db.session.add(m)

    # Création des individus
    m = Individu(IDindividu=1, IDfamille=1, prenom=u"Kévin", date_naiss=datetime.date(2010, 1, 1), IDcivilite=1)
    db.session.add(m)

    m = Individu(IDindividu=2, IDfamille=1, prenom=u"Sophie", date_naiss=datetime.date(2012, 2, 1), IDcivilite=2)
    db.session.add(m)
    
    # Création des inscriptions
    m = Inscription(IDindividu=1, IDfamille=1, IDactivite=1, IDgroupe=1)
    db.session.add(m)

    m = Inscription(IDindividu=2, IDfamille=1, IDactivite=1, IDgroupe=1)
    db.session.add(m)

    m = Inscription(IDindividu=2, IDfamille=1, IDactivite=2, IDgroupe=3)
    db.session.add(m)

    # Création des unités
    unites = [u"Journée avec repas", u"Journée sans repas", u"Matinée", u"Matinée avec repas", u"Après-midi", u"Après-midi avec repas"]
    index = 1
    for nom_unite in unites :
        m = Unite(nom=nom_unite, IDactivite=1, ordre=index)
        db.session.add(m)
        index += 1

    m = Unite(nom=u"Accueil du matin", IDactivite=2, ordre=1)
    db.session.add(m)
    
    m = Unite(nom=u"Accueil du soir", IDactivite=2, ordre=2)
    db.session.add(m)
        
    # Création des ouvertures
    for mois in (7, 8) :
        for jour in range(1, 31+1) :
            for IDunite in range(1, len(unites)+1) :
                m = Ouverture(date=datetime.date(2016, mois, jour), IDunite=IDunite, IDgroupe=1)
                db.session.add(m)

    for jour in range(1, 30+1) :
        for IDunite in [7, 8] :
            m = Ouverture(date=datetime.date(2016, 9, jour), IDunite=IDunite, IDgroupe=3)
            db.session.add(m)
                
    # Création des périodes
    m = Periode(IDactivite=1, nom=u"Juillet 2016", date_debut=datetime.date(2016, 7, 1), date_fin=datetime.date(2016, 7, 31))
    db.session.add(m)

    m = Periode(IDactivite=1, nom=u"Août 2016", date_debut=datetime.date(2016, 8, 1), date_fin=datetime.date(2016, 8, 31))
    db.session.add(m)

    m = Periode(IDactivite=2, nom=u"Septembre 2016", date_debut=datetime.date(2016, 9, 1), date_fin=datetime.date(2016, 9, 30))
    db.session.add(m)

    # Création des consommations
    m = Consommation(date=datetime.date(2016, 7, 2), IDunite=1, IDinscription=1, etat="reservation")
    db.session.add(m)
    
    m = Consommation(date=datetime.date(2016, 7, 3), IDunite=1, IDinscription=1, etat="reservation")
    db.session.add(m)

    m = Consommation(date=datetime.date(2016, 7, 4), IDunite=3, IDinscription=1, etat="reservation")
    db.session.add(m)
    
    # Envoi des enregistrements
    db.session.commit()

