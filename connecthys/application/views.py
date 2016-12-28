#!/usr/bin/env python
# -*- coding: utf-8 -*-
#--------------------------------------------------------------
# Application :    Connecthys, le portail internet de Noethys
# Site internet :  www.noethys.com
# Auteur:          Ivan LUCAS
# Copyright:       (c) 2010-16 Ivan LUCAS
# Licence:         Licence GNU GPL
#--------------------------------------------------------------

import random, datetime, traceback
from flask import Flask, render_template, session, request, flash, url_for, redirect, abort, g, jsonify, json, Response, send_from_directory
from flask_login import LoginManager, login_required, current_user, login_user, logout_user
from application import app, login_manager, db
from application import models, forms, utils, updater, exemples
from sqlalchemy import func


LISTE_PAGES = [
    {"type" : "label", "label" : u"MENU"}, 
        {"type" : "page", "page" : "accueil", "raccourci" : True}, 
    {"type" : "label", "label" : u"VOTRE DOSSIER"}, 
        {"type" : "page", "page" : "inscriptions", "raccourci" : True, "affichage" : "ACTIVITES_AFFICHER"}, 
        {"type" : "page", "page" : "reservations", "raccourci" : True, "affichage" : "RESERVATIONS_AFFICHER"}, 
        {"type" : "page", "page" : "factures", "raccourci" : True, "affichage" : "FACTURES_AFFICHER"}, 
        {"type" : "page", "page" : "reglements", "raccourci" : True, "affichage" : "REGLEMENTS_AFFICHER"}, 
        {"type" : "page", "page" : "pieces", "raccourci" : True, "affichage" : "PIECES_AFFICHER"}, 
        {"type" : "page", "page" : "cotisations", "raccourci" : True, "affichage" : "COTISATIONS_AFFICHER"}, 
        {"type" : "page", "page" : "historique", "raccourci" : True, "affichage" : "HISTORIQUE_AFFICHER"},
    {"type" : "label", "label" : u"INFOS"},     
        {"type" : "page", "page" : "contact", "raccourci" : True, "affichage" : "CONTACT_AFFICHER"}, 
        {"type" : "page", "page" : "mentions", "raccourci" : False, "affichage" : "MENTIONS_AFFICHER"},
        {"type" : "page", "page" : "aide", "raccourci" : False, "affichage" : "AIDE_AFFICHER"},
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


@app.route('/robots.txt')
def static_from_root():
    return send_from_directory(app.static_folder, request.path[1:])
    
    
@app.route('/update/<int:secret>/<int:version_noethys>/<int:mode>')
def update(secret=0, version_noethys=0, mode=0):
    # Codage et vérification de la clé de sécurité
    secret_key = str(datetime.datetime.now().strftime("%Y%m%d"))
    for caract in app.config['SECRET_KEY'] :
        if caract in "0123456789" :
            secret_key += caract
    secret_key = int(secret_key) 
    if secret_key != secret :
        dict_resultat = {"resultat" : "erreur", "erreur" : u"Cle de securite erronee."}
        app.logger.debug("Demande update: secretkey=%s - Mauvaise cle de securite !" % secret_key)
        return Response(json.dumps(dict_resultat), status=200, mimetype='application/json', content_type='application/json; charset=utf-8')
    
    # Recherche le mode
    if mode == 0 :
        mode = "local"
    elif mode == 1 :
        mode = "cgi"
    elif mode == 2 :
        mode = "wsgi"
    else :
        dict_resultat = {"resultat" : "erreur", "erreur" : u"Mode inconnu"}
        app.logger.debug("Demande update: secretkey=%s - Mode inconnu : %s" % (secret_key, mode))
        return Response(json.dumps(dict_resultat), status=200, mimetype='application/json', content_type='application/json; charset=utf-8')
    
    # Décode le numéro de version de Noethys
    version_noethys = updater.GetVersionFromInt(version_noethys)
    app.logger.debug("Demande update: secretkey=%s - Version Noethys=%s" % (secret_key, version_noethys))
    resultat = updater.Recherche_update(version_noethys, mode, app)
    
    dict_resultat = {"resultat" : resultat}
    return Response(json.dumps(dict_resultat), status=200, mimetype='application/json', content_type='application/json; charset=utf-8')
    

@app.route('/upgrade/<int:secret>')
def upgrade(secret=0):
    # Codage et vérification de la clé de sécurité
    secret_key = str(datetime.datetime.now().strftime("%Y%m%d"))
    for caract in app.config['SECRET_KEY'] :
        if caract in "0123456789" :
            secret_key += caract
    secret_key = int(secret_key) 
    
    if secret_key != secret :
        dict_resultat = {"resultat" : "erreur", "erreur" : u"Clé de sécurité erronée."}
        
    else :
        try :
            models.UpgradeDB()
            dict_resultat = {"resultat" : "ok"}
        except Exception, err:
            dict_resultat = {"resultat" : "erreur", "erreur" : str(err), "trace" : traceback.format_exc()}
        
        if dict_resultat["resultat"] != "ok" :
            app.logger.error("Erreur dans l'upgrade : %s" % traceback.format_exc())
    
    reponse = Response(json.dumps(dict_resultat), status=200, mimetype='application/json', content_type='application/json; charset=utf-8')
    app.logger.debug("Demande upgrade: secretkey(%s)", secret_key)
    return reponse


@app.route('/get_version')
def get_version():
    # Renvoie le numéro de la version de l'application
    version = app.config["VERSION_APPLICATION"]
    dict_resultat = {"version_str" : version, "version_tuple" : updater.GetVersionTuple(version)}
    reponse = Response(json.dumps(dict_resultat), status=200, mimetype='application/json', content_type='application/json; charset=utf-8')
    app.logger.debug("Demande version: version(%s)", dict_resultat)
    return reponse

    
#@login_manager.user_loader
#def load_user(id):
#    return models.User.query.get(int(id))
    
@login_manager.user_loader
def load_user(session_token):
    if session_token == "None" : return None
    return models.User.query.filter_by(session_token=session_token).first()
    
    
@app.before_request
def before_request():
    # Mémorise l'utilisateur en cours
    g.user = current_user
    g.liste_pages = LISTE_PAGES
    g.dict_pages = DICT_PAGES
    g.date_jour = datetime.date.today()
    
    
@app.after_request
def add_header(response):
    response.cache_control.private = True
    response.cache_control.public = False
    #response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    #response.headers['Pragma'] = 'no-cache'
    #response.headers['Expires'] = '-1'  
    return response
    
    
@app.route('/')
def index():
    return redirect(url_for('accueil'))
    

#@app.route('/exemples')
#def exemples():
#    db.drop_all()
#    db.create_all()
#    exemples.Creation_donnees_fictives()
#    return u"Base de donnees créée et données fictives ajoutées."

@app.route('/syncup/<int:secret>')
def syncup(secret=0):
    import importation
    resultat = importation.Importation(secret=secret)
    app.logger.debug("Syncho depuis Noethys: secret(%s)", secret)
    return str(resultat)
    
@app.route('/syncdown/<int:secret>/<int:last>')
def syncdown(secret=0, last=0):
    import exportation
    resultat = exportation.Exportation(secret=secret, last=last)
    app.logger.debug("Recuperation des demandes: secret(%s) - last(%s)", secret, last)
    return resultat

@app.errorhandler(500)
def internal_error(exception):
    trace = traceback.format_exc()
    return("<pre>" + trace + "</pre>"), 500
    

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
        dict_parametres = models.GetDictParametres()
        return render_template('login.html', form=form, dict_parametres=dict_parametres)
    
    # Validation du form de login avec Flask-WTF
    if form.validate_on_submit():
    
        # Recherche l'identifiant
        registered_user = models.User.query.filter_by(identifiant=form.identifiant.data).first()
        
        # Codes d'accès corrects
        if registered_user is not None:
            app.logger.debug("Connexion de l'utilisateur %s", form.identifiant.data)
            
            # Vérifie que le compte internet est actif
            if registered_user.is_active() == False :
                app.logger.debug("Tentative de connexion a un compte desactive : Identifiant =", form.identifiant.data)
                flash(u"Ce compte a été désactivé" , 'error')
                return redirect(url_for('login'))
            
            # Vérification du mot de passe
            if registered_user.check_password(form.password.data) == False :
                app.logger.debug("Mot de passe %s incorrect pour %s", form.password.data, form.identifiant.data)
                registered_user = None
                flash(u"Mot de passe incorrect" , 'error')
                return redirect(url_for('login'))

            # Mémorisation du remember_me
            #remember = form.remember.data
            
            # Mémorisation du user
            login_user(registered_user, remember=False)
            texte_bienvenue = models.GetParametre(nom="ACCUEIL_BIENVENUE")
            flash(texte_bienvenue)
            app.logger.debug("Connexion reussie de %s", form.identifiant.data)
            
            return redirect(url_for('accueil'))
            #return redirect(request.args.get('next') or url_for('accueil'))

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
    # Récupération des éléments manquants
    liste_pieces_manquantes = models.Piece_manquante.query.filter_by(IDfamille=current_user.IDfamille).order_by(models.Piece_manquante.nom).all()
    liste_cotisations_manquantes = models.Cotisation_manquante.query.filter_by(IDfamille=current_user.IDfamille).order_by(models.Cotisation_manquante.nom).all()
    
    # Récupération des messages
    liste_messages_temp = models.Message.query.order_by(models.Message.texte).all()
    liste_messages = []
    for message in liste_messages_temp :
        if message.Is_actif_today() :
            liste_messages.append(message)
            
    dict_parametres = models.GetDictParametres()
    app.logger.debug("Page ACCUEIL (%s): famille id(%s) %s", current_user.identifiant, current_user.IDfamille, current_user.nom )
    return render_template('accueil.html', active_page="accueil",\
                            liste_pieces_manquantes=liste_pieces_manquantes, \
                            liste_cotisations_manquantes=liste_cotisations_manquantes, \
                            liste_messages=liste_messages, \
                            dict_parametres=dict_parametres)

    
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
    historique = GetHistorique(IDfamille=current_user.IDfamille, categorie="factures")
    
    dict_parametres = models.GetDictParametres()
    app.logger.debug("Page FACTURES (%s): famille id(%s)", current_user.identifiant, current_user.IDfamille)
    return render_template('factures.html', active_page="factures", liste_factures=liste_factures, \
                            nbre_factures_impayees=nbre_factures_impayees, \
                            montant_factures_impayees=montant_factures_impayees, \
                            historique=historique, dict_parametres=dict_parametres)

                            
@app.route('/envoyer_demande_facture')
@login_required
def envoyer_demande_facture():
    try:
        id = request.args.get("id", 0, type=int)
        numfacture = request.args.get("info", "", type=str)
        methode_envoi = request.args.get("methode_envoi", "", type=str)
        commentaire = request.args.get("commentaire", "", type=unicode)
        
        # Enregistrement action
        parametres = u"IDfacture=%d#methode_envoi=%s" % (id, methode_envoi)
        if methode_envoi == "email" :
            description = u"Recevoir la facture n°%s par Email" % numfacture
        if methode_envoi == "courrier" :
            description = u"Recevoir la facture n°%s par courrier" % numfacture
        if methode_envoi == "retirer" :
            texte_lieu = models.GetParametre(nom="RECEVOIR_DOCUMENT_RETIRER_LIEU")
            description = u"Retirer la facture n°%s %s" % (numfacture, texte_lieu)

        m = models.Action(IDfamille=current_user.IDfamille, categorie="factures", action="recevoir", description=description, etat="attente", commentaire=commentaire, parametres=parametres)
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
    if models.GetParametre(nom="PAIEMENT_EN_LIGNE_ACTIF") == "True" :
    
        # Récupération de la liste des factures pour paiement en ligne
        liste_factures = models.Facture.query.filter_by(IDfamille=current_user.IDfamille).order_by(models.Facture.date_debut.desc()).all()
        
        # Recherche les factures impayées pour paiement en ligne
        for facture in liste_factures :
            if facture.montant_solde > 0.0 :
                nbre_factures_impayees += 1
                montant_factures_impayees += facture.montant_solde
    
    # Recherche l'historique des demandes liées aux règlements
    historique = GetHistorique(IDfamille=current_user.IDfamille, categorie="reglements")
    dict_parametres = models.GetDictParametres()
    
    app.logger.debug("Page REGLEMENTS (%s): famille id(%s)", current_user.identifiant, current_user.IDfamille)
    return render_template('reglements.html', active_page="reglements", liste_reglements=liste_reglements, \
                            liste_factures=liste_factures, nbre_factures_impayees=nbre_factures_impayees, \
                            montant_factures_impayees=montant_factures_impayees, \
                            historique=historique, dict_parametres=dict_parametres)

                            
@app.route('/envoyer_demande_recu')
@login_required
def envoyer_demande_recu():
    try:
        id = request.args.get("id", 0, type=int)
        info = request.args.get("info", "", type=str)
        methode_envoi = request.args.get("methode_envoi", "", type=str)
        commentaire = request.args.get("commentaire", "", type=unicode)
        
        # Enregistrement action
        parametres = u"IDreglement=%d#methode_envoi=%s" % (id, methode_envoi)
        if methode_envoi == "email" :
            description = u"Recevoir le reçu du règlement n°%d par Email" % id
        if methode_envoi == "courrier" :
            description = u"Recevoir le reçu du règlement n°%d par courrier" % id
        if methode_envoi == "retirer" :
            texte_lieu = models.GetParametre(nom="RECEVOIR_DOCUMENT_RETIRER_LIEU")
            description = u"Retirer le reçu du règlement n°%d %s" % (id, texte_lieu)

        m = models.Action(IDfamille=current_user.IDfamille, categorie="reglements", action="recevoir", description=description, etat="attente", commentaire=commentaire, parametres=parametres)
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
    historique = GetHistorique(IDfamille=current_user.IDfamille, categorie=None)
    dict_parametres = models.GetDictParametres()
    app.logger.debug("Page HISTORIQUE (%s): famille id(%s)", current_user.identifiant, current_user.IDfamille)
    return render_template('historique.html', active_page="historique", historique=historique, dict_parametres=dict_parametres)
                            
                            
# ------------------------- PIECES ---------------------------------- 

@app.route('/pieces')
@login_required
def pieces():
    # Récupération de la liste des pièces manquantes
    liste_pieces_manquantes = models.Piece_manquante.query.filter_by(IDfamille=current_user.IDfamille).order_by(models.Piece_manquante.nom).all()

    # Récupération de la liste des types de pièces
    liste_types_pieces = models.Type_piece.query.order_by(models.Type_piece.nom).all()
    dict_parametres = models.GetDictParametres()
    app.logger.debug("Page PIECES (%s): famille id(%s) liste_pieces_manquantes: %s", current_user.identifiant, current_user.IDfamille, liste_pieces_manquantes)
    return render_template('pieces.html', active_page="pieces", \
                            liste_pieces_manquantes=liste_pieces_manquantes,\
                            liste_types_pieces=liste_types_pieces, dict_parametres=dict_parametres)


# ------------------------- COTISATIONS ---------------------------------- 

@app.route('/cotisations')
@login_required
def cotisations():
    # Récupération de la liste des cotisations manquantes
    liste_cotisations_manquantes = models.Cotisation_manquante.query.filter_by(IDfamille=current_user.IDfamille).order_by(models.Cotisation_manquante.nom).all()
    dict_parametres = models.GetDictParametres()
    app.logger.debug("Page COTISATIONS (%s): famille id(%s) - liste_cotisations_manquante: %s", current_user.identifiant, current_user.IDfamille, liste_cotisations_manquantes)
    return render_template('cotisations.html', active_page="cotisations", \
                            liste_cotisations_manquantes=liste_cotisations_manquantes, dict_parametres=dict_parametres)
    
                            
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
        app.logger.debug("SUPPRESSION DEMANDE (%s): famille id(%s) - demande(%s)", current_user.identifiant, current_user.IDfamille, IDaction)
        return jsonify(success=1)
    except Exception, erreur:
        app.logger.debug("[ERREUR] SUPPRESSION DEMANDE (%s): famille id(%s) - demande(%s)", current_user.identifiant, current_user.IDfamille, IDaction)
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
    historique = GetHistorique(IDfamille=current_user.IDfamille, categorie="reservations")
    dict_parametres = models.GetDictParametres()
    app.logger.debug("Page RESERVATIONS (%s): famille id(%s) %s - liste_individus: %s", current_user.identifiant, current_user.IDfamille, current_user.nom, liste_individus)
    return render_template('reservations.html', active_page="reservations", \
                            liste_individus = liste_individus, \
                            historique = historique, dict_parametres=dict_parametres)
    

def Get_dict_planning(IDindividu=None, IDperiode=None, index_couleur=0, coches=None):
    # Couleur
    if index_couleur > len(COULEURS)-1 :
        return None
    couleur = COULEURS[index_couleur]
    
    # Période
    periode = models.Periode.query.filter_by(IDperiode=IDperiode).first()
    if periode == None or not periode.Is_active_today() :
        app.logger.warning(u"IDfamille %d : Tentative d'accéder à la période %s dans les réservations." % (current_user.IDfamille, IDperiode))
        flash(u"Vous n'êtes pas autorisé à accéder à la période demandée !")
        return None
    
    # Inscription
    inscription = models.Inscription.query.filter_by(IDfamille=current_user.IDfamille, IDindividu=IDindividu, IDactivite=periode.IDactivite).first() # .order_by(models.Activite.nom)
    if inscription == None :
        app.logger.warning(u"IDfamille %d : Tentative d'accéder à l'individu %s dans les réservations." % (current_user.IDfamille, IDindividu))
        flash(u"Vous n'êtes pas autorisé à accéder au planning de l'individu demandé !")
        return None
    
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
    actions = models.Action.query.filter_by(categorie="reservations", IDfamille=current_user.IDfamille, IDindividu=inscription.IDindividu, IDperiode=periode.IDperiode, etat="attente").order_by(models.Action.horodatage).all()
    if actions != None :
        dict_reservations = {}
        for action in actions :
            liste_reservations = models.Reservation.query.filter_by(IDaction=action.IDaction).all()
            for reservation in liste_reservations :
                if not dict_reservations.has_key(reservation.date) :
                    dict_reservations[reservation.date] = {}
                dict_reservations[reservation.date][reservation.IDunite] = reservation.etat
    else :
        dict_reservations = None
    
    # Pour version imprimable
    if coches != None :
        liste_coches = []
        if len(coches) > 0 :
            for coche in coches.split(",") :
                date, IDunite = utils.DateEngEnDD(coche.split("A")[0]), int(coche.split("A")[1])
                liste_coches.append((date, IDunite))
                
                # Coche les nouvelles réservations
                if dict_reservations != None :
                    if not dict_reservations.has_key(date) :
                        dict_reservations[date] = {}
                    dict_reservations[date][IDunite] = 1
            
            # Décoche les anciennes réservations
            for date, dict_unites_temp in dict_reservations.iteritems() :
                for IDunite, etat in dict_unites_temp.iteritems() :
                    if (date, IDunite) not in liste_coches :
                        dict_reservations[date][IDunite] = 0

                    
    # Génération de la liste initiale des réservations actives
    # liste_reservations_initiale = []
    # for date, liste_unites_temp in dict_reservations.iteritems() :
        # for IDunite, etat in liste_unites_temp.iteritems() :
            # if etat == 1 :
                # liste_reservations_initiale.append("%s#%d" % (date, IDunite))
    
            
    
    
    
    # Consommations
    liste_consommations = models.Consommation.query.filter_by(IDinscription=inscription.IDinscription).all()
    dict_consommations = {}
    for consommation in liste_consommations :
        if not dict_consommations.has_key(consommation.date) :
            dict_consommations[consommation.date] = {}
        dict_consommations[consommation.date][consommation.IDunite] = consommation.etat
    
    # Attribution des consommations à chaque unité de réservation
    liste_unites_temp = []
    for unite in liste_unites :
        liste_unites_principales = unite.Get_unites_principales()
        liste_unites_temp.append( (len(liste_unites_principales), liste_unites_principales, unite) )
    liste_unites_temp.sort(reverse=True)
    
    dict_conso_par_unite_resa = {}
    
    for date in liste_dates :
    
        liste_unites_conso_utilisees = []
        
        for nbre_unites_principales, liste_unites_principales, unite in liste_unites_temp :
            
            valide = True
            for IDunite_conso in liste_unites_principales :
                if IDunite_conso in liste_unites_conso_utilisees :
                    valide = False
            
            if valide :
                
                liste_etats = []
                for IDunite_conso in liste_unites_principales :
                    if dict_consommations.has_key(date) :
                        if dict_consommations[date].has_key(IDunite_conso) :
                            liste_etats.append(dict_consommations[date][IDunite_conso])
                    
                if len(liste_etats) == nbre_unites_principales :
                    if not dict_conso_par_unite_resa.has_key(date) :
                        dict_conso_par_unite_resa[date] = {}
                    
                    if "attente" in liste_etats :
                        dict_conso_par_unite_resa[date][unite] = "attente"
                    elif "present" in liste_etats :
                        dict_conso_par_unite_resa[date][unite] = "present"
                    elif "absenti" in liste_etats :
                        dict_conso_par_unite_resa[date][unite] = "absenti"
                    elif "absentj" in liste_etats :
                        dict_conso_par_unite_resa[date][unite] = "absentj"
                    else :
                        dict_conso_par_unite_resa[date][unite] = "reservation"
                    
                    for IDunite_conso in liste_unites_principales :
                        liste_unites_conso_utilisees.append(IDunite_conso)                    
                    
    # Recherche les réservations actives
    liste_reservations_initiale = []
    for date in liste_dates :
        for unite in liste_unites :
            dict_planning_temp = {"dict_reservations" : dict_reservations, "dict_conso_par_unite_resa" : dict_conso_par_unite_resa}
            
            # Vérifie si la case est cochée
            coche = utils.GetEtatCocheCase(unite, date, dict_planning_temp)
            
            # Vérifie si c'est une unité modifiable
            etat = utils.GetEtatFondCase(unite, date, dict_planning_temp)
            if etat != None and etat not in ("reservation", "attente") :
                coche = False
            
            # Mémorisation dans la liste des réservations initiales
            if coche :
                unite_txt = "%s#%d" % (date, unite.IDunite)
                if unite_txt not in liste_reservations_initiale :
                    liste_reservations_initiale.append(unite_txt)
                
    liste_reservations_initiale = ";".join(liste_reservations_initiale)
    
    # Mémorise toutes les données du planning
    dict_planning = {
        "periode" : periode,
        "inscription" : inscription,
        "liste_unites" : liste_unites,
        "liste_dates" : liste_dates,
        "dict_ouvertures" : dict_ouvertures,
        "dict_consommations" : dict_consommations,
        "dict_conso_par_unite_resa" : dict_conso_par_unite_resa,
        "dict_reservations" : dict_reservations,
        "couleur" : couleur,
        "liste_reservations_initiale" : liste_reservations_initiale,
        }
    
    app.logger.debug("Page PLANNING (%s): famille id(%s) Individu id(%s) pour la periode id(%s)\ndict_planning: %s", current_user.identifiant, current_user.IDfamille, IDindividu, IDperiode, dict_planning)
    return dict_planning
    
# @app.route('/planning/<int:IDindividu>/<int:IDperiode>/<int:index_couleur>')
# @login_required
# def planning(IDindividu=None, IDperiode=None, index_couleur=0):
    # dict_planning = Get_dict_planning(IDindividu, IDperiode, index_couleur)
    # return render_template('planning.html', active_page="reservations", \
                            # dict_planning = dict_planning)

@app.route('/planning')
@login_required
def planning():
    IDindividu = request.args.get("IDindividu", None, type=int)
    IDperiode = request.args.get("IDperiode", None, type=int)
    index_couleur = request.args.get("index_couleur", None, type=int)
    
    dict_planning = Get_dict_planning(IDindividu, IDperiode, index_couleur)
    if dict_planning == None :
        return redirect(url_for('reservations'))
    
    dict_parametres = models.GetDictParametres()
    return render_template('planning.html', active_page="reservations", \
                            dict_planning = dict_planning, dict_parametres=dict_parametres)

    
@app.route('/imprimer_reservations')
@login_required
def imprimer_reservations():
    IDindividu = request.args.get("IDindividu", None, type=int)
    IDperiode = request.args.get("IDperiode", None, type=int)
    resultats = request.args.get("resultats", "", type=str)
    
    dict_planning = Get_dict_planning(IDindividu=IDindividu, IDperiode=IDperiode, coches=resultats)
    if dict_planning == None :
        return redirect(url_for('reservations'))
    
    dict_parametres = models.GetDictParametres()
    return render_template('imprimer_reservations.html', dict_planning=dict_planning, dict_parametres=dict_parametres)
    
              
@app.route('/envoyer_reservations')
@login_required
def envoyer_reservations():
    try:
        # Récupération de la liste des cases cochées
        resultats = request.args.get("resultats", "", type=str)
        IDinscription = request.args.get("IDinscription", None, type=int)
        IDperiode = request.args.get("IDperiode", None, type=int)
        IDactivite = request.args.get("IDactivite", None, type=int)
        activite_nom = request.args.get("activite_nom", None, type=unicode)
        IDindividu = request.args.get("IDindividu", None, type=int)
        individu_prenom = request.args.get("individu_prenom", None, type=unicode)
        date_debut_periode = request.args.get("date_debut_periode", "", type=str)
        date_fin_periode = request.args.get("date_fin_periode", "", type=str)
        commentaire = request.args.get("commentaire", None, type=unicode)
        liste_reservations_initiale = request.args.get("liste_reservations_initiale", "", type=str)
        
        # Paramètres
        parametres = u"IDactivite=%d#date_debut_periode=%s#date_fin_periode=%s" % (IDactivite, date_debut_periode, date_fin_periode)
        
        liste_reservations_finale, nbre_ajouts, nbre_suppressions = GetModificationsReservations(liste_reservations_initiale, resultats)
        
        if nbre_ajouts == 0 and nbre_suppressions == 0 :
        
            # Retourne un message d'erreur si aucune modification par rapport aux réservations initiales
            return jsonify(success=0, error_msg=u"Vous n'avez effectué aucune modification dans vos réservations !")         
            
        else :
        
            # Description
            date_debut_periode_fr = utils.DateEngFr(date_debut_periode)
            date_fin_periode_fr = utils.DateEngFr(date_fin_periode)
            temp = []
            if nbre_ajouts == 1 : temp.append(u"1 ajout")
            if nbre_ajouts > 1 : temp.append(u"%d ajouts" % nbre_ajouts)
            if nbre_suppressions == 1 : temp.append(u"1 suppression")
            if nbre_suppressions > 1 : temp.append(u"%d suppressions" % nbre_suppressions)
            description = u"Réservations %s pour %s sur la période du %s au %s (%s)" % (activite_nom, individu_prenom, date_debut_periode_fr, date_fin_periode_fr, " et ".join(temp))
            
            # Enregistrement de l'action
            action = models.Action(IDfamille=current_user.IDfamille, IDindividu=IDindividu, categorie="reservations", action="envoyer", description=description, etat="attente", IDperiode=IDperiode, commentaire=commentaire, parametres=parametres)
            db.session.add(action)
            db.session.flush()
            
            # Enregistrement des réservations
            for date, IDunite, etat in liste_reservations_finale :
                reservation = models.Reservation(date=date, IDinscription=IDinscription, IDunite=IDunite, IDaction=action.IDaction, etat=etat)
                db.session.add(reservation)

            db.session.commit()
            
            flash(u"Votre demande de réservations a bien été enregistrée")
            app.logger.debug("Demande de reservations (%s): famille id(%s) Individu id(%s) pour la periode id(%s)\nliste_reservations: %s", current_user.identifiant, current_user.IDfamille, IDindividu, IDperiode ,liste_reservations_finale)
            return jsonify(success=1)
            
    except Exception, erreur:
        app.logger.debug("[ERREUR] Demande de reservations (%s): famille id(%s)", current_user.identifiant, current_user.IDfamille)
        return jsonify(success=0, error_msg=str(erreur))

        
        
        
def GetModificationsReservations(liste_reservations_initiale=[], resultats=[]):
    # Formatage de la liste des réservations initiale txt en liste
    if len(liste_reservations_initiale) > 0 :
        liste_reservations_initiale = liste_reservations_initiale.split(";")
    else :
        liste_reservations_initiale = []
    
    # Formatage de la liste des réservations txt en liste
    if len(resultats) > 0 :
        liste_reservations = resultats.split(",")
    else :
        liste_reservations = []
    
    # Recherche les ajouts
    liste_reservations_finale = []
    nbre_ajouts = 0
    for valeur in liste_reservations :
        if valeur not in liste_reservations_initiale :
            date = utils.CallFonction("DateEngEnDD", valeur.split("#")[0])
            IDunite = int(valeur.split("#")[1])
            liste_reservations_finale.append((date, IDunite, 1))
            nbre_ajouts += 1
            
    # Recherche les suppressions
    nbre_suppressions = 0
    for valeur in liste_reservations_initiale :
        if valeur not in liste_reservations :
            date = utils.CallFonction("DateEngEnDD", valeur.split("#")[0])
            IDunite = int(valeur.split("#")[1])
            liste_reservations_finale.append((date, IDunite, 0))
            nbre_suppressions += 1
    
    return liste_reservations_finale, nbre_ajouts, nbre_suppressions

    
    
        
@app.route('/detail_envoi_reservations')
@login_required
def detail_envoi_reservations():
    try:
        # Détail des réservations
        IDactivite = request.args.get("IDactivite", None, type=int)
        resultats = request.args.get("resultats", "", type=str)
        liste_reservations_initiale = request.args.get("liste_reservations_initiale", "", type=str)
        liste_reservations_finale, nbre_ajouts, nbre_suppressions = GetModificationsReservations(liste_reservations_initiale, resultats)
        
        # Liste des unités
        liste_unites = models.Unite.query.filter_by(IDactivite=IDactivite).all()
        dict_unites = {}
        for unite in liste_unites :
            dict_unites[unite.IDunite] = unite
            
        liste_lignes = []
        for date, IDunite, etat in liste_reservations_finale :
            if etat == 1 :
                ligne = u"- Ajout"
            else :
                ligne = u"- Suppression"
            ligne += u" de la réservation du %s (%s)\n" % (utils.DateEngFr(date), dict_unites[IDunite].nom)
            liste_lignes.append(ligne)
            
        if len(liste_lignes) > 0 :
            detail = "".join(liste_lignes)
        else :
            detail = u"Aucune modification demandée."        
        
        return jsonify(success=1, detail=detail)
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
    historique = GetHistorique(IDfamille=current_user.IDfamille, categorie="inscriptions")
    dict_parametres = models.GetDictParametres()
    app.logger.debug("Page INSCRIPTIONS (%s): famille id(%s) liste_individus: %s", current_user.identifiant, current_user.IDfamille, liste_individus)
    return render_template('inscriptions.html', active_page="inscriptions", \
                            liste_individus = liste_individus, \
                            liste_activites = liste_activites, \
                            dict_groupes = dict_groupes, \
                            historique = historique, dict_parametres=dict_parametres)

                            
@app.route('/envoyer_demande_inscription')
@login_required
def envoyer_demande_inscription():
    try:
        IDindividu = request.args.get("idindividu", 0, type=int)
        activite = request.args.get("activite", "", type=str)
        if activite == "" :
            return jsonify(success=0, error_msg=u"Aucune activité n'a été sélectionnée")
        IDactivite = int(activite.split("-")[0])
        IDgroupe = int(activite.split("-")[1])
        commentaire = request.args.get("commentaire", "", type=unicode)
        
        # Vérifie que l'individu n'est pas déjà inscrit
        inscription = models.Inscription.query.filter_by(IDindividu=IDindividu, IDactivite=IDactivite).first()
        if inscription != None :
            return jsonify(success=0, error_msg=u"%s est déjà inscrit(e) à l'activité sélectionnée !" % inscription.individu.prenom)
                    
        # Enregistrement
        individu = models.Individu.query.filter_by(IDindividu=IDindividu).first()
        activite = models.Activite.query.filter_by(IDactivite=IDactivite).first()
        description = u"Inscription de %s à l'activité %s" % (individu.prenom, activite.nom)
        parametres = u"IDactivite=%d#IDgroupe=%d" % (IDactivite, IDgroupe)

        m = models.Action(IDfamille=current_user.IDfamille, IDindividu=IDindividu, categorie="inscriptions", action="inscrire", description=description, etat="attente", commentaire=commentaire, parametres=parametres)
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
    dict_parametres = models.GetDictParametres()
    return render_template('contact.html', active_page="contact", dict_parametres=dict_parametres)
    
        
# ------------------------- MENTIONS ---------------------------------- 

@app.route('/mentions')
@login_required
def mentions():   
    dict_parametres = models.GetDictParametres()
    return render_template('mentions.html', active_page="mentions", dict_parametres=dict_parametres)
        
      
# ------------------------- AIDE ---------------------------------- 

@app.route('/aide')
@login_required
def aide():    
    dict_parametres = models.GetDictParametres()
    return render_template('aide.html', active_page="aide", dict_parametres=dict_parametres)

    
    
    
@app.route('/detail_demande')
@login_required
def detail_demande():
    try:
        # Détail des réservations
        IDaction = request.args.get("idaction", 0, type=int)
        liste_reservations = models.Reservation.query.filter_by(IDaction=IDaction).order_by(models.Reservation.date, models.Reservation.etat).all()
        
        liste_unites = models.Unite.query.all()
        dict_unites = {}
        for unite in liste_unites :
            dict_unites[unite.IDunite] = unite        
        
        liste_lignes = []
        for reservation in liste_reservations :
            txt_date = utils.CallFonction("DateDDEnFrComplet", reservation.date)
            if reservation.etat == 1 :
                ligne = u"- Ajout"
            else :
                ligne = u"- Suppression"
            ligne += u" de la réservation du %s (%s)\n" % (txt_date, dict_unites[reservation.IDunite].nom)
            liste_lignes.append(ligne)
        detail = "".join(liste_lignes)
                    
        return jsonify(success=1, detail=detail)
    except Exception, erreur:
        return jsonify(success=0, error_msg=str(erreur))

    
    
    
def GetHistorique(IDfamille=None, categorie=None):
    """ Historique : Récupération de la liste des dernières actions liées à une catégorie """
    """ Si categorie == None > Toutes les catégories sont affichées """
    # Récupération de la date de la dernière synchro
    m = models.Parametre.query.filter_by(nom="derniere_synchro").first()
    if m != None :
        derniere_synchro = datetime.datetime.strptime(m.parametre, "%Y%m%d%H%M%S%f")
    else :
        derniere_synchro = None
    
    # Récupération des actions
    historique_delai = int(models.GetParametre(nom="HISTORIQUE_DELAI", defaut=0))
    date_limite = datetime.datetime.now() - datetime.timedelta(days=(historique_delai+1)*30)
    if categorie == None :
        liste_actions = models.Action.query.filter(models.Action.IDfamille==IDfamille, models.Action.horodatage>=date_limite).order_by(models.Action.horodatage.desc()).all()
    else :
        liste_actions = models.Action.query.filter(models.Action.IDfamille==IDfamille, models.Action.horodatage>=date_limite, models.Action.categorie==categorie).order_by(models.Action.horodatage.desc()).all()
    liste_dates_actions = []
    dict_actions = {}
    dict_dernieres_reservations = {}
    for action in liste_actions :
        horodatage = utils.CallFonction("DateDDEnFr", action.horodatage)
        if horodatage not in liste_dates_actions :
            liste_dates_actions.append(horodatage)
        if not dict_actions.has_key(horodatage) :
            dict_actions[horodatage] = []
        dict_actions[horodatage].append(action)
        
        if action.categorie == "reservations" :
            if not dict_dernieres_reservations.has_key(action.IDperiode) or (action.horodatage > dict_dernieres_reservations[action.IDperiode].horodatage and action.etat != "suppression") :
                dict_dernieres_reservations[action.IDperiode] = action
    
    return {"liste_dates" : liste_dates_actions, "dict_actions" : dict_actions, "derniere_synchro" : derniere_synchro, "categorie" : categorie}
    