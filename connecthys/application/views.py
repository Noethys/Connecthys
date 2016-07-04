#!/usr/bin/env python
# -*- coding: utf-8 -*-
#--------------------------------------------------------------
# Application :    Connecthys, le portail internet de Noethys
# Site internet :  www.noethys.com
# Auteur:          Ivan LUCAS
# Copyright:       (c) 2010-16 Ivan LUCAS
# Licence:         Licence GNU GPL
#--------------------------------------------------------------

import random, datetime
from flask import Flask, render_template, session, request, flash, url_for, redirect, abort, g, jsonify
from flask_login import LoginManager, login_required, current_user, login_user, logout_user
from application import app, login_manager, db
from application import models, forms, utils, exemples
from sqlalchemy import func



LISTE_PAGES = [
    {"type" : "label", "label" : u"MENU"}, 
        {"type" : "page", "page" : "accueil", "raccourci" : True}, 
    {"type" : "label", "label" : u"VOTRE DOSSIER"}, 
        {"type" : "page", "page" : "inscriptions", "raccourci" : True}, 
        {"type" : "page", "page" : "reservations", "raccourci" : True}, 
        {"type" : "page", "page" : "factures", "raccourci" : True}, 
        {"type" : "page", "page" : "reglements", "raccourci" : True}, 
        {"type" : "page", "page" : "pieces", "raccourci" : True}, 
        {"type" : "page", "page" : "cotisations", "raccourci" : True}, 
        {"type" : "page", "page" : "historique", "raccourci" : True},
    {"type" : "label", "label" : u"INFOS"},     
        {"type" : "page", "page" : "contact", "raccourci" : True}, 
        {"type" : "page", "page" : "mentions", "raccourci" : False},
        {"type" : "page", "page" : "aide", "raccourci" : False},
    ]

DICT_PAGES = {
    "accueil" : {"nom" : u"Accueil", "icone" : "fa-home", "description" : u" ", "couleur" : "white"},
    "inscriptions" : {"nom" : u"Activités", "icone" : "fa-cogs", "description" : u"Consulter et demander des inscriptions", "couleur" : "blue"},
    "reservations" : {"nom" : u"Réservations", "icone" : "fa-calendar", "description" : u"Consulter et demander des réservations", "couleur" : "aqua"},
    "factures" : {"nom" : u"Factures", "icone" : "fa-file-text-o", "description" : u"Consulter et payer des factures", "couleur" : "green"},
    "reglements" : {"nom" : u"Règlements", "icone" : "fa-money", "description" : u"Consulter les règlements", "couleur" : "red"},
    "pieces" : {"nom" : u"Pièces", "icone" : "fa-files-o", "description" : u"Consulter et télécharger des pièces", "couleur" : "orange"},
    "cotisations" : {"nom" : u"Cotisations", "icone" : "fa-folder-o", "description" : u"Consulter les cotisations", "couleur" : "olive"},
    "historique" : {"nom" : u"Historique", "icone" : "fa-clock-o", "description" : u"Consulter l'historique des demandes", "couleur" : "purple"},
    "contact" : {"nom" : u"Contact", "icone" : "fa-envelope-o", "description" : u"Contacter l'organisateur", "couleur" : "yellow"},
    "mentions" : {"nom" : u"Mentions légales", "icone" : "fa-info-circle", "description" : u"Consulter les mentions légales"},
    "aide" : {"nom" : u"Aide", "icone" : "fa-support", "description" : u"Consulter l'aide"},
    }

COULEURS = ["green", "blue", "yellow", "red", "light-blue"]


@login_manager.user_loader
def load_user(id):
    return models.User.query.get(int(id))

@app.before_request
def before_request():
    # Mémorise l'utilisateur en cours
    g.user = current_user
    g.liste_pages = LISTE_PAGES
    g.dict_pages = DICT_PAGES
    g.date_jour = datetime.date.today()
    g.version = "0.0.1"
    
    
@app.route('/initdb')
def initdb():
    db.drop_all()
    db.create_all()
    exemples.Creation_donnees_fictives()
    return u"Base de donnees créée."

@app.route('/')
def index():
    return redirect(url_for('accueil'))


# ------------------------- LOGIN et LOGOUT ---------------------------------- 

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Si l'utilisateur est déjà connecté, on le renvoie vers l'accueil
    if current_user.is_authenticated :
        return redirect(url_for('accueil'))

    # Génération du form de login
    form = forms.LoginForm()
    
    # Affiche la page de login
    if request.method == 'GET':
        return render_template('login.html', form=form)
    
    # Validation du form de login avec Flask-WTF
    if form.validate_on_submit():
    
        # Recherche l'identifiant
        registered_user = models.User.query.filter_by(identifiant=form.identifiant.data).first()
        
        # Codes d'accès corrects
        if registered_user is not None:
        
            # Vérification du mot de passe
            if registered_user.check_password(form.password.data) == False :
                registered_user = None
                flash(u"Mot de passe incorrect" , 'error')
                return redirect(url_for('login'))

            # Mémorisation du remember_me
            remember = form.remember.data
            
            # Mémorisation du user
            login_user(registered_user, remember=remember)
            flash(u"Bienvenue dans le portail Famille")
            
            return redirect(request.args.get('next') or url_for('accueil'))

    # Re-demande codes si incorrects
    flash(u"Codes d'accès incorrects" , 'error')
    return redirect(url_for('login'))
                   
        
@app.route('/logout')
def logout():
    logout_user()
    flash(u"Vous avez été déconnecté", "error")
    return redirect(url_for('login')) 
    
    
    
# ------------------------- ACCUEIL ---------------------------------- 

@app.route('/accueil')
@login_required
def accueil():    
    liste_pieces_manquantes = models.Piece_manquante.query.filter_by(IDfamille=current_user.IDfamille).order_by(models.Piece_manquante.nom).all()
    liste_cotisations_manquantes = models.Cotisation_manquante.query.filter_by(IDfamille=current_user.IDfamille).order_by(models.Cotisation_manquante.nom).all()
    
    return render_template('accueil.html', active_page="accueil",\
                            liste_pieces_manquantes=liste_pieces_manquantes, \
                            liste_cotisations_manquantes=liste_cotisations_manquantes)

    
# ------------------------- FACTURES ---------------------------------- 

@app.route('/factures')
@login_required
def factures():
    # Récupération de la liste des factures
    liste_factures = models.Facture.query.filter_by(IDfamille=current_user.IDfamille).order_by(models.Facture.date_debut.desc()).all()
    
    # Recherche les factures impayées
    nbre_factures_impayees = 0
    montant_factures_impayees = 0.0
    for facture in liste_factures :
        if facture.montant_solde > 0.0 :
            nbre_factures_impayees += 1
            montant_factures_impayees += facture.montant_solde
    
    # Recherche l'historique des demandes liées aux factures
    historique = GetHistorique(IDuser=current_user.IDuser, categorie="factures")
    
    return render_template('factures.html', active_page="factures", liste_factures=liste_factures, \
                            nbre_factures_impayees=nbre_factures_impayees, \
                            montant_factures_impayees=montant_factures_impayees, \
                            historique=historique)

                            
@app.route('/envoyer_demande_facture')
@login_required
def envoyer_demande_facture():
    try:
        id = request.args.get("id", 0, type=int)
        numfacture = request.args.get("info", "", type=str)
        methode_envoi = request.args.get("methode_envoi", "", type=str)
        commentaire = request.args.get("commentaire", "", type=str)
        
        # Enregistrement action
        parametres = u"id=%d#methode_envoi=%s" % (id, methode_envoi)
        if methode_envoi == "email" :
            description = u"Recevoir la facture n°%s par Email" % numfacture
        if methode_envoi == "courrier" :
            description = u"Recevoir la facture n°%s par courrier" % numfacture
        if methode_envoi == "retirer" :
            description = u"Retirer la facture n°%s %s" % (numfacture, app.config["RECEVOIR_DOCUMENT_RETIRER_LIEU"])

        m = models.Action(IDuser=current_user.IDuser, categorie="factures", action="recevoir", description=description, etat="attente", commentaire=commentaire, parametres=parametres)
        db.session.add(m)
        db.session.commit()
        
        flash(u"Votre demande d'une facture a bien été enregistrée")
        return jsonify(success=1)
    except Exception, erreur:
        return jsonify(success=0, error_msg=str(erreur))
                            
                            
# ------------------------- REGLEMENTS ---------------------------------- 

@app.route('/reglements')
@login_required
def reglements():
    # Récupération de la liste des règlements
    liste_reglements = models.Reglement.query.filter_by(IDfamille=current_user.IDfamille).order_by(models.Reglement.date.desc()).all()
    
    # Paiement en ligne
    liste_factures = []
    nbre_factures_impayees = 0
    montant_factures_impayees = 0.0
    if app.config["PAIEMENT_EN_LIGNE_ACTIF"] == True :
    
        # Récupération de la liste des factures pour paiement en ligne
        liste_factures = models.Facture.query.filter_by(IDfamille=current_user.IDfamille).order_by(models.Facture.date_debut.desc()).all()
        
        # Recherche les factures impayées pour paiement en ligne
        for facture in liste_factures :
            if facture.montant_solde > 0.0 :
                nbre_factures_impayees += 1
                montant_factures_impayees += facture.montant_solde
    
    # Recherche l'historique des demandes liées aux règlements
    historique = GetHistorique(IDuser=current_user.IDuser, categorie="reglements")
    
    return render_template('reglements.html', active_page="reglements", liste_reglements=liste_reglements, \
                            liste_factures=liste_factures, nbre_factures_impayees=nbre_factures_impayees, \
                            montant_factures_impayees=montant_factures_impayees, \
                            historique=historique)

                            
@app.route('/envoyer_demande_recu')
@login_required
def envoyer_demande_recu():
    try:
        id = request.args.get("id", 0, type=int)
        info = request.args.get("info", "", type=str)
        methode_envoi = request.args.get("methode_envoi", "", type=str)
        commentaire = request.args.get("commentaire", "", type=str)
        
        # Enregistrement action
        parametres = u"id=%d#methode_envoi=%s" % (id, methode_envoi)
        if methode_envoi == "email" :
            description = u"Recevoir le reçu du règlement n°%d par Email" % id
        if methode_envoi == "courrier" :
            description = u"Recevoir le reçu du règlement n°%d par courrier" % id
        if methode_envoi == "retirer" :
            description = u"Retirer le reçu du règlement n°%d %s" % (id, app.config["RECEVOIR_DOCUMENT_RETIRER_LIEU"])

        m = models.Action(IDuser=current_user.IDuser, categorie="reglements", action="recevoir", description=description, etat="attente", commentaire=commentaire, parametres=parametres)
        db.session.add(m)
        db.session.commit()
        
        flash(u"Votre demande d'un reçu de règlement a bien été enregistrée")
        return jsonify(success=1)
    except Exception, erreur:
        return jsonify(success=0, error_msg=str(erreur))
                          
                            
                            
# ------------------------- HISTORIQUE ---------------------------------- 

@app.route('/historique')
@login_required
def historique():
    # Recherche l'historique général
    historique = GetHistorique(IDuser=current_user.IDuser, categorie=None)
    
    return render_template('historique.html', active_page="historique", historique=historique)
                            
                            
# ------------------------- PIECES ---------------------------------- 

@app.route('/pieces')
@login_required
def pieces():
    # Récupération de la liste des pièces manquantes
    liste_pieces_manquantes = models.Piece_manquante.query.filter_by(IDfamille=current_user.IDfamille).order_by(models.Piece_manquante.nom).all()

    # Récupération de la liste des types de pièces
    liste_types_pieces = models.Type_piece.query.order_by(models.Type_piece.nom).all()
    
    return render_template('pieces.html', active_page="pieces", \
                            liste_pieces_manquantes=liste_pieces_manquantes,\
                            liste_types_pieces=liste_types_pieces)


# ------------------------- COTISATIONS ---------------------------------- 

@app.route('/cotisations')
@login_required
def cotisations():
    # Récupération de la liste des cotisations manquantes
    liste_cotisations_manquantes = models.Cotisation_manquante.query.filter_by(IDfamille=current_user.IDfamille).order_by(models.Cotisation_manquante.nom).all()
    
    return render_template('cotisations.html', active_page="cotisations", \
                            liste_cotisations_manquantes=liste_cotisations_manquantes)
    
                            
@app.route('/supprimer_demande')
@login_required
def supprimer_demande():
    try:
        IDaction = request.args.get("idaction", 0, type=int)

        # Suppression de l'action dans la db
        action = models.Action.query.filter_by(IDaction=IDaction).first()
        action.etat = "suppression"
        db.session.commit()
        
        flash(u"Votre suppression a bien été enregistrée")
        return jsonify(success=1)
    except Exception, erreur:
        return jsonify(success=0, error_msg=str(erreur))

        

        
# ------------------------- RESERVATIONS ---------------------------------- 
 
@app.route('/reservations')
@login_required
def reservations():
    
    # Récupération des individus
    liste_individus_temp = models.Individu.query.filter_by(IDfamille=current_user.IDfamille).order_by(models.Individu.prenom).all()
    
    liste_individus = []
    for individu in liste_individus_temp :
        if len(individu.inscriptions) > 0 :
            # Attribution d'une couleur
            index_couleur = random.randint(0, len(COULEURS)-1)
            individu.index_couleur = index_couleur
            individu.couleur = COULEURS[index_couleur]
            liste_individus.append(individu)
    
    # Recherche l'historique des demandes liées aux réservations
    historique = GetHistorique(IDuser=current_user.IDuser, categorie="reservations")
    
    return render_template('reservations.html', active_page="reservations", \
                            liste_individus = liste_individus, \
                            historique = historique)
    

def Get_dict_planning(IDindividu=None, IDperiode=None, index_couleur=0):
    # Couleur
    couleur = COULEURS[index_couleur]
    
    # Période
    periode = models.Periode.query.filter_by(IDperiode=IDperiode).first()

    # Inscription
    inscription = models.Inscription.query.filter_by(IDindividu=IDindividu, IDactivite=periode.IDactivite).first() # .order_by(models.Activite.nom)
    
    # Unités
    liste_unites = models.Unite.query.filter_by(IDactivite=periode.IDactivite).order_by(models.Unite.ordre).all()
    
    # Ouvertures
    liste_ouvertures = models.Ouverture.query.filter(models.Ouverture.IDgroupe == inscription.IDgroupe, models.Ouverture.date >= periode.date_debut, models.Ouverture.date <= periode.date_fin).all()
    
    # Dates
    liste_dates = []
    dict_ouvertures = {}
    for ouverture in liste_ouvertures :
        
        # Mémorisation de la date
        if ouverture.date not in liste_dates :
            liste_dates.append(ouverture.date)
        
        # Mémorisation de l'ouverture des unités
        if not dict_ouvertures.has_key(ouverture.date) :
            dict_ouvertures[ouverture.date] = []
        dict_ouvertures[ouverture.date].append(ouverture.IDunite)
        
    liste_dates.sort() 
    
    # Réservations
    dict_reservations = {}
    action = models.Action.query.filter_by(categorie="reservations", IDuser=current_user.IDuser, IDperiode=periode.IDperiode, etat="attente").order_by(models.Action.horodatage.desc()).first()
    if action != None :
        liste_reservations = models.Reservation.query.filter_by(IDaction=action.IDaction).all()
        for reservation in liste_reservations :
            if not dict_reservations.has_key(reservation.date) :
                dict_reservations[reservation.date] = {}
            dict_reservations[reservation.date][reservation.IDunite] = 1

    # Consommations
    liste_consommations = models.Consommation.query.filter_by(IDinscription=inscription.IDinscription).all()
    dict_consommations = {}
    for consommation in liste_consommations :
        if not dict_consommations.has_key(consommation.date) :
            dict_consommations[consommation.date] = {}
        dict_consommations[consommation.date][consommation.IDunite] = consommation.etat
        
    # Mémorise toutes les données du planning
    dict_planning = {
        "periode" : periode,
        "inscription" : inscription,
        "liste_unites" : liste_unites,
        "liste_dates" : liste_dates,
        "dict_ouvertures" : dict_ouvertures,
        "dict_consommations" : dict_consommations,
        "dict_reservations" : dict_reservations,
        "couleur" : couleur,
        }
        
    return dict_planning
    
@app.route('/planning/<int:IDindividu>/<int:IDperiode>/<int:index_couleur>')
@login_required
def planning(IDindividu=None, IDperiode=None, index_couleur=0):
    dict_planning = Get_dict_planning(IDindividu, IDperiode, index_couleur)
    return render_template('planning.html', active_page="reservations", \
                            dict_planning = dict_planning)


@app.route('/imprimer_reservations/<int:IDindividu>/<int:IDperiode>')
@login_required
def imprimer_reservations(IDindividu=None, IDperiode=None):
    dict_planning = Get_dict_planning(IDindividu, IDperiode)
    return render_template('imprimer_reservations.html', dict_planning=dict_planning)
    

    
              
@app.route('/envoyer_reservations')
@login_required
def envoyer_reservations():
    try:
        # Récupération de la liste des cases cochées
        resultats = request.args.get("resultats", "", type=str)
        IDinscription = request.args.get("IDinscription", None, type=int)
        IDperiode = request.args.get("IDperiode", None, type=int)
        commentaire = request.args.get("commentaire", None, type=str)
        
        # Traitement des consommations
        liste_reservations = []
        liste_dates_uniques = []
        for valeur in resultats.split(",") :
            date = utils.CallFonction("DateEngEnDD", valeur.split("#")[0])
            IDunite = int(valeur.split("#")[1])
            liste_reservations.append((date, IDunite))
            
            if date not in liste_dates_uniques :
                liste_dates_uniques.append(date)
        
        # Enregistrement de l'action
        action = models.Action(IDuser=current_user.IDuser, categorie="reservations", action="envoyer", description=u"Réservation de %d dates" % len(liste_dates_uniques), etat="attente", IDperiode=IDperiode, commentaire=commentaire, parametres=None)
        db.session.add(action)
        db.session.flush()
        
        # Enregistrement des réservations
        for date, IDunite in liste_reservations :
            reservation = models.Reservation(date=date, IDinscription=IDinscription, IDunite=IDunite, IDaction=action.IDaction)
            db.session.add(reservation)

        db.session.commit()
        
        flash(u"Votre demande de réservations a bien été enregistrée")
        return jsonify(success=1)
    except Exception, erreur:
        return jsonify(success=0, error_msg=str(erreur))

        
# ------------------------- INSCRIPTIONS ---------------------------------- 

@app.route('/inscriptions')
@login_required
def inscriptions():
    
    # Récupération des individus
    liste_individus_temp = models.Individu.query.filter_by(IDfamille=current_user.IDfamille).order_by(models.Individu.prenom).all()
    
    liste_individus = []
    for individu in liste_individus_temp :
        if len(individu.inscriptions) > 0 :
            # Attribution d'une couleur
            index_couleur = random.randint(0, len(COULEURS)-1)
            individu.index_couleur = index_couleur
            individu.couleur = COULEURS[index_couleur]
            liste_individus.append(individu)
    
    # Liste des activités
    liste_activites = models.Activite.query.filter_by().order_by(models.Activite.nom).all()
    liste_groupes = models.Groupe.query.filter_by().order_by(models.Groupe.ordre).all()
    dict_groupes = {}
    for groupe in liste_groupes :
        if not dict_groupes.has_key(groupe.IDactivite) :
            dict_groupes[groupe.IDactivite] = []
        dict_groupes[groupe.IDactivite].append(groupe)
    
    # Recherche l'historique des demandes liées aux réservations
    historique = GetHistorique(IDuser=current_user.IDuser, categorie="inscriptions")
    
    return render_template('inscriptions.html', active_page="inscriptions", \
                            liste_individus = liste_individus, \
                            liste_activites = liste_activites, \
                            dict_groupes = dict_groupes, \
                            historique = historique)

                            
@app.route('/envoyer_demande_inscription')
@login_required
def envoyer_demande_inscription():
    try:
        IDindividu = request.args.get("idindividu", 0, type=int)
        activite = request.args.get("activite", "", type=str)
        IDactivite = int(activite.split("-")[0])
        IDgroupe = int(activite.split("-")[1])
        commentaire = request.args.get("commentaire", "", type=str)
        
        # Vérifie que l'individu n'est pas déjà inscrit
        inscription = models.Inscription.query.filter_by(IDindividu=IDindividu, IDactivite=IDactivite).first()
        if inscription != None :
            return jsonify(success=0, error_msg=u"%s est déjà inscrit(e) à l'activité sélectionnée !" % inscription.individu.prenom)
                    
        # Enregistrement
        individu = models.Individu.query.filter_by(IDindividu=IDindividu).first()
        activite = models.Activite.query.filter_by(IDactivite=IDactivite).first()
        description = u"Inscrire %s à l'activité %s" % (individu.prenom, activite.nom)
        parametres = u"IDactivite=%d#IDgroupe=%d" % (IDactivite, IDgroupe)

        m = models.Action(IDuser=current_user.IDuser, categorie="inscriptions", action="inscrire", description=description, etat="attente", commentaire=commentaire, parametres=parametres)
        db.session.add(m)
        db.session.commit()
        
        flash(u"Votre demande d'inscription à une activité a bien été enregistrée")
        return jsonify(success=1)
    except Exception, erreur:
        return jsonify(success=0, error_msg=str(erreur))

        
# ------------------------- CONTACT ---------------------------------- 

@app.route('/contact')
@login_required
def contact():    
    return render_template('contact.html', active_page="contact")
    
        
# ------------------------- MENTIONS ---------------------------------- 

@app.route('/mentions')
@login_required
def mentions():    
    return render_template('mentions.html', active_page="mentions")
        
      
# ------------------------- AIDE ---------------------------------- 

@app.route('/aide')
@login_required
def aide():    
    return render_template('aide.html', active_page="aide")




    
def GetHistorique(IDuser=None, categorie=None):
    """ Historique : Récupération de la liste des dernières actions liées à une catégorie """
    """ Si categorie == None > Toutes les catégories sont affichées """
    if categorie == None :
        liste_actions = models.Action.query.filter_by(IDuser=IDuser).order_by(models.Action.horodatage.desc()).all()
    else :
        liste_actions = models.Action.query.filter_by(IDuser=IDuser, categorie=categorie).order_by(models.Action.horodatage.desc()).all()
    liste_dates_actions = []
    dict_actions = {}
    for action in liste_actions :
        horodatage = utils.CallFonction("DateDDEnFr", action.horodatage)
        if horodatage not in liste_dates_actions :
            liste_dates_actions.append(horodatage)
        if not dict_actions.has_key(horodatage) :
            dict_actions[horodatage] = []
        dict_actions[horodatage].append(action)
    
    return {"liste_dates" : liste_dates_actions, "dict_actions" : dict_actions}
    
