#!/usr/bin/env python
# -*- coding: utf-8 -*-
#--------------------------------------------------------------
# Application :    Connecthys, le portail internet de Noethys
# Site internet :  www.noethys.com
# Auteur:          Ivan LUCAS
# Copyright:       (c) 2010-18 Ivan LUCAS
# Licence:         Licence GNU GPL
#--------------------------------------------------------------

import random, datetime, traceback, copy, re, sys, os
from flask import Flask, render_template, session, request, flash, url_for, redirect, abort, g, jsonify, json, Response, send_from_directory
from flask_login import LoginManager, login_required, current_user, login_user, logout_user
try :
    from flask_wtf import CSRFProtect
except :
    # Pour compatibilité avec anciennes versions de flask_wtf
    from flask_wtf import CsrfProtect
from itsdangerous import URLSafeTimedSerializer
from flask_wtf.csrf import CSRFError
from application import app, login_manager, db, mail, csrf, captcha
from application import models, forms, utils, updater, exemples
from sqlalchemy import or_
from eopayment import Payment
from operator import itemgetter
import six, re
from uuid import uuid4
from cryptage import IMPORT_AES, CrypterFichier

try :
    from flask_mail import Message
except :
    app.logger.error("Impossible d'importer flask_mail")

import os.path
REP_APPLICATION = os.path.abspath(os.path.dirname(__file__))
REP_CONNECTHYS = os.path.dirname(REP_APPLICATION)


LISTE_PAGES_FAMILLES = [
    {"type" : "label", "label" : u"MENU"}, 
        {"type" : "page", "page" : "accueil_famille", "raccourci" : True},
    {"type" : "label", "label" : u"VOTRE DOSSIER"}, 
        {"type" : "page", "page" : "renseignements", "raccourci" : True, "affichage" : "RENSEIGNEMENTS_AFFICHER"}, 
        {"type" : "page", "page" : "inscriptions", "raccourci" : True, "affichage" : "ACTIVITES_AFFICHER"}, 
        {"type" : "page", "page" : "reservations", "raccourci" : True, "affichage" : "RESERVATIONS_AFFICHER"}, 
        {"type" : "page", "page" : "factures", "raccourci" : True, "affichage" : "FACTURES_AFFICHER"}, 
        {"type" : "page", "page" : "reglements", "raccourci" : True, "affichage" : "REGLEMENTS_AFFICHER"}, 
        {"type" : "page", "page" : "pieces", "raccourci" : True, "affichage" : "PIECES_AFFICHER"}, 
        {"type" : "page", "page" : "cotisations", "raccourci" : True, "affichage" : "COTISATIONS_AFFICHER"},
        {"type" : "page", "page" : "locations", "raccourci" : True, "affichage" : "LOCATIONS_AFFICHER"},
        {"type" : "page", "page" : "historique", "raccourci" : True, "affichage" : "HISTORIQUE_AFFICHER"},
    {"type" : "label", "label" : u"DIVERS"},
        {"type" : "page", "page" : "contact", "raccourci" : True, "affichage" : "CONTACT_AFFICHER"}, 
        {"type" : "page", "page" : "mentions", "raccourci" : False, "affichage" : "MENTIONS_AFFICHER"},
        {"type" : "page", "page" : "aide", "raccourci" : False, "affichage" : "AIDE_AFFICHER"},
    ]

LISTE_PAGES_ADMIN = [
    {"type" : "label", "label" : u"MENU"},
        {"type" : "page", "page" : "accueil_admin", "raccourci" : True},
    ]


DICT_PAGES = {
    # Familles
    "accueil_famille" : {"nom" : u"Accueil", "icone" : "fa-home", "description" : u" ", "couleur" : "white"},
    "renseignements" : {"nom" : u"Renseignements", "icone" : "fa-user", "description" : u"Consulter et modifier des renseignements", "couleur" : "purple"},
    "inscriptions" : {"nom" : u"Activités", "icone" : "fa-cogs", "description" : u"Consulter et demander des inscriptions", "couleur" : "green"},
    "reservations" : {"nom" : u"Réservations", "icone" : "fa-calendar", "description" : u"Consulter et demander des réservations", "couleur" : "aqua"},
    "factures" : {"nom" : u"Factures", "icone" : "fa-file-text-o", "description" : u"Consulter et payer des factures", "couleur" : "orange"},
    "reglements" : {"nom" : u"Règlements", "icone" : "fa-money", "description" : u"Consulter les règlements", "couleur" : "red"},
    "pieces" : {"nom" : u"Pièces", "icone" : "fa-files-o", "description" : u"Consulter et télécharger des pièces", "couleur" : "blue"},
    "cotisations" : {"nom" : u"Cotisations", "icone" : "fa-folder-o", "description" : u"Consulter les cotisations", "couleur" : "olive"},
    "locations" : {"nom" : u"Locations", "icone" : "fa-shopping-cart", "description" : u"Consulter et modifier des locations", "couleur" : "aqua"},
    "historique" : {"nom" : u"Historique", "icone" : "fa-clock-o", "description" : u"Consulter l'historique des demandes", "couleur" : "purple"},
    "contact" : {"nom" : u"Contact", "icone" : "fa-envelope-o", "description" : u"Contacter l'organisateur", "couleur" : "yellow"},
    "mentions" : {"nom" : u"Mentions légales", "icone" : "fa-info-circle", "description" : u"Consulter les mentions légales"},
    "aide" : {"nom" : u"Aide", "icone" : "fa-support", "description" : u"Consulter l'aide"},
    "compte" : {"nom" : u"Gestion du compte", "icone" : "fa-support", "description" : u"Gestion du compte"},

    # Administrateurs
    "accueil_admin" : {"nom" : u"Accueil", "icone" : "fa-home", "description" : u" ", "couleur" : "white"},
    }


COULEURS = ["green", "blue", "yellow", "red", "light-blue"]

CHAMPS_RENSEIGNEMENTS = ["nom", "prenom", "date_naiss", "cp_naiss", "ville_naiss", "adresse_auto", "rue_resid", "cp_resid", "ville_resid", 
                                        "tel_domicile", "tel_mobile", "mail", "profession", "employeur", "travail_tel", "travail_mail"]

DICT_RENSEIGNEMENTS = {"nom" : u"Nom", "prenom" : u"Prénom", "date_naiss" : u"Date de naissance", "cp_naiss" : u"CP de naissance", "ville_naiss" : u"Ville de naissance", "rue_resid" : u"Adresse - Rue", "cp_resid" : u"Adresse - CP", "ville_resid" : u"Adresse - Ville", 
                                        "tel_domicile" : u"Tél. Domicile", "tel_mobile" : u"Tél. Mobile", "mail" : u"Email", "profession" : u"Profession", "employeur" : u"Employeur", "travail_tel" : u"Tél. Pro.", "travail_mail" : u"Email Pro."}

ETATS_PAIEMENTS = {1: "RECEIVED", 2: "ACCEPTED", 3: "PAID", 4: "DENIED", 5: "CANCELLED", 6: "WAITING", 99: "ERROR"}



def VerifyKey(secret=0):
    # Codage et vérification de la clé de sécurité
    secret_key = str(datetime.datetime.now().strftime("%Y%m%d"))
    for caract in app.config['SECRET_KEY']:
        if caract in "0123456789":
            secret_key += caract
    secret_key = int(secret_key)
    resultat = secret_key == secret
    return resultat


@app.route('/robots.txt')
def static_from_root():
    return send_from_directory(app.static_folder, request.path[1:])
    
    
@app.route('/update/<int:secret>/<int:version_noethys>/<int:mode>')
def update(secret=0, version_noethys=0, mode=0):
    if not VerifyKey(secret):
        dict_resultat = {"resultat" : "erreur", "erreur" : u"Cle de securite erronee."}
        app.logger.debug("Demande update: secretkey=%s - Mauvaise cle de securite !", secret)
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
        app.logger.debug("Demande update: Mode inconnu : %s", mode)
        return Response(json.dumps(dict_resultat), status=200, mimetype='application/json', content_type='application/json; charset=utf-8')
    
    # Décode le numéro de version de Noethys
    version_noethys = updater.GetVersionFromInt(version_noethys)
    app.logger.debug("Demande update: Version Noethys=%s", version_noethys)
    resultat = updater.Recherche_update(version_noethys, mode, app)
    
    dict_resultat = {"resultat" : resultat}
    return Response(json.dumps(dict_resultat), status=200, mimetype='application/json', content_type='application/json; charset=utf-8')
    

@app.route('/upgrade/<int:secret>')
def upgrade(secret=0):
    app.logger.debug("Demande upgrade")
    if not VerifyKey(secret):
        dict_resultat = {"resultat": "erreur", "erreur": u"Clé de sécurité erronée."}
    else :
        try :
            models.UpgradeDB()
            dict_resultat = {"resultat" : "ok"}
        except Exception as err:
            dict_resultat = {"resultat" : "erreur", "erreur" : str(err), "trace" : traceback.format_exc()}
        
        if dict_resultat["resultat"] != "ok" :
            app.logger.error("Erreur dans l'upgrade : %s" % traceback.format_exc())
    
    reponse = Response(json.dumps(dict_resultat), status=200, mimetype='application/json', content_type='application/json; charset=utf-8')
    return reponse



@app.route('/repairdb/<int:secret>')
def repairdb(secret=0):
    app.logger.debug("Demande repairdb.")
    if not VerifyKey(secret):
        dict_resultat = {"resultat": "erreur", "erreur": u"Clé de sécurité erronée."}
    else:
        try:
            models.RepairDB()
            dict_resultat = {"resultat": "ok"}
        except Exception as err:
            dict_resultat = {"resultat": "erreur", "erreur": str(err), "trace": traceback.format_exc()}

        if dict_resultat["resultat"] != "ok":
            app.logger.error("Erreur dans le repairdb : %s" % traceback.format_exc())

    reponse = Response(json.dumps(dict_resultat), status=200, mimetype='application/json', content_type='application/json; charset=utf-8')
    return reponse


@app.route('/cleardb/<int:secret>')
def cleardb(secret=0):
    if not VerifyKey(secret):
        dict_resultat = {"resultat": "erreur", "erreur": u"Clé de sécurité erronée."}
    else:
        app.logger.debug("Effacement de la base...")
        to_db = app.config['SQLALCHEMY_DATABASE_URI']
        if "mysql" in to_db:
            db.engine.execute("SET foreign_key_checks = 0;")
        for table in reversed(db.metadata.sorted_tables):
            app.logger.debug("Effacement de la table %s", table)
            db.session.execute(table.delete())
        db.session.commit()
        if "mysql" in to_db:
            db.engine.execute("SET foreign_key_checks = 1;")
        app.logger.debug("Effacement de la base fini.")
        dict_resultat = {"resultat": "ok"}

    reponse = Response(json.dumps(dict_resultat), status=200, mimetype='application/json', content_type='application/json; charset=utf-8')
    return reponse


@app.route('/get_version')
def get_version():
    # Renvoie le numéro de la version de l'application
    version = app.config["VERSION_APPLICATION"]
    dict_resultat = {"version_str" : version, "version_tuple" : updater.GetVersionTuple(version)}
    reponse = Response(json.dumps(dict_resultat), status=200, mimetype='application/json', content_type='application/json; charset=utf-8')
    app.logger.debug("Demande version: version(%s)", dict_resultat)
    return reponse

    

@login_manager.user_loader
def load_user(session_token):
    if session_token == "None" : return None
    try :
        user = models.User.query.filter_by(session_token=session_token).first()
    except :
        user = None
    return user
    
    
@app.before_request
def before_request():
    # Vérifie si le mode maintenance est activé
    if os.path.exists("maintenance.txt"):
        abort(503)

    # Mémorise l'utilisateur en cours
    g.user = current_user

    # Mémorise des variables
    g.liste_pages_familles, g.liste_pages_admin, g.dict_pages = GetPages()
    g.date_jour = datetime.date.today()

def GetPages():
    liste_pages_familles = copy.copy(LISTE_PAGES_FAMILLES)
    liste_pages_admin = copy.copy(LISTE_PAGES_ADMIN)
    dict_pages = copy.copy(DICT_PAGES)

    try :
        liste_pages_perso = models.Page.query.order_by(models.Page.ordre).all()
    except :
        liste_pages_perso = []

    if len(liste_pages_perso) > 0 :

        # Label
        liste_pages_familles.insert(2, {"type": "label", "label": u"INFORMATIONS"})

        # Création des pages
        index = 3
        for page in liste_pages_perso :
            codePage = "page_perso%d" % page.IDpage
            liste_pages_familles.insert(index, {"type": "page", "page": codePage, "num_page" : page.IDpage, "raccourci": False, "affichage": True})
            dict_pages[codePage] = {"nom" : page.titre, "icone" : "fa-circle-o", "description" : u" ", "couleur" : page.couleur}
            index += 1

    return liste_pages_familles, liste_pages_admin, dict_pages


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
    app.logger.debug("Syncho depuis Noethys")
    return str(resultat)
    
@app.route('/syncdown/<int:secret>/<int:last>')
def syncdown(secret=0, last=0):
    import exportation
    resultat = exportation.Exportation(secret=secret, last=last)
    app.logger.debug("Recuperation des demandes: last(%s)", last)
    return resultat

@app.errorhandler(500)
def internal_error(exception):
    trace = traceback.format_exc()
    return("<pre>" + trace + "</pre>"), 500
    
@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    app.logger.debug(u"Erreur de CSRF :")
    app.logger.debug(e.description)
    return render_template('csrf_error.html'), 400

@app.errorhandler(503)
def maintenance(error):
    return render_template('maintenance.html'), 503


# ------------------------- LOGIN et LOGOUT ---------------------------------- 

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Si l'utilisateur est déjà connecté, on le renvoie vers l'accueil
    if current_user.is_authenticated :
        return redirect(url_for('accueil'))

    dict_parametres = models.GetDictParametres()

    # Génération du form de login
    # if app.config.get('RECAPTCHA_ACTIVATION') and app.config.get('RECAPTCHA_PUBLIC_KEY'):
    if app.config.get('CAPTCHA', 1) == 1:
        form = forms.LoginFormWithCaptcha()
    else:
        form = forms.LoginForm()

    # Affiche la page de login
    if request.method == 'GET':
        return render_template('login.html', form=form, dict_parametres=dict_parametres)
    
    # Validation du form de login avec Flask-WTF
    if form.validate_on_submit():

        # Vérification du captcha
        if hasattr(form, "captcha") and not captcha.validate():
            flash(u"Le code de sécurité n'a pas été correctement recopié", 'error')
            return redirect(url_for('login'))
            
        # Recherche l'identifiant
        try:
            registered_user = models.User.query.filter_by(identifiant=form.identifiant.data).first()
        except Exception as err:
            app.logger.info("Erreur dans recherche du user durant le login")
            app.logger.info(err)

            # Tentative de réparation de la DB
            if "no such column" in str(err) or "Unknown column" in str(err):
                app.logger.info("Il semble manquer une colonne : tentative de reparation de la DB")
                try:
                    models.RepairDB()
                    models.UpgradeDB()
                except:
                    pass

            flash(u"Une erreur a été rencontrée. Veuillez réessayer de vous connecter.", 'error')
            return redirect(url_for('login'))

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
                app.logger.debug("Mot de passe incorrect pour %s", form.identifiant.data)
                registered_user = None
                flash(u"Mot de passe incorrect" , 'error')
                return redirect(url_for('login'))

            # Mémorisation du remember_me
            #remember = form.remember.data
            
            # Mémorisation du user
            login_user(registered_user, remember=False)
            texte_bienvenue = models.GetParametre(nom="ACCUEIL_BIENVENUE", dict_parametres=dict_parametres)
            flash(texte_bienvenue)
            app.logger.debug("Connexion reussie de %s", form.identifiant.data)

            # Force la modification du mot de passe
            if "custom" not in registered_user.password and models.GetParametre(nom="MDP_FORCER_MODIFICATION", dict_parametres=dict_parametres, defaut="True") == "True" :
                app.logger.debug("Force modification mot de passe pour %s", form.identifiant.data)
                return redirect(url_for('force_change_password'))

            return redirect(url_for('accueil'))
            #return redirect(request.args.get('next') or url_for('accueil'))

    # Re-demande codes si incorrects
    if "recaptcha" in form.errors:
        flash(u"Vous devez cocher la case 'Je ne suis pas un robot'", 'error')
    else:
        flash(u"Codes d'accès incorrects", 'error')
    return redirect(url_for('login'))
                   
        
@app.route('/logout')
def logout():
    logout_user()
    flash(u"Vous avez été déconnecté", "error")
    return redirect(url_for('login'))


# ------------------------- FORCE CHANGE PASSWORD ----------------------------------

@app.route('/force_change_password', methods=['GET', 'POST'])
@login_required
def force_change_password():
    # Si l'utilisateur n'est pas connecté, on le renvoie vers l'accueil
    if not current_user.is_authenticated or "custom" in current_user.password :
        return redirect(url_for('login'))

    # Génération du form de login
    form = forms.ChangePassword()

    # Affiche la page de changement
    if request.method == 'GET':
        dict_parametres = models.GetDictParametres()
        conditions_utilisation = models.Element.query.filter_by(categorie="conditions_utilisation").first()
        if conditions_utilisation == None :
            conditions_utilisation = ""
        else :
            conditions_utilisation = utils.FusionDonneesOrganisateur(conditions_utilisation.texte_html, dict_parametres)
        return render_template('force_change_password.html', form=form, dict_parametres=dict_parametres, conditions_utilisation=conditions_utilisation)

    # Validation du form avec Flask-WTF
    if form.validate_on_submit():
        if ValiderModificationPassword(form=form) != True :
            return redirect(url_for("force_change_password"))

    # Renvoie vers l'accueil
    flash(u"Votre nouveau mot de passe a bien été enregistré")
    return redirect(url_for('accueil'))



# ------------------------- ACCUEIL ----------------------------------

@app.route('/accueil')
@login_required
def accueil():
    # Vérifie que son mot de passe est personnalisé, sinon on le logout
    if "custom" not in current_user.password and models.GetParametre(nom="MDP_FORCER_MODIFICATION", defaut="True") == "True":
        flash(u"Vous devez obligatoirement modifier votre mot de passe !", 'error')
        return redirect(url_for('logout'))

    if current_user.role == "famille" :
        return redirect(url_for('accueil_famille'))
    if current_user.role == "utilisateur" :
        return redirect(url_for('accueil_admin'))
    return redirect(url_for('logout'))


@app.route('/accueil_famille')
@login_required
def accueil_famille():
    dict_parametres = models.GetDictParametres()

    # Vérifie que son mot de passe est personnalisé, sinon on le logout
    if "custom" not in current_user.password and models.GetParametre(nom="MDP_FORCER_MODIFICATION", dict_parametres=dict_parametres, defaut="True") == "True":
        flash(u"Vous devez obligatoirement modifier votre mot de passe !", 'error')
        return redirect(url_for('logout'))

    if current_user.role != "famille" :
        return redirect(url_for('logout'))

    # Récupération des éléments manquants
    liste_pieces_manquantes = models.Piece_manquante.query.filter_by(IDfamille=current_user.IDfamille).order_by(models.Piece_manquante.IDtype_piece).all()
    liste_cotisations_manquantes = models.Cotisation_manquante.query.filter_by(IDfamille=current_user.IDfamille).order_by(models.Cotisation_manquante.nom).all()
    
    # Récupération des messages
    liste_messages_temp = models.Message.query.order_by(models.Message.texte).all()
    liste_messages = []
    for message in liste_messages_temp :
        if message.Is_actif_today() :
            liste_messages.append(message)

    app.logger.debug("Page ACCUEIL (%s): famille id(%s)", current_user.identifiant, current_user.IDfamille)
    return render_template('accueil.html', active_page="accueil_famille",\
                            liste_pieces_manquantes=liste_pieces_manquantes, \
                            liste_cotisations_manquantes=liste_cotisations_manquantes, \
                            liste_messages=liste_messages, \
                            dict_parametres=dict_parametres)


@app.route('/accueil_admin')
@login_required
def accueil_admin():
    if current_user.role != "utilisateur" :
        return redirect(url_for('logout'))


    dict_parametres = models.GetDictParametres()
    app.logger.debug("Page ACCUEIL_ADMIN (%s): utilisateur id(%s)", current_user.identifiant, current_user.IDutilisateur)
    return render_template('admin.html', active_page="accueil_admin", dict_parametres=dict_parametres)


    
# ------------------------- FACTURES ---------------------------------- 

@app.route('/factures')
@login_required
def factures():
    if current_user.role != "famille" :
        return redirect(url_for('logout'))

    dict_parametres = models.GetDictParametres()

    # Récupération de la liste des factures
    liste_factures = models.Facture.query.filter_by(IDfamille=current_user.IDfamille).order_by(models.Facture.date_debut.desc()).all()
    app.logger.debug("Page FACTURES (%s): famille id(%s) liste_factures:(%s)", current_user.identifiant, current_user.IDfamille, liste_factures)

    # Récupération des montants paiements en ligne en attente de validation
    liste_paiements = models.Paiement.query.filter_by(IDfamille=current_user.IDfamille).all()
    dict_paiements = {"facture": {}, "periode": {}}
    if len(liste_paiements) > 0:
        liste_IDpaiement_attente = [paiement.IDpaiement for paiement in models.Action.query.filter_by(action="paiement_en_ligne", IDfamille=current_user.IDfamille, etat="attente").all()]
        for paiement in liste_paiements:
            if paiement.IDpaiement in liste_IDpaiement_attente:
                paid = False
                en_cours_paiement = "0"

                # Si le paiement est confirmé
                if paiement.resultat == "PAID" or paiement.resultrans in ("P", "V"):
                    paid = True

                # Si le paiement TIPI n'est pas confirmé mais qu'il a été effectué il y a moins de 5 minutes
                if paid == False and paiement.systeme_paiement == "tipi_regie" and datetime.datetime.strptime(paiement.IDtransaction[:12], "%Y%m%d%H%M") + datetime.timedelta(minutes=5) > datetime.datetime.utcnow():
                    paid = True
                    en_cours_paiement = "1"

                if paid == True:
                    for texte in paiement.ventilation.split(","):
                        if texte[0] == "F":
                            type_impaye = "facture"
                        elif texte[0] == "P":
                            type_impaye = "periode"
                        else :
                            type_impaye = None
                        if type_impaye != None:
                            ID, montant = texte[1:].split("#")
                            ID, montant = int(ID), float(montant)
                            if (ID in dict_paiements[type_impaye]) == False :
                                dict_paiements[type_impaye][ID] = {"montant": 0.0, "en_cours_paiement": en_cours_paiement}
                            dict_paiements[type_impaye][ID]["montant"] += montant

    # Recherche les factures impayées
    nbre_factures_impayees = 0
    montant_impaye = 0.0
    for facture in liste_factures :

        # Cherche si un paiement en ligne en attente n'a pas déjà réglé la facture
        if facture.IDfacture in dict_paiements["facture"]:
            facture.montant_regle += dict_paiements["facture"][facture.IDfacture]["montant"]
            facture.montant_solde -= dict_paiements["facture"][facture.IDfacture]["montant"]
            facture.en_cours_paiement = dict_paiements["facture"][facture.IDfacture]["en_cours_paiement"]

        # Additionne les factures impayées
        if facture.montant_solde > 0.0 :
            nbre_factures_impayees += 1
            montant_impaye += facture.montant_solde

    # Recherche la préfacturation
    liste_prefacturation = []
    prefacturation_has_impaye = False
    if models.GetParametre(nom="FACTURES_PREFACTURATION", dict_parametres=dict_parametres) == "True":
        liste_prefacturation = models.Prefacturation.query.filter_by(IDfamille=current_user.IDfamille).order_by(models.Prefacturation.IDperiode.desc()).all()
        for prefacturation in liste_prefacturation :

            # Cherche si un paiement en ligne en attente n'a pas déjà réglé la période
            if prefacturation.IDperiode in dict_paiements["periode"]:
                prefacturation.montant_regle += dict_paiements["periode"][prefacturation.IDperiode]["montant"]
                prefacturation.montant_solde -= dict_paiements["periode"][prefacturation.IDperiode]["montant"]

            if prefacturation.montant_solde > 0.0 :
                montant_impaye += prefacturation.montant_solde
                prefacturation_has_impaye = True

    # Création du texte de rappel des impayés
    texte_impayes = None
    if montant_impaye > 0.0 :
        texte_impayes = u"Il reste "
        if nbre_factures_impayees == 1 :
            texte_impayes += u"1 facture à régler "
        if nbre_factures_impayees > 1 :
            texte_impayes += u"%d factures à régler " % nbre_factures_impayees
        if prefacturation_has_impaye == True :
            if nbre_factures_impayees > 0 :
                texte_impayes += u"et "
            texte_impayes += u"des prestations à régler en avance "
        texte_impayes += u"pour un total de <strong>%s</strong>" % utils.CallFonction("Formate_montant", montant_impaye)

    # Recherche l'historique des demandes liées aux factures
    historique = GetHistorique(IDfamille=current_user.IDfamille, categorie="factures", dict_parametres=dict_parametres)

    app.logger.debug("Page FACTURES (%s): famille id(%s)", current_user.identifiant, current_user.IDfamille)
    return render_template('factures.html', active_page="factures", liste_factures=liste_factures, texte_impayes=texte_impayes, \
                            liste_paiements=liste_paiements, liste_prefacturation=liste_prefacturation, \
                            historique=historique, dict_parametres=dict_parametres)

                            
@app.route('/envoyer_demande_facture')
@login_required
def envoyer_demande_facture():
    if current_user.role != "famille" :
        return redirect(url_for('logout'))

    try:
        id = request.args.get("id", 0, type=int)
        numfacture = request.args.get("info", "", type=str)
        methode_envoi = request.args.get("methode_envoi", "", type=str)
        commentaire = request.args.get("commentaire", "", type=six.text_type)
        
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
    except Exception as erreur:
        return jsonify(success=0, error_msg=str(erreur))
                            

def GetPaymentPayzen():
    dict_parametres = models.GetDictParametres()
    site_id = models.GetParametre(nom="PAYZEN_SITE_ID", dict_parametres=dict_parametres)
    mode = models.GetParametre(nom="PAYZEN_MODE", dict_parametres=dict_parametres)
    certificat_test = models.GetParametre(nom="PAYZEN_CERTIFICAT_TEST", dict_parametres=dict_parametres)
    certificat_production = models.GetParametre(nom="PAYZEN_CERTIFICAT_PRODUCTION", dict_parametres=dict_parametres)

    # Envoi de la requete
    p = Payment("payzen", {
        'vads_site_id': site_id,
        'vads_ctx_mode': mode,
        'secret_test': certificat_test,
        'secret_production': certificat_production,
        'vads_url_return': url_for('accueil', _external=True),
        'vads_url_cancel': url_for('retour_paiement_cancel', _external=True),
        'vads_url_error': url_for('retour_paiement_error', _external=True),
        'vads_url_refused': url_for('retour_paiement_refused', _external=True),
        'vads_url_success': url_for('retour_paiement_success', _external=True),
        'vads_contrib': 'noethys',
        })#, logger=app.logger)

    # Modifie le répertoire temp si on est sous Windows
    if sys.platform.startswith("win"):
        repertoire_temp = os.path.join(REP_CONNECTHYS, "temp")
        if os.path.isdir(repertoire_temp) == False:
            os.mkdir(repertoire_temp)
        p.backend.PATH = repertoire_temp

    return p




@app.route('/effectuer_paiement_en_ligne')
@login_required
def effectuer_paiement_en_ligne():
    if current_user.role != "famille" :
        return redirect(url_for('logout'))

    app.logger.debug("Page EFFECTUER_PAIEMENT EN LIGNE (%s): famille id(%s)", current_user.identifiant, current_user.IDfamille)

    dict_parametres = models.GetDictParametres()

    try:
        # Récupération des données de la requête
        montant_reglement = request.args.get("montant_reglement", ",", type=float)
        liste_impayes_txt = request.args.get("liste_impayes", ",", type=str)
        paiement_echelonne = request.args.get("paiement_echelonne", 0, type=int)

        # Vérifie que le montant est supérieur à zéro
        if montant_reglement == 0.0 :
            return jsonify(success=0, error_msg=u"Le montant doit être supérieur à zéro !")

        # Vérifie que le montant est supérieur au montant minimal fixé
        montant_minimal = float(models.GetParametre(nom="PAIEMENT_EN_LIGNE_MONTANT_MINIMAL", dict_parametres=dict_parametres))
        if montant_reglement < montant_minimal :
            return jsonify(success=0, error_msg=u"Le paiement en ligne nécessite un montant minimal de %.2f € !" % montant_minimal)

        # Mémorise les numéros de factures et la ventilation
        dict_ventilation = {"facture": {}, "periode": {}}
        for texte in liste_impayes_txt.split(','):
            type_impaye, ID, solde = texte.split("##")
            dict_ventilation[type_impaye][int(ID)] = float(solde)

        # Importation des factures
        liste_factures = models.Facture.query.filter(models.Facture.IDfacture.in_(list(dict_ventilation["facture"].keys()))).order_by(models.Facture.date_debut.desc()).all()

        # On mémorise la ventilation
        ventilation = []
        for type_impaye in ["facture", "periode"]:
            for ID, solde in dict_ventilation[type_impaye].items():
                if type_impaye == "facture" : prefixe = "F"
                if type_impaye == "periode": prefixe = "P"
                ventilation.append("%s%d#%s" % (prefixe, ID, solde))
        ventilation_str = ",".join(ventilation)

        # Mémorisation de la liste des ID de facture en str
        factures_ID_str = ",".join([str(IDfacture) for IDfacture in list(dict_ventilation["facture"].keys())])

        # --------------------------- Mode démo -----------------------------

        if models.GetParametre(nom="PAIEMENT_EN_LIGNE_SYSTEME", dict_parametres=dict_parametres) == "4":
            app.logger.debug("Page EFFECTUER_PAIEMENT_EN_LIGNE MODE DEMO (IDFamille %s) : montant=%s factures_ID=%s", current_user.identifiant, str(montant_reglement), factures_ID_str)

            return jsonify(success=1, systeme_paiement="demo")


        # ----------------------- Paiement avec TIPI -------------------------

        if models.GetParametre(nom="PAIEMENT_EN_LIGNE_SYSTEME", dict_parametres=dict_parametres) == "1":
            systeme_paiement = "tipi_regie"
            liste_regies = models.Regie.query.all()
            saisie_type = models.GetParametre(nom="PAIEMENT_EN_LIGNE_TIPI_SAISIE", dict_parametres=dict_parametres)
            app.logger.debug("Page EFFECTUER_PAIEMENT EN LIGNE (%s): famille id(%s) saisie_type(%s)", current_user.identifiant, current_user.IDfamille, saisie_type)

            # validation
            if saisie_type == '1':
                saisie = 'X'
            # production
            elif saisie_type == '2':
                saisie = 'A'
            else:
                saisie = 'T'

            app.logger.debug("Page EFFECTUER_PAIEMENT EN LIGNE (%s): famille id(%s) liste_regie(%s)", current_user.identifiant, current_user.IDfamille, liste_regies)

            # il y a plus d une facture sélectionnée
            if len(dict_ventilation["facture"]) > 1:
                app.logger.debug(u"Page EFFECTUER_PAIEMENT_EN_LIGNE (%s): plus d'une facture selectionnee pour TIPI NON TRAITE", current_user.identifiant)
                return jsonify(success=0, error_msg="Paiement en ligne multi-factures impossible")

            # Vérifie qu'il n'y a pas de préfacturation dedans
            if len(dict_ventilation["periode"]) > 0 :
                app.logger.debug(u"Page EFFECTUER_PAIEMENT_EN_LIGNE (%s): Il n'est pas possible de régler de la préfacturation avec TIPI", current_user.identifiant)
                return jsonify(success=0, error_msg="Paiement de la prefacturation impossible avec TIPI")

            # Envoi de la requete
            facture = liste_factures[0]
            regie = models.Regie.query.filter_by(IDregie=facture.IDregie).first()
            if regie == None :
                app.logger.debug(u"Page EFFECTUER_PAIEMENT_EN_LIGNE TIPI (%s): Aucune régie n'a été paramétrée.", current_user.identifiant)
                return jsonify(success=0, error_msg=u"Aucune régie n'a été paramétrée. Contactez l'administrateur du portail.")

            app.logger.debug(u"Page EFFECTUER_PAIEMENT_EN_LIGNE : IDfacture:%s montant:%s regie.nom: (%s) type(regie.nom): (%s) regie.numclitipi: (%s)", facture.IDfacture, montant_reglement, regie.nom, type(regie.nom), regie.numclitipi)
            p = Payment(systeme_paiement, {'numcli': regie.numclitipi})
            requete = p.request(amount=str(montant_reglement),
                exer=str(facture.date_debut.year),
                refdet=facture.numero,
                objet="Paiement " + regie.nom.encode("ascii", 'ignore'),
                email=utils.CallFonction("DecrypteChaine", current_user.email).split(";")[0],
                urlcl=url_for('retour_tipi', _external=True),
                saisie=saisie)
            app.logger.debug(u"Page EFFECTUER_PAIEMENT_EN_LIGNE (%s): requete: %s // systeme_paiement(%s)", current_user.identifiant, requete, systeme_paiement)

            # Enregistrement du paiement
            m = models.Paiement(IDfamille=current_user.IDfamille, systeme_paiement=systeme_paiement, factures_ID=factures_ID_str,
                                IDtransaction=requete[0], refdet=facture.numero, montant=montant_reglement, objet=requete[3], saisie=saisie,
                                ventilation=ventilation_str, horodatage=datetime.datetime.now())
            db.session.add(m)
            db.session.commit()

            flash(u"Votre demande de paiement en ligne d'une facture est en cours")
            return jsonify(success=1, systeme_paiement="tipi_regie", urltoredirect=requete[2])

        # ----------------------- Paiement avec PAYZEN ----------------------
        if models.GetParametre(nom="PAIEMENT_EN_LIGNE_SYSTEME", dict_parametres=dict_parametres) == "3":
            systeme_paiement = "payzen"

            # Envoi de la requete
            p = GetPaymentPayzen()

            email = utils.CallFonction("DecrypteChaine", current_user.email).split(";")[0]
            if paiement_echelonne == 1:
                # Vérifie le montant minimal pour le paiement échelonné
                montant_minimal_echelonnement = 30.0
                if montant_reglement < montant_minimal_echelonnement:
                    return jsonify(success=0, error_msg=u"Le paiement en plusieurs fois nécessite un montant minimal de %.2f € !" % montant_minimal_echelonnement)

                # Calcul des dates et montants échelonnés
                montant_total = montant_reglement * 100
                today = datetime.date.today()
                paiement_1 = "%s=%d" % (today.strftime("%Y%m%d"), (montant_total // 3) + (montant_total % 3))
                paiement_2 = "%s=%d" % ((today + datetime.timedelta(days=30)).strftime("%Y%m%d"), montant_total // 3)
                paiement_3 = "%s=%d" % ((today + datetime.timedelta(days=60)).strftime("%Y%m%d"), montant_total // 3)
                vads_payment_config = "MULTI_EXT:%s;%s;%s" % (paiement_1, paiement_2, paiement_3)
            else:
                vads_payment_config = "SINGLE"
            requete = p.request(amount=montant_reglement, email=email, vads_payment_config=vads_payment_config)
            transaction_id, f, form = requete

            app.logger.debug("Page EFFECTUER_PAIEMENT_EN_LIGNE PAYZEN (IDFamille %s) : IDtransaction=%s montant=%s factures_ID=%s", current_user.identifiant, transaction_id, str(montant_reglement), factures_ID_str)

            # Enregistrement du paiement dans la base
            m = models.Paiement(IDfamille=current_user.IDfamille, systeme_paiement=systeme_paiement, factures_ID=factures_ID_str,
                                IDtransaction=transaction_id, montant=montant_reglement, saisie=models.GetParametre(nom="PAYZEN_MODE", dict_parametres=dict_parametres),
                                ventilation=ventilation_str, horodatage=datetime.datetime.now())
            db.session.add(m)
            db.session.commit()

            # Renvoie le formulaire de paiement au template
            form = six.text_type(form)
            form = form.replace("<form ", "<form id='form_paiement' ")
            return jsonify(success=1, systeme_paiement=systeme_paiement, form_paiement=form)

    except Exception as erreur:
        app.logger.debug("Page EFFECTUER_PAIEMENT_EN_LIGNE (%s): ERREUR: %s)", current_user.identifiant, erreur)
        return jsonify(success=0, error_msg=str(erreur))



# ---------------------- NOTIFICATION PAYZEN --------------------

@app.route('/ipn_payzen', methods=['POST'])
@csrf.exempt
def ipn_payzen():
    app.logger.debug("Page RETOUR IPN PAYZEN")

    # Extraction des variables post
    data = request.get_data(as_text=True).encode('ASCII')
    app.logger.debug(data)

    # Récupération des données et calcul de la signature
    p = GetPaymentPayzen()
    reponse = p.response(data)

    # Vérifie que la signature de la réponse est correcte
    if reponse.signed != True :
        app.logger.debug(u"Paiement en ligne IDtransaction=%s : ATTENTION, erreur de signature dans la réponse !" % reponse.order_id)

    # Recherche l'état du paiement
    resultat = ETATS_PAIEMENTS[reponse.result]

    # Recherche s'il s'agit un paiement MULTI
    if resultat == "ERROR":
        vads_card_brand = request.form.get("vads_card_brand", 0, type=str)
        vads_result = request.form.get("vads_result", 0, type=str)
        if reponse.signed == True and vads_card_brand == "MULTI" and vads_result == "00":
            resultat = "PAID"

    # Affichage de la réponse dans le log
    app.logger.debug(u"Paiement en ligne IDtransaction=%s : signature=%s, resultat=%s" % (reponse.order_id, reponse.signed, resultat))

    # Modification du paiement pré-enregistré
    paiement = models.Paiement.query.filter_by(IDtransaction=reponse.order_id).first()
    paiement.resultat = resultat
    paiement.message = reponse.bank_status.decode("utf8")
    db.session.commit()

    # Paiement échelonné
    vads_payment_config = request.form.get("vads_payment_config", "SINGLE", type=str)
    vads_payment_config = vads_payment_config.replace("=", ">")

    # Enregistrement de l'action
    if resultat == "PAID":
        parametres = u"systeme_paiement=%s#factures_ID=%s#IDpaiement=%s#IDtransaction=%s#montant=%s#config=%s" % (paiement.systeme_paiement, paiement.factures_ID, paiement.IDpaiement, paiement.IDtransaction, paiement.montant, vads_payment_config)
        commentaire = paiement.message
        if vads_payment_config != "SINGLE":
            liste_paiements = []
            for date, montant in re.findall(r"([0-9]+)>([0-9]+)", vads_payment_config):
                liste_paiements.append(u"%s (%s)" % (float(montant)/100, datetime.datetime.strptime(date, "%Y%m%d").strftime("%d/%m/%Y")))
            commentaire += u". Paiement en plusieurs fois : %s." % ", ".join(liste_paiements)
        description = u"Paiement en ligne - Transaction n°%s de %s" % (paiement.IDtransaction.split("_")[1], utils.Formate_montant(paiement.montant))
        m = models.Action(IDfamille=paiement.IDfamille, categorie="reglements", action="paiement_en_ligne", IDpaiement=paiement.IDpaiement,
                          description=description, etat="attente", commentaire=commentaire, parametres=parametres, ventilation=paiement.ventilation)
        db.session.add(m)
        db.session.commit()

    app.logger.debug(u"Enregistrement de l'action Paiement en ligne IDtransaction=%s", paiement.IDtransaction)
    return 'Notification processed'



# ---------------------- RETOUR PAIEMENT --------------------

@app.route('/retour_paiement_cancel', methods=['GET'])
@login_required
def retour_paiement_cancel():
    dict_parametres = models.GetDictParametres()
    return render_template('retour_paiement.html', active_page="factures", resultat="cancel", dict_parametres=dict_parametres)

@app.route('/retour_paiement_error', methods=['GET'])
@login_required
def retour_paiement_error():
    dict_parametres = models.GetDictParametres()
    return render_template('retour_paiement.html', active_page="factures", resultat="error", dict_parametres=dict_parametres)

@app.route('/retour_paiement_refused', methods=['GET'])
@login_required
def retour_paiement_refused():
    dict_parametres = models.GetDictParametres()
    return render_template('retour_paiement.html', active_page="factures", resultat="refused", dict_parametres=dict_parametres)

@app.route('/retour_paiement_success', methods=['GET'])
@login_required
def retour_paiement_success():
    dict_parametres = models.GetDictParametres()
    return render_template('retour_paiement.html', active_page="factures", resultat="success", dict_parametres=dict_parametres)


@app.route('/fix_doublons', methods=['GET', 'POST'])
def fix_doublons():
    app.logger.debug("Suppression des doublons dans les actions...")
    resultats = db.session.execute("select count(*) as nbre_doublons, IDpaiement, min(IDaction) from portail_actions where IDpaiement is not null group by IDpaiement having count(*) > 1;")
    for index, (nbre_doublons, IDpaiement, IDaction) in enumerate(resultats, 1):
        app.logger.debug("index=%d IDpaiement=%d min(IDaction)=%d" % (index, IDpaiement, IDaction))
        models.Action.query.filter_by(IDpaiement=IDpaiement, etat="attente").filter(models.Action.IDaction!=IDaction).update({models.Action.etat: "validation"})
    db.session.commit()
    app.logger.debug("Fin de la suppression des doublons")
    return jsonify(success=1, error_msg="ok")


# -----------------------RETOUR TIPI REGIE-------------------

@app.route('/retour_tipi', methods=['POST'])
@csrf.exempt
def retour_tipi():
    # if current_user.role != "famille" :
    #     return redirect(url_for('logout'))

    try :

        # Extraction des variables post
        data = request.get_data(as_text=True).encode('ASCII')

        # Extraction des champs non traités par eopayment
        resultrans = request.form.get("resultrans", 0, type=str)
        numauto = request.form.get("numauto", 0, type=str)
        dattrans = request.form.get("dattrans", 0, type=str)
        heurtrans = request.form.get("heurtrans", 0, type=str)

        # Récupération des données et calcul de la signature
        p = Payment("tipi_regie", {})
        reponse = p.response(data)

        # Recherche l'état du paiement
        resultat = ETATS_PAIEMENTS[reponse.result]

        # Modification du paiement pré-enregistré
        paiement = models.Paiement.query.filter_by(IDtransaction=reponse.transaction_id).first()
        if paiement == None :
            app.logger.debug("Page RETOUR_TIPI: le paiement pre-enregistre n'a pas ete trouve.)")
            return jsonify(success=0, error_msg=u"Le paiement pré-enregistré n'a pas été trouvé dans la base.")

        # Evite les doublons
        if models.Action.query.filter_by(IDpaiement=paiement.IDpaiement).count():
            app.logger.debug("Page RETOUR_TIPI: Doublon sur le retour tipi.)")
            return redirect(url_for('retour_paiement_error'))

        paiement.resultrans = resultrans
        paiement.resultat = resultat
        paiement.numauto = numauto
        paiement.dattrans = dattrans
        paiement.heurtrans = heurtrans
        paiement.message = reponse.bank_status.decode("utf8")
        db.session.commit()

        # Réponse dans log
        app.logger.debug("Page RETOUR_TIPI: reponse:%s refdet: %s)", reponse, paiement.refdet)

        # Enregistrement du résultat et redirection
        if resultat == "PAID":
            parametres = u"systeme_paiement=%s#factures_ID=%s#IDpaiement=%s#IDtransaction=%s#refdet=%s#montant=%s#objet=%s#numauto=%s#dattrans=%s#heurtrans=%s" % ("tipi_regie", paiement.factures_ID, paiement.IDpaiement, paiement.IDtransaction, paiement.refdet, paiement.montant, paiement.objet, numauto, dattrans, heurtrans)
            commentaire = ""
            description = "Paiement en ligne de la facture %s" % paiement.refdet
            m = models.Action(IDfamille=paiement.IDfamille, categorie="reglements", action="paiement_en_ligne", description=description,
                              IDpaiement=paiement.IDpaiement, etat="attente", commentaire=commentaire, parametres=parametres, ventilation=paiement.ventilation)
            db.session.add(m)
            db.session.commit()
            app.logger.debug(u"Enregistrement de l'action Paiement en ligne IDtransaction=%s", paiement.IDtransaction)

            return redirect(url_for('retour_paiement_success'))

        elif resultat == "DENIED":
            return redirect(url_for('retour_paiement_refused'))
        elif resultat == "CANCELLED":
            return redirect(url_for('retour_paiement_cancel'))
        else :
            return redirect(url_for('retour_paiement_error'))

    except Exception as erreur:
        app.logger.debug("Page RETOUR_TIPI: ERREUR: %s", erreur)
        return jsonify(success=0, error_msg=str(erreur))


# ------------------------- REGLEMENTS ---------------------------------- 

@app.route('/reglements')
@login_required
def reglements():
    if current_user.role != "famille" :
        return redirect(url_for('logout'))

    # Récupération de la liste des règlements
    liste_reglements = models.Reglement.query.filter_by(IDfamille=current_user.IDfamille).order_by(models.Reglement.date.desc()).all()

    # Récupération de la liste des paiements en attente
    liste_paiements_temp = models.Paiement.query.filter_by(IDfamille=current_user.IDfamille, resultat="PAID").order_by(models.Paiement.horodatage.desc()).all()
    dict_paiements_factures = {}
    liste_paiements = []
    if len(liste_paiements_temp) > 0:
        liste_IDpaiement_attente = [paiement.IDpaiement for paiement in models.Action.query.filter_by(action="paiement_en_ligne", IDfamille=current_user.IDfamille, etat="attente").all()]
        for paiement in liste_paiements_temp:
            if paiement.IDpaiement in liste_IDpaiement_attente:
                liste_paiements.append(paiement)

    # Recherche l'historique des demandes liées aux règlements
    dict_parametres = models.GetDictParametres()
    historique = GetHistorique(IDfamille=current_user.IDfamille, categorie="reglements", dict_parametres=dict_parametres)
    
    app.logger.debug("Page REGLEMENTS (%s): famille id(%s)", current_user.identifiant, current_user.IDfamille)
    return render_template('reglements.html', active_page="reglements", liste_reglements=liste_reglements, \
                           liste_paiements=liste_paiements, historique=historique, dict_parametres=dict_parametres)

                            
@app.route('/envoyer_demande_recu')
@login_required
def envoyer_demande_recu():
    if current_user.role != "famille" :
        return redirect(url_for('logout'))

    try:
        id = request.args.get("id", 0, type=int)
        info = request.args.get("info", "", type=str)
        methode_envoi = request.args.get("methode_envoi", "", type=str)
        commentaire = request.args.get("commentaire", "", type=six.text_type)
        
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
    except Exception as erreur:
        return jsonify(success=0, error_msg=str(erreur))
                          
                            
                            
# ------------------------- HISTORIQUE ---------------------------------- 

@app.route('/historique')
@login_required
def historique():
    if current_user.role != "famille" :
        return redirect(url_for('logout'))

    # Recherche l'historique général
    dict_parametres = models.GetDictParametres()
    historique = GetHistorique(IDfamille=current_user.IDfamille, categorie=None, dict_parametres=dict_parametres)
    app.logger.debug("Page HISTORIQUE (%s): famille id(%s)", current_user.identifiant, current_user.IDfamille)
    return render_template('historique.html', active_page="historique", historique=historique, dict_parametres=dict_parametres)
                            
                            
# ------------------------- PIECES ---------------------------------- 

@app.route('/pieces', methods=['GET', 'POST'])
@login_required
def pieces():
    if current_user.role != "famille":
        return redirect(url_for('logout'))

    # S'il s'agit d'un upload de pièce
    if request.method == 'POST' and 'piece' in request.files:
        nom, ext = request.files['piece'].filename.rsplit(".", 1)
        try:
            nom_fichier = app.pieces.save(request.files["piece"], name="%s.%s" % (str(uuid4()), ext))
        except:
            flash(u"Vous ne pouvez pas transmettre cette pièce", 'error')
            return redirect(url_for('pieces'))
        chemin_fichier = os.path.join(app.REP_PIECES, nom_fichier)

        # Cryptage du fichier
        if IMPORT_AES:
            cryptage_mdp = app.config['SECRET_KEY'][:10]
            resultat = CrypterFichier(chemin_fichier, chemin_fichier, cryptage_mdp)

        choix_type_piece = request.form.get("choix_type_piece", "", type=int)
        titre_piece = request.form.get("titre_piece", "", type=six.text_type)
        commentaire = request.form.get("commentaire", "", type=six.text_type)
        parametres = "chemin=%s" % nom_fichier

        # Recherche la pièce manquante
        IDindividu = None
        if choix_type_piece:
            piece_manquante = models.Piece_manquante.query.filter_by(IDpiece_manquante=choix_type_piece).first()
            titre_piece = piece_manquante.GetNom()
            parametres += "#IDtype_piece=%d" % piece_manquante.IDtype_piece
            if piece_manquante.IDindividu:
                IDindividu = piece_manquante.IDindividu

        description = u"Envoi de la pièce %s" % titre_piece
        m = models.Action(IDfamille=current_user.IDfamille, IDindividu=IDindividu, categorie="pieces", action="envoyer", description=description, etat="attente", commentaire=commentaire, parametres=parametres)
        db.session.add(m)
        db.session.commit()

        flash(u"Pièce enregistrée avec succès")
        return redirect(url_for('pieces'))

    # Form envoi de pièces
    form = forms.Piece()

    # Récupération de la liste des pièces manquantes
    liste_pieces_manquantes = models.Piece_manquante.query.filter_by(IDfamille=current_user.IDfamille).order_by(models.Piece_manquante.IDtype_piece).all()

    # Récupération de la liste des types de pièces
    liste_types_pieces = models.Type_piece.query.order_by(models.Type_piece.nom).all()
    dict_parametres = models.GetDictParametres()

    # Historique
    historique = GetHistorique(IDfamille=current_user.IDfamille, categorie="pieces", dict_parametres=dict_parametres)

    app.logger.debug("Page PIECES (%s): famille id(%s) liste_pieces_manquantes: %s", current_user.identifiant, current_user.IDfamille, liste_pieces_manquantes)
    return render_template('pieces.html', active_page="pieces", form=form, \
                            liste_pieces_manquantes=liste_pieces_manquantes,\
                            liste_types_pieces=liste_types_pieces, dict_parametres=dict_parametres, historique=historique)


# ------------------------- COTISATIONS ---------------------------------- 

@app.route('/cotisations')
@login_required
def cotisations():
    if current_user.role != "famille" :
        return redirect(url_for('logout'))

    # Récupération de la liste des cotisations manquantes
    liste_cotisations_manquantes = models.Cotisation_manquante.query.filter_by(IDfamille=current_user.IDfamille).order_by(models.Cotisation_manquante.nom).all()

    # Récupération de la liste des cotisations
    liste_individus = models.Individu.query.filter_by(IDfamille=current_user.IDfamille).all()
    liste_IDindividu = [individu.IDindividu for individu in liste_individus]
    liste_cotisations = models.Cotisation.query.filter(or_(models.Cotisation.IDindividu.in_(liste_IDindividu), models.Cotisation.IDfamille == current_user.IDfamille)).order_by(models.Cotisation.date_debut.desc()).all()

    dict_parametres = models.GetDictParametres()
    app.logger.debug("Page COTISATIONS (%s): famille id(%s)", current_user.identifiant, current_user.IDfamille)
    return render_template('cotisations.html', active_page="cotisations", liste_cotisations=liste_cotisations, \
                            liste_cotisations_manquantes=liste_cotisations_manquantes, dict_parametres=dict_parametres)



# ------------------------- LOCATIONS ----------------------------------

@app.route('/locations')
@login_required
def locations():
    if current_user.role != "famille" :
        return redirect(url_for('logout'))

    # Récupération de la liste des locations
    liste_locations = models.Location.query.filter(models.Location.IDfamille==current_user.IDfamille, models.Location.date_debut >= datetime.date.today()).all()
    liste_reservations = models.Reservation_location.query.filter(
        models.Reservation_location.action.has(IDfamille=current_user.IDfamille),
        models.Reservation_location.action.has(etat="attente"),
        models.Reservation_location.date_debut >= datetime.date.today()
        ).all()

    dict_locations = {}
    for location in liste_locations:
        dict_locations[location.IDlocation] = {"debut": location.date_debut, "fin": location.date_fin, "IDproduit": location.IDproduit, "etat": "valide"}
    for reservation in liste_reservations:
        etat = "attente"
        if reservation.etat == "supprimer":
            etat = "suppr"
        dict_locations[reservation.IDlocation] = {"debut": reservation.date_debut, "fin": reservation.date_fin, "IDproduit": reservation.IDproduit, "etat": etat}
    prochaines_locations = sorted(list(dict_locations.values()), key=itemgetter('debut'))

    # Récupération du dict des produits
    liste_produits = models.Produit.query.order_by(models.Produit.nom).all()
    dict_produits = {}
    for produit in liste_produits:
        dict_produits[produit.IDproduit] = produit.nom

    # Recherche l'historique des demandes liées aux réservations
    dict_parametres = models.GetDictParametres()
    historique = GetHistorique(IDfamille=current_user.IDfamille, categorie="locations", dict_parametres=dict_parametres)
    
    app.logger.debug("Page LOCATIONS (%s): famille id(%s)", current_user.identifiant, current_user.IDfamille)
    return render_template('locations.html', active_page="locations", prochaines_locations=prochaines_locations, dict_produits=dict_produits, \
                           dict_parametres=dict_parametres, historique=historique)


@app.route('/planning_locations')
@login_required
def planning_locations():
    if current_user.role != "famille":
        return redirect(url_for('logout'))

    liste_produits = []
    for produit in models.Produit.query.order_by(models.Produit.nom).all():
        liste_produits.append({"IDproduit": produit.IDproduit, "partage": 1 if produit.activation_partage else 0})

    # Form location
    form = forms.Location()

    dict_parametres = models.GetDictParametres()
    return render_template('planning_locations.html', active_page="locations", form=form, liste_produits=liste_produits, dict_parametres=dict_parametres)


@app.route('/get_produits')
@login_required
def get_produits():
    liste_produits = models.Produit.query.order_by(models.Produit.nom).all()
    liste_finale = []
    for produit in liste_produits:
        dictProduit = {
            "id": str(produit.IDproduit),
            "groupId": produit.nom_categorie,
            "title": produit.nom,
            "eventColor": 'green',
            "activation_partage": produit.activation_partage,
        }
        liste_finale.append(dictProduit)
    return jsonify(liste_finale)


@app.route('/get_locations/<int:idfamille>')
@login_required
def get_locations(idfamille=None):
    if current_user.IDfamille != idfamille:
        return jsonify([])

    if len(request.args['start']) == 10:
        start = datetime.datetime.strptime(request.args['start'], '%Y-%m-%d')
        end = datetime.datetime.strptime(request.args['end'], '%Y-%m-%d')
    else:
        start = datetime.datetime.strptime(request.args['start'], '%Y-%m-%dT%H:%M:%S')
        end = datetime.datetime.strptime(request.args['end'], '%Y-%m-%dT%H:%M:%S')

    # Récupération des paramètres
    dict_parametres = models.GetDictParametres()

    # Importation des produits
    liste_produits = models.Produit.query.all()
    dict_produits = {}
    for produit in liste_produits:
        dict_produits[produit.IDproduit] = produit.nom

    # Importation des locations existantes
    liste_locations = models.Location.query.filter(models.Location.date_debut <= end, models.Location.date_fin >= start).all()

    # Importation des réservations
    actions = models.Action.query.filter_by(categorie="locations", IDfamille=current_user.IDfamille, etat="attente").order_by(models.Action.horodatage).all()
    if actions != None :
        dict_reservations = {}
        for action in actions :
            liste_reservations = models.Reservation_location.query.filter_by(IDaction=action.IDaction).all()
            for reservation in liste_reservations:
                dict_reservations[str(reservation.IDlocation)] = reservation
    else :
        dict_reservations = None

    # Récupération des noms des autres loueurs
    dict_loueurs = {}
    if dict_parametres.get("LOCATIONS_AFFICHER_AUTRES_LOUEURS", False) == 'True':
        dict_loueurs = {user.IDfamille: utils.CallFonction("DecrypteChaine", user.nom) for user in models.User.query.filter(models.User.IDfamille.in_([location.IDfamille for location in liste_locations])).all()}

    # Ajout des locations existantes
    liste_events = []
    for location in liste_locations:
        dictEvent = {
            "allDay": "",
            "title": dict_produits[location.IDproduit],
            "id": str(location.IDlocation),
            "start": str(location.date_debut),
            "end": str(location.date_fin),
            "resourceId": str(location.IDproduit),
            'overlap': False,
            'color': "green",
            "partage": location.partage,
            "description": location.description,
        }

        # Si afficher autres loueurs
        if location.IDfamille in dict_loueurs and location.IDfamille != idfamille:
            dictEvent["title"] = dict_loueurs[location.IDfamille] + " : " + dictEvent["title"]

        # Si description existante
        if location.description:
            dictEvent["title"] += " - " + location.description

        # Si la location a déjà commencé, on empêche la modification
        if location.date_debut <= datetime.datetime.now():
            dictEvent["editable"] = False

        # Affichage des locations des autres usagers
        if location.IDfamille != idfamille:
            dictEvent["editable"] = False
            dictEvent["backgroundColor"] = "#f29da6"
            if dict_parametres.get("LOCATIONS_AFFICHER_AUTRES_LOUEURS", False) != 'True':
                dictEvent["rendering"] = 'background'

        valide = True
        if str(location.IDlocation) in dict_reservations:
            reservation = dict_reservations[str(location.IDlocation)]
            if reservation == 0:
                valide = False
            else:
                dictEvent["start"] = str(reservation.date_debut)
                dictEvent["end"] = str(reservation.date_fin)
                dictEvent["resourceId"] = str(reservation.IDproduit)

        if valide:
            liste_events.append(dictEvent)

    # Ajout des nouvelles réservations en attente de validation
    for id, reservation in dict_reservations.items():
        if "-" in id and reservation.etat != "supprimer":
            dictEvent = {
                "allDay": "",
                "title": dict_produits[reservation.IDproduit],
                "id": str(reservation.IDlocation),
                "start": str(reservation.date_debut),
                "end": str(reservation.date_fin),
                "resourceId": str(reservation.IDproduit),
                "overlap": False,
                "color": "orange",
                "partage": reservation.partage,
                "description": reservation.description,
            }
            if reservation.description:
                dictEvent["title"] += " - " + reservation.description
            liste_events.append(dictEvent)

    return jsonify(liste_events)


@app.route('/detail_envoi_locations', methods=['POST'])
@login_required
def detail_envoi_locations():
    if current_user.role != "famille":
        return redirect(url_for('logout'))

    dict_modifications = request.form.get("dict_modifications", "", type=str)

    try:
        liste_modifications = []
        for id_event, dict_event in json.loads(dict_modifications).items():
            liste_modifications.append({
                "etat": dict_event["etat"],
                "title": dict_event["event"]["title"],
                "start": datetime.datetime.strptime(dict_event["event"]["start"], '%Y-%m-%d %H:%M:%S'),
                "end": datetime.datetime.strptime(dict_event["event"]["end"], '%Y-%m-%d %H:%M:%S'),
                "resourceId": dict_event["event"]["resourceId"],
                "nom_ressource": dict_event["event"]["nom_ressource"],
                "id": dict_event["event"]["id"],
                "partage": dict_event["event"]["partage"],
            })

        liste_modifications = sorted(liste_modifications, key=itemgetter('start'))

        liste_lignes = []
        for dict_event in liste_modifications:
            if dict_event["etat"] == "ajouter":
                ligne = u"- Ajout"
            elif dict_event["etat"] == "modifier":
                ligne = u"- Modification"
            else:
                ligne = u"- Suppression"

            start = dict_event["start"].strftime("%d/%m/%Y-%Hh%M")
            end = dict_event["end"].strftime("%d/%m/%Y-%Hh%M")
            nom_ressource = dict_event["nom_ressource"]
            ligne += u" du %s au %s : %s\n" % (start, end, nom_ressource)
            liste_lignes.append(ligne)

        if len(liste_lignes) > 0:
            detail = "".join(liste_lignes)
        else:
            detail = u"Aucune modification demandée."

        return jsonify(success=1, detail=detail)
    except Exception as erreur:
        return jsonify(success=0, error_msg=str(erreur))


@app.route('/envoyer_locations', methods=['POST'])
@login_required
def envoyer_locations():
    if current_user.role != "famille":
        return redirect(url_for('logout'))

    dict_modifications = request.form.get("dict_modifications", "", type=str)
    commentaire = request.form.get("commentaire", None, type=six.text_type)

    liste_modifications = []
    liste_dates = []
    nbre_ajouts, nbre_modifications, nbre_suppressions = 0, 0, 0
    for id_event, dict_event in json.loads(dict_modifications).items():
        start = datetime.datetime.strptime(dict_event["event"]["start"], '%Y-%m-%d %H:%M:%S')
        end = datetime.datetime.strptime(dict_event["event"]["end"], '%Y-%m-%d %H:%M:%S')
        liste_modifications.append({
            "etat": dict_event["etat"],
            "title": dict_event["event"]["title"],
            "debut": start,
            "fin": end,
            "IDproduit": int(dict_event["event"]["resourceId"]),
            "nom_produit": dict_event["event"]["nom_ressource"],
            "id": dict_event["event"]["id"],
            "partage": dict_event["event"]["partage"],
            "description": dict_event["event"]["description"],
        })
        liste_dates.append(start)
        liste_dates.append(end)
        if dict_event["etat"] == "ajouter": nbre_ajouts += 1
        if dict_event["etat"] == "modifier": nbre_modifications += 1
        if dict_event["etat"] == "supprimer": nbre_suppressions += 1

    liste_dates.sort()

    # Si aucune réservation
    if len(liste_modifications) == 0:
        # Retourne un message d'erreur si aucune modification par rapport aux réservations initiales
        return jsonify(success=0, error_msg=u"Vous n'avez effectué aucune modification dans vos réservations !")

    try:

        # Description
        temp = []
        if nbre_ajouts == 1: temp.append(u"1 ajout")
        if nbre_ajouts > 1: temp.append(u"%d ajouts" % nbre_ajouts)
        if nbre_modifications == 1: temp.append(u"1 modification")
        if nbre_modifications > 1: temp.append(u"%d modifications" % nbre_modifications)
        if nbre_suppressions == 1: temp.append(u"1 suppression")
        if nbre_suppressions > 1: temp.append(u"%d suppressions" % nbre_suppressions)
        txt_actions = utils.Convert_liste_to_texte_virgules(temp)

        description = u"Réservations de locations sur la période du %s au %s (%s)" % (min(liste_dates).strftime("%d/%m/%Y"), max(liste_dates).strftime("%d/%m/%Y"), txt_actions)

        # Enregistrement de l'action
        action = models.Action(IDfamille=current_user.IDfamille, categorie="locations", action="envoyer",
                               description=description, etat="attente", commentaire=commentaire, parametres=None)
        db.session.add(action)
        db.session.flush()

        # Enregistrement des réservations
        for dict_event in liste_modifications:
            reservation = models.Reservation_location(IDlocation=str(dict_event["id"]), date_debut=dict_event["debut"], date_fin=dict_event["fin"],
                                                      IDproduit=dict_event["IDproduit"], IDaction=action.IDaction, etat=dict_event["etat"], partage=dict_event["partage"],
                                                      description=dict_event["description"])
            db.session.add(reservation)

        db.session.commit()

        flash(u"Votre demande de réservations a bien été enregistrée")
        app.logger.debug("Demande de locations (%s): famille id(%s) liste_reservations: %s", current_user.identifiant, current_user.IDfamille, liste_modifications)
        return jsonify(success=1)

    except Exception as erreur:
        app.logger.debug("[ERREUR] Demande de locations (%s): famille id(%s)", current_user.identifiant, current_user.IDfamille)
        app.logger.debug(erreur)
        return jsonify(success=0, error_msg=str(erreur))




# -----------------------------------------------------------------------

@app.route('/supprimer_demande')
@login_required
def supprimer_demande():
    if current_user.role != "famille" :
        return redirect(url_for('logout'))

    try:
        IDaction = request.args.get("idaction", 0, type=int)

        # Suppression de l'action dans la db
        action = models.Action.query.filter_by(IDaction=IDaction).first()
        action.etat = "suppression"
        db.session.commit()

        # Si c'est une pièce, on supprime la pièce jointe
        if action.categorie == "pieces":
            for parametre in action.parametres.split("#"):
                key, valeur = parametre.split("=")
                if key == "chemin" and os.path.isfile(valeur):
                    os.remove(valeur)
        
        flash(u"Votre suppression a bien été enregistrée")
        app.logger.debug("SUPPRESSION DEMANDE (%s): famille id(%s) - demande(%s)", current_user.identifiant, current_user.IDfamille, IDaction)
        return jsonify(success=1)
    except Exception as erreur:
        app.logger.debug("[ERREUR] SUPPRESSION DEMANDE (%s): famille id(%s) - demande(%s)", current_user.identifiant, current_user.IDfamille, IDaction)
        return jsonify(success=0, error_msg=str(erreur))

        

        
# ------------------------- RESERVATIONS ---------------------------------- 
 
@app.route('/reservations')
@login_required
def reservations():
    if current_user.role != "famille" :
        return redirect(url_for('logout'))

    # Récupération des individus
    liste_individus_temp = models.Individu.query.filter_by(IDfamille=current_user.IDfamille).order_by(models.Individu.prenom).all()

    # Récupération des inscriptions
    inscriptions = models.Inscription.query.filter_by(IDfamille=current_user.IDfamille).filter((models.Inscription.date_desinscription == None) | (models.Inscription.date_desinscription > datetime.date.today())).all()
    dict_inscriptions = {}
    liste_activites = []
    for inscription in inscriptions:
        dict_inscriptions.setdefault(inscription.IDindividu, [])
        dict_inscriptions[inscription.IDindividu].append(inscription)
        if inscription.IDactivite not in liste_activites:
            liste_activites.append(inscription.IDactivite)

    # Récupération des périodes
    liste_periodes = models.Periode.query.filter(models.Periode.IDactivite.in_(liste_activites)).all()
    dict_periodes = {}
    for periode in liste_periodes:
        dict_periodes.setdefault(periode.IDactivite, [])
        if periode.Is_active_today():
            dict_periodes[periode.IDactivite].append(periode)

    liste_individus = []
    for individu in liste_individus_temp:
        inscriptions = dict_inscriptions.get(individu.IDindividu, [])
        if inscriptions:
            # Attribution d'une couleur
            index_couleur = random.randint(0, len(COULEURS) - 1)
            individu.index_couleur = index_couleur
            individu.couleur = COULEURS[index_couleur]
            individu.inscriptions_actives = [inscription for inscription in inscriptions if len(dict_periodes.get(inscription.IDactivite, []))]
            liste_individus.append(individu)

    # Recherche l'historique des demandes liées aux réservations
    dict_parametres = models.GetDictParametres()
    historique = GetHistorique(IDfamille=current_user.IDfamille, categorie="reservations", dict_parametres=dict_parametres)
    
    app.logger.debug("Page RESERVATIONS (%s): famille id(%s) - liste_individus: %s", current_user.identifiant, current_user.IDfamille, liste_individus)
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
    inscription = models.Inscription.query.filter_by(IDfamille=current_user.IDfamille, IDindividu=IDindividu, IDactivite=periode.IDactivite).first()
    if inscription == None :
        app.logger.warning(u"IDfamille %d : Tentative d'accéder à l'individu %s dans les réservations." % (current_user.IDfamille, IDindividu))
        flash(u"Vous n'êtes pas autorisé à accéder au planning de l'individu demandé !")
        return None
    
    # Unités
    liste_unites = models.Unite.query.filter_by(IDactivite=periode.IDactivite).order_by(models.Unite.ordre).all()
    
    # Ouvertures
    liste_ouvertures = models.Ouverture.query.filter(models.Ouverture.IDgroupe == inscription.IDgroupe, models.Ouverture.date >= periode.date_debut, models.Ouverture.date <= periode.date_fin).all()

    # Evenements
    # liste_evenements = models.Evenement.query.filter(models.Evenement.IDgroupe == inscription.IDgroupe, models.Evenement.date >= periode.date_debut, models.Evenement.date <= periode.date_fin).all()
    # dict_evenements = {}
    # for evenement in liste_evenements :
    #     if not dict_evenements.has_key(evenement.date):
    #         dict_evenements[evenement.date] = {}
    #     if not dict_evenements[evenement.date].has_key(evenement.IDunite):
    #         dict_evenements[evenement.date][evenement.IDunite] = []
    #     dict_evenements[evenement.date][evenement.IDunite].append(evenement)

    # Fériés
    liste_feries = models.Ferie.query.all()
    
    # Dates
    liste_dates = []
    dict_ouvertures = {}
    for ouverture in liste_ouvertures :
        
        # Mémorisation de la date
        if ouverture.date not in liste_dates :
            liste_dates.append(ouverture.date)
        
        # Mémorisation de l'ouverture des unités
        if ouverture.date not in dict_ouvertures :
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
                if reservation.date not in dict_reservations :
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
                    if date not in dict_reservations :
                        dict_reservations[date] = {}
                    dict_reservations[date][IDunite] = 1
            
            # Décoche les anciennes réservations
            for date, dict_unites_temp in dict_reservations.items() :
                for IDunite, etat in dict_unites_temp.items() :
                    if (date, IDunite) not in liste_coches :
                        dict_reservations[date][IDunite] = 0

    # Consommations
    liste_consommations = models.Consommation.query.filter_by(IDinscription=inscription.IDinscription).all()
    dict_consommations = {}
    for consommation in liste_consommations :
        if consommation.date not in dict_consommations :
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
                    if date in dict_consommations :
                        if IDunite_conso in dict_consommations[date] :
                            liste_etats.append(dict_consommations[date][IDunite_conso])
                    
                if len(liste_etats) == nbre_unites_principales :
                    if date not in dict_conso_par_unite_resa :
                        dict_conso_par_unite_resa[date] = {}
                    
                    if "attente" in liste_etats :
                        dict_conso_par_unite_resa[date][unite] = "attente"
                    elif "present" in liste_etats :
                        dict_conso_par_unite_resa[date][unite] = "present"
                    elif "absenti" in liste_etats :
                        dict_conso_par_unite_resa[date][unite] = "absenti"
                    elif "absentj" in liste_etats :
                        dict_conso_par_unite_resa[date][unite] = "absentj"
                    elif "refus" in liste_etats :
                        dict_conso_par_unite_resa[date][unite] = "refus"
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
        "liste_feries" : liste_feries,
        "dict_consommations" : dict_consommations,
        "dict_conso_par_unite_resa" : dict_conso_par_unite_resa,
        "dict_reservations" : dict_reservations,
        "couleur" : couleur,
        "liste_reservations_initiale" : liste_reservations_initiale,
        }
    
    app.logger.debug("Page PLANNING (%s): famille id(%s) Individu id(%s) pour la periode id(%s)", current_user.identifiant, current_user.IDfamille, IDindividu, IDperiode)
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
    if current_user.role != "famille" :
        return redirect(url_for('logout'))

    IDindividu = request.args.get("IDindividu", None, type=int)
    IDperiode = request.args.get("IDperiode", None, type=int)
    index_couleur = request.args.get("index_couleur", None, type=int)
    
    dict_planning = Get_dict_planning(IDindividu, IDperiode, index_couleur)
    if dict_planning == None :
        return redirect(url_for('reservations'))
    
    dict_parametres = models.GetDictParametres()
    return render_template('planning.html', active_page="reservations", dict_planning=dict_planning, dict_parametres=dict_parametres)

    
@app.route('/imprimer_reservations')
@login_required
def imprimer_reservations():
    if current_user.role != "famille" :
        return redirect(url_for('logout'))

    IDindividu = request.args.get("IDindividu", None, type=int)
    IDperiode = request.args.get("IDperiode", None, type=int)
    resultats = request.args.get("resultats", "", type=str)
    
    dict_planning = Get_dict_planning(IDindividu=IDindividu, IDperiode=IDperiode, coches=resultats)
    if dict_planning == None :
        return redirect(url_for('reservations'))
    
    dict_parametres = models.GetDictParametres()
    return render_template('imprimer_reservations.html', dict_planning=dict_planning, dict_parametres=dict_parametres)
    
              
@app.route('/envoyer_reservations', methods=['POST'])
@login_required
def envoyer_reservations():
    if current_user.role != "famille" :
        return redirect(url_for('logout'))

    try:
        # Récupération de la liste des cases cochées
        resultats = request.form.get("resultats", "", type=str)
        IDinscription = request.form.get("IDinscription", None, type=int)
        IDperiode = request.form.get("IDperiode", None, type=int)
        IDactivite = request.form.get("IDactivite", None, type=int)
        activite_nom = request.form.get("activite_nom", None, type=six.text_type)
        IDindividu = request.form.get("IDindividu", None, type=int)
        individu_prenom = request.form.get("individu_prenom", None, type=six.text_type)
        date_debut_periode = request.form.get("date_debut_periode", "", type=str)
        date_fin_periode = request.form.get("date_fin_periode", "", type=str)
        commentaire = request.form.get("commentaire", None, type=six.text_type)
        liste_reservations_initiale = request.form.get("liste_reservations_initiale", "", type=str)
        
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
            
    except Exception as erreur:
        app.logger.debug("[ERREUR] Demande de reservations (%s): famille id(%s)", current_user.identifiant, current_user.IDfamille)
        app.logger.debug(erreur)
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

    
    
        
@app.route('/detail_envoi_reservations', methods=['POST'])
@login_required
def detail_envoi_reservations():
    if current_user.role != "famille" :
        return redirect(url_for('logout'))

    try:
        # Détail des réservations
        IDactivite = request.form.get("IDactivite", None, type=int)
        resultats = request.form.get("resultats", "", type=str)
        liste_reservations_initiale = request.form.get("liste_reservations_initiale", "", type=str)
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
    except Exception as erreur:
        return jsonify(success=0, error_msg=str(erreur))
   
   

   
# ------------------------- RENSEIGNEMENTS ---------------------------------- 

@app.route('/renseignements')
@login_required
def renseignements():
    if current_user.role != "famille" :
        return redirect(url_for('logout'))

    # Récupération des renseignements modifiés
    dict_renseignements = GetDictRenseignements(IDfamille=current_user.IDfamille)
    
    # Récupération des individus
    liste_individus_temp = models.Individu.query.filter_by(IDfamille=current_user.IDfamille).order_by(models.Individu.nom).all()
    
    liste_individus = []
    for individu in liste_individus_temp :
        # Attribution d'une couleur
        index_couleur = random.randint(0, len(COULEURS)-1)
        individu.index_couleur = index_couleur
        individu.couleur = COULEURS[index_couleur]
        liste_individus.append(individu)
        
        individu.renseignements = dict_renseignements[individu.IDindividu]
        
    # Recherche l'historique des demandes liées aux renseignements
    dict_parametres = models.GetDictParametres()
    historique = GetHistorique(IDfamille=current_user.IDfamille, categorie="renseignements", dict_parametres=dict_parametres)

    if dict_parametres["RENSEIGNEMENTS_AFFICHER"] == 'False' :
        return redirect(url_for('accueil'))
    
    app.logger.debug("Page RENSEIGNEMENTS (%s): famille id(%s) liste_individus: %s", current_user.identifiant, current_user.IDfamille, liste_individus)
    return render_template('renseignements.html', active_page="renseignements", \
                            liste_individus = liste_individus, \
                            historique = historique, dict_parametres=dict_parametres)

                            
                            
def GetDictRenseignements(IDfamille=None, IDindividu=None):
    """ Importation des renseignements en cours """
    # Importation des valeurs de la table individus
    if IDfamille != None :
        liste_individus = models.Individu.query.filter_by(IDfamille=IDfamille).all()
    else :
        liste_individus = [models.Individu.query.filter_by(IDindividu=IDindividu).first(),]
    
    dict_valeurs = {"liste_choix_adresses" : []}
    liste_choix_adresses = []
    for individu in liste_individus :
        if (IDindividu in dict_valeurs) == False :
            dict_valeurs[individu.IDindividu] = {"individu" : individu, "champs_modifies" : []}
            
        for champ in CHAMPS_RENSEIGNEMENTS :
            valeur = getattr(individu, champ)
            valeur = utils.CallFonction("DecrypteChaine", valeur)
            if "date" in champ :
                if isinstance(valeur, six.text_type) or isinstance(valeur, str):
                    valeur = utils.CallFonction("DateEngEnDD", valeur)
                valeur = utils.CallFonction("DateDDEnFr", valeur)
            elif "adresse_auto" in champ :
                if valeur == None :
                    valeur = 0
                else :
                    valeur = int(valeur)
            else :
                valeur = utils.CallFonction("ConvertToUnicode", valeur)
            dict_valeurs[individu.IDindividu][champ] = valeur
            
            
    # Récupération des valeurs en cours (initiales + modifiées)
    if IDfamille != None :
        actions = models.Action.query.filter_by(categorie="renseignements", IDfamille=current_user.IDfamille, etat="attente").order_by(models.Action.horodatage).all()   
    else :
        actions = models.Action.query.filter_by(categorie="renseignements", IDfamille=current_user.IDfamille, IDindividu=IDindividu, etat="attente").order_by(models.Action.horodatage).all()   
    for action in actions :
        for renseignement in action.renseignements :
            valeur = utils.CallFonction("DecrypteChaine", renseignement.valeur)
            if renseignement.champ == "adresse_auto" and valeur == None :
                valeur = 0
            dict_valeurs[action.IDindividu][renseignement.champ] = valeur
            dict_valeurs[action.IDindividu]["champs_modifies"].append(renseignement.champ)
    
    for IDindividu, dictChamps in dict_valeurs.items() :
        if type(dictChamps) == dict :
            adresse_rattachee = False
            if dictChamps["adresse_auto"] != 0 :
                IDindividuTemp = int(dictChamps["adresse_auto"])
                if IDindividuTemp in dict_valeurs:
                    rue =  dict_valeurs[IDindividuTemp]["rue_resid"]
                    cp = dict_valeurs[IDindividuTemp]["cp_resid"]
                    ville = dict_valeurs[IDindividuTemp]["ville_resid"]
                    prenom = dict_valeurs[IDindividuTemp]["prenom"]
                    dict_valeurs[IDindividu]["adresse"] = u"%s %s %s (L'adresse de %s)" % (rue, cp, ville, prenom)
                    adresse_rattachee = True

            if adresse_rattachee == False :
                rue = dict_valeurs[IDindividu]["rue_resid"]
                cp = dict_valeurs[IDindividu]["cp_resid"]
                ville = dict_valeurs[IDindividu]["ville_resid"]
                dict_valeurs[IDindividu]["adresse"] = u"%s %s %s" % (rue, cp, ville)
            
                dict_valeurs["liste_choix_adresses"].append((IDindividu, u"La même adresse que %s" % dictChamps["prenom"])) 
            
    return dict_valeurs
    

@app.route('/modifier_renseignements')
@login_required
def modifier_renseignements():
    if current_user.role != "famille" :
        return redirect(url_for('logout'))

    IDindividu = request.args.get("IDindividu", None, type=int)    
    dict_parametres = models.GetDictParametres()
    
    # Importation des renseignements en cours
    dict_renseignements = GetDictRenseignements(IDfamille=current_user.IDfamille)
    
    # Remplissage du formulaire
    form = forms.Renseignements()   
    form.idindividu.data = IDindividu
    
    # Remplissage du champ adresse_auto
    liste_adresses_auto = [(0, u"L'adresse suivante"),]
    for IDindividuTemp, label in dict_renseignements["liste_choix_adresses"] :
        if IDindividu != IDindividuTemp :
            liste_adresses_auto.append((IDindividuTemp, label))
    form.adresse_auto.choices = liste_adresses_auto
    
    # Attibution des valeurs
    for champ in CHAMPS_RENSEIGNEMENTS :
        valeur = dict_renseignements[IDindividu][champ]
        getattr(form, champ).data = valeur
        
    return render_template('modifier_renseignements.html', active_page="renseignements", individu=dict_renseignements[IDindividu]["individu"], dict_parametres=dict_parametres, form=form)

    
    
@app.route('/envoyer_modification_renseignements', methods=['POST'])
@login_required
def envoyer_modification_renseignements():
    if current_user.role != "famille" :
        return redirect(url_for('logout'))

    dict_parametres = models.GetDictParametres()

    try:
        # Récupération du form rempli
        form = forms.Renseignements(request.form)   
        
        # Récupération des valeurs
        IDindividu = int(form.idindividu.data)
        
        # Récupération des valeurs initiales
        dict_renseignements = GetDictRenseignements(IDfamille=current_user.IDfamille)
        individu = dict_renseignements[IDindividu]["individu"]
        
        # Validation des nouvelles valeurs
        date_naiss = form.date_naiss.data
        if date_naiss != "" :
            try :
                date_naiss = datetime.datetime.strptime(date_naiss, '%d/%m/%Y')
            except :
                return jsonify(success=0, error_msg=u"La date de naissance saisie ne semble pas correcte !")
        
        if "_" in form.cp_naiss.data :
            return jsonify(success=0, error_msg=u"Le code postal de naissance saisi ne semble pas correct !")

        if "_" in form.cp_resid.data :
            return jsonify(success=0, error_msg=u"Le code postal de résidence saisi ne semble pas correct !")

        if "_" in form.tel_domicile.data :
            return jsonify(success=0, error_msg=u"Le téléphone du domicile saisi ne semble pas correct !")

        if "_" in form.tel_mobile.data :
            return jsonify(success=0, error_msg=u"Le téléphone mobile saisi ne semble pas correct !")

        if "_" in form.travail_tel.data :
            return jsonify(success=0, error_msg=u"Le téléphone professionnel saisi ne semble pas correct !")

        if len(form.mail.data) > 0 and u"@" not in form.mail.data :
            return jsonify(success=0, error_msg=u"L'Email saisi ne semble pas correct !")

        if len(form.travail_mail.data) > 0 and u"@" not in form.travail_mail.data :
            return jsonify(success=0, error_msg=u"L'Email professionnel saisi ne semble pas correct !")

        
        # Recherche les champs modifiés
        dict_champs_modifies = {}
        for champ in CHAMPS_RENSEIGNEMENTS :
            nouvelle_valeur = getattr(form, champ).data
            ancienne_valeur = dict_renseignements[IDindividu][champ]
            champ_desactive = utils.IsRenseignementDisabled(dict_parametres, individu, champ=champ)
            if champ_desactive == False and nouvelle_valeur != ancienne_valeur :
                dict_champs_modifies[champ] = nouvelle_valeur
        
        # Description
        nbre_champs_modifies = len(dict_champs_modifies)
        if nbre_champs_modifies == 0 :
            return jsonify(success=0, error_msg=u"Vous n'avez modifié aucun renseignement !")
        elif nbre_champs_modifies == 1 :
            description = u"Modification de 1 renseignement pour %s" % individu.GetRenseignement("prenom")
        else :
            description = u"Modification de %d renseignements pour %s" % (nbre_champs_modifies, individu.GetRenseignement("prenom"))
        
        # Enregistrement de l'action
        action = models.Action(IDfamille=current_user.IDfamille, IDindividu=IDindividu, categorie="renseignements", action="envoyer", description=description, etat="attente", parametres=None)
        db.session.add(action)
        db.session.flush()
        
        # Enregistrement des renseignements
        for champ, valeur in dict_champs_modifies.items():
            if champ == "adresse_auto" and valeur == 0 :
                valeur = None
            valeur = utils.CallFonction("CrypteChaine", valeur)
            renseignement = models.Renseignement(champ=champ, valeur=valeur, IDaction=action.IDaction)
            db.session.add(renseignement)

        db.session.commit()

            
        flash(u"Votre demande de modification a bien été enregistrée")
        return jsonify(success=1)
        
    except Exception as erreur:
        return jsonify(success=0, error_msg=str(erreur))

        
        
        
# ------------------------- INSCRIPTIONS ---------------------------------- 

@app.route('/inscriptions')
@login_required
def inscriptions():
    if current_user.role != "famille" :
        return redirect(url_for('logout'))

    # Récupération des individus
    liste_individus_temp = models.Individu.query.filter_by(IDfamille=current_user.IDfamille).order_by(models.Individu.prenom).all()
    
    liste_individus = []
    for individu in liste_individus_temp :
        if True :#len(individu.get_inscriptions()) > 0 :
            # Attribution d'une couleur
            index_couleur = random.randint(0, len(COULEURS)-1)
            individu.index_couleur = index_couleur
            individu.couleur = COULEURS[index_couleur]
            individu.inscriptions = individu.get_inscriptions()
            liste_individus.append(individu)
    
    # Liste des activités
    liste_activites = models.Activite.query.filter_by().order_by(models.Activite.nom).all()
    liste_groupes = models.Groupe.query.filter_by().order_by(models.Groupe.ordre).all()
    dict_groupes = {}
    for groupe in liste_groupes :
        if groupe.IDactivite not in dict_groupes :
            dict_groupes[groupe.IDactivite] = []
        dict_groupes[groupe.IDactivite].append(groupe)
    
    # Recherche l'historique des demandes liées aux réservations
    dict_parametres = models.GetDictParametres()
    historique = GetHistorique(IDfamille=current_user.IDfamille, categorie="inscriptions", dict_parametres=dict_parametres)

    app.logger.debug("Page INSCRIPTIONS (%s): famille id(%s) liste_individus: %s", current_user.identifiant, current_user.IDfamille, liste_individus)
    return render_template('inscriptions.html', active_page="inscriptions", \
                            liste_individus = liste_individus, \
                            liste_activites = liste_activites, \
                            dict_groupes = dict_groupes, \
                            historique = historique, dict_parametres=dict_parametres)

                            
@app.route('/envoyer_demande_inscription')
@login_required
def envoyer_demande_inscription():
    if current_user.role != "famille" :
        return redirect(url_for('logout'))

    try:
        IDindividu = request.args.get("idindividu", 0, type=int)
        activite = request.args.get("activite", "", type=str)
        if activite == "" :
            return jsonify(success=0, error_msg=u"Aucune activité n'a été sélectionnée")
        IDactivite = int(activite.split("-")[0])
        IDgroupe = int(activite.split("-")[1])
        commentaire = request.args.get("commentaire", "", type=six.text_type)
        
        # Vérifie que l'individu n'est pas déjà inscrit
        inscription = models.Inscription.query.filter_by(IDindividu=IDindividu, IDactivite=IDactivite).first()
        if inscription != None :
            return jsonify(success=0, error_msg=u"%s est déjà inscrit(e) à l'activité sélectionnée !" % inscription.get_individu().GetRenseignement("prenom"))
                    
        # Enregistrement
        individu = models.Individu.query.filter_by(IDindividu=IDindividu).first()
        activite = models.Activite.query.filter_by(IDactivite=IDactivite).first()
        description = u"Inscription de %s à l'activité %s" % (individu.GetRenseignement("prenom"), activite.nom)
        parametres = u"IDactivite=%d#IDgroupe=%d" % (IDactivite, IDgroupe)

        m = models.Action(IDfamille=current_user.IDfamille, IDindividu=IDindividu, categorie="inscriptions", action="inscrire", description=description, etat="attente", commentaire=commentaire, parametres=parametres)
        db.session.add(m)
        db.session.commit()
        
        flash(u"Votre demande d'inscription à une activité a bien été enregistrée")
        return jsonify(success=1)
    except Exception as erreur:
        return jsonify(success=0, error_msg=str(erreur))

   

# ------------------------- CONTACT ---------------------------------- 

@app.route('/contact')
@login_required
def contact():
    if current_user.role != "famille" :
        return redirect(url_for('logout'))

    dict_parametres = models.GetDictParametres()
    return render_template('contact.html', active_page="contact", dict_parametres=dict_parametres)


# ------------------------- MENTIONS ---------------------------------- 

@app.route('/mentions')
@login_required
def mentions():
    if current_user.role != "famille" :
        return redirect(url_for('logout'))

    dict_parametres = models.GetDictParametres()
    conditions_utilisation = models.Element.query.filter_by(categorie="conditions_utilisation").first()
    if conditions_utilisation == None:
        conditions_utilisation = ""
    else:
        conditions_utilisation = utils.FusionDonneesOrganisateur(conditions_utilisation.texte_html, dict_parametres)
    return render_template('mentions.html', active_page="mentions", dict_parametres=dict_parametres, conditions_utilisation=conditions_utilisation)
        
      
# ------------------------- AIDE ---------------------------------- 

@app.route('/aide')
@login_required
def aide():
    if current_user.role != "famille" :
        return redirect(url_for('logout'))

    dict_parametres = models.GetDictParametres()
    return render_template('aide.html', active_page="aide", dict_parametres=dict_parametres)


# ------------------------- COMPTE ----------------------------------


@app.route('/compte', methods=['GET', 'POST'])
@login_required
def compte():
    # Si l'utilisateur n'est pas connecté, on le renvoie vers l'accueil
    if not current_user.is_authenticated :
        return redirect(url_for('login'))

    # Génération du form de login
    form = forms.ChangePassword()

    # Affiche la page de changement
    if request.method == 'GET':
        dict_parametres = models.GetDictParametres()
        return render_template('compte.html', active_page="compte", form=form, dict_parametres=dict_parametres)

    # Validation du form avec Flask-WTF
    if form.validate_on_submit():
        if ValiderModificationPassword(form=form, valider_conditions=False) != True :
            return redirect(url_for("compte"))

    # Renvoie vers l'accueil
    flash(u"Votre nouveau mot de passe a bien été enregistré", 'error')
    return redirect(url_for('compte'))


@app.route('/page_perso/<int:num_page>')
@login_required
def page_perso(num_page=0):
    # Vérifie que la page existe bien
    if ("page_perso%d" % num_page in g.dict_pages) == False :
        return redirect(url_for('accueil'))

    # Importation des blocs et des éléments de blocs
    liste_blocs = models.Bloc.query.filter_by(IDpage=num_page).order_by(models.Bloc.ordre).all()
    listeIDblocs = [bloc.IDbloc for bloc in liste_blocs]
    liste_elements = models.Element.query.filter(models.Element.IDbloc.in_(listeIDblocs)).order_by(models.Element.ordre).all()
    dict_elements = {}
    for element in liste_elements :
        if (element.IDbloc in dict_elements) == False :
            dict_elements[element.IDbloc] = []
        dict_elements[element.IDbloc].append(element)

    # Création de la page
    dict_parametres = models.GetDictParametres()
    return render_template('page_perso.html', active_page="page_perso%d" % num_page, dict_parametres=dict_parametres, liste_blocs=liste_blocs, dict_elements=dict_elements)

@app.route('/get_events_calendrier/<int:idbloc>')
@login_required
def get_events_calendrier(idbloc=None):
    try :
        start = request.args['start']
        end = request.args['end']
        start = datetime.datetime.strptime("%s 00:00" % start, '%Y-%m-%d %H:%M')
        end = datetime.datetime.strptime("%s 23:59" % end, '%Y-%m-%d %H:%M')
        liste_elements = models.Element.query.filter(models.Element.categorie=="bloc_calendrier", models.Element.IDbloc==idbloc, models.Element.date_debut <= end, models.Element.date_fin >= start).all()
    except :
        liste_elements = []

    liste_events = []
    for element in liste_elements :
        description = ""
        couleur = "#3c8dbc"
        try :
            for parametre in element.parametres.split("###"):
                nom, valeur = parametre.split(":::")
                if nom == "description":
                    description = valeur
                if nom == "couleur":
                    couleur = valeur
        except:
            pass

        dictEvent = {
            "allDay": "",
            "title": element.titre,
            "id": str(element.IDelement),
            "start": str(element.date_debut),
            "end": str(element.date_fin),
            "description": description,
            "backgroundColor": couleur,
            "borderColor": couleur,
        }
        liste_events.append(dictEvent)

    return jsonify(liste_events)






@app.route('/detail_demande')
@login_required
def detail_demande():
    if current_user.role != "famille" :
        return redirect(url_for('logout'))

    try:
        # Détail des réservations
        IDaction = request.args.get("idaction", 0, type=int)
        categorie = request.args.get("categorie", "", type=str)
        detail = ""
        
        # Détail des réservations
        if categorie == "reservations" :
        
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
        
        # Détail des renseignements
        if categorie == "renseignements" :
            
            liste_renseignements = models.Renseignement.query.filter_by(IDaction=IDaction).all()

            liste_lignes = []
            for renseignement in liste_renseignements :
                valeur = utils.CallFonction("DecrypteChaine", renseignement.valeur)
            
                label = None
                if renseignement.champ in DICT_RENSEIGNEMENTS :
                    label = u"- %s : %s\n" % (DICT_RENSEIGNEMENTS[renseignement.champ], valeur)
                    
                if renseignement.champ == "adresse_auto" and renseignement.valeur != None :
                    individuTemp = models.Individu.query.filter_by(IDindividu=int(valeur)).first()
                    label = u"- Adresse associée à celle de %s\n" % individuTemp.GetRenseignement("prenom")
                    
                if label != None :
                    liste_lignes.append(label)
                    
            detail = "".join(liste_lignes)

        # Détail des locations
        if categorie == "locations":

            liste_locations = models.Reservation_location.query.filter_by(IDaction=IDaction).order_by(models.Reservation_location.date_debut, models.Reservation_location.etat).all()

            liste_produits = models.Produit.query.all()
            dict_produits = {}
            for produit in liste_produits:
                dict_produits[produit.IDproduit] = produit.nom

            liste_lignes = []
            for location in liste_locations:
                if location.etat == "supprimer":
                    ligne = u"- Suppression"
                elif location.etat == "modifier":
                    ligne = u"- Modification"
                else:
                    ligne = u"- Ajout"
                start = location.date_debut.strftime("%d/%m/%Y-%Hh%M")
                end = location.date_fin.strftime("%d/%m/%Y-%Hh%M")
                nom_ressource = dict_produits[location.IDproduit]
                ligne += u" du %s au %s : %s\n" % (start, end, nom_ressource)
                liste_lignes.append(ligne)

            detail = "".join(liste_lignes)

        return jsonify(success=1, detail=detail)
    except Exception as erreur:
        return jsonify(success=0, error_msg=str(erreur))


@app.route('/lost_password', methods=['GET', 'POST'])
def lost_password():
    # Si l'utilisateur est déjà connecté, on le renvoie vers l'accueil
    if current_user.is_authenticated or models.GetParametre(nom="MDP_AUTORISER_REINITIALISATION", defaut="False") == "False":
        return redirect(url_for('login'))

    # Génération du form
    # if app.config.get('RECAPTCHA_ACTIVATION') and app.config.get('RECAPTCHA_PUBLIC_KEY'):
    if app.config.get('CAPTCHA', 1) == 1:
        form = forms.LostPasswordWithCaptcha()
    else:
        form = forms.LostPassword()
    dict_parametres = models.GetDictParametres()

    # Affiche la page de login
    if request.method == 'GET':
        return render_template('lost_password.html', form=form, dict_parametres=dict_parametres)

    # Validation du form
    if form.validate_on_submit():

        app.logger.debug("Demande reinit password identifiant=%s email=%s", form.identifiant.data, form.email.data)

        # Vérification du captcha
        if hasattr(form, "captcha") and not captcha.validate():
            flash(u"Le code de sécurité n'a pas été correctement recopié", 'error')
            return redirect(url_for('lost_password'))

        # Recherche si l'identifiant est correct
        user = models.User.query.filter_by(identifiant=form.identifiant.data).first()
        if user == None :
            app.logger.debug("Demande reinit password identifiant=%s email=%s : Identifiant incorrect.", form.identifiant.data, form.email.data)
            flash(u"L'identifiant saisi est incorrect !", 'error')
            return redirect(url_for('lost_password'))
        identifiant = form.identifiant.data

        # Vérifie la saisie de l'email
        if re.match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$", form.email.data) == None:
            app.logger.debug("Demande reinit password identifiant=%s email=%s : Adresse email non valide.", form.identifiant.data, form.email.data)
            flash(u"L'adresse email saisie n'est pas valide !", 'error')
            return redirect(url_for('lost_password'))

        # Recherche si l'adresse email correspond à l'identifiant saisi
        email_destinataire = False
        if user.email != ("", None):
            emails = utils.CallFonction("DecrypteChaine", user.email)
            for email in emails.split(";"):
                if email == form.email.data:
                    email_destinataire = form.email.data

        if email_destinataire == False :
            app.logger.debug("Demande reinit password identifiant=%s email=%s : Adresse email inconnue.", form.identifiant.data, form.email.data)
            flash(u"L'adresse email saisie est inconnue !", 'error')
            return redirect(url_for('lost_password'))

        # Préparation du token et de l'url de reset
        ts = URLSafeTimedSerializer(app.config["SECRET_KEY"])
        token = ts.dumps(identifiant, salt='confirm-password-lost')
        confirm_url = url_for('reset_password', token=token, _external=True)

        # Envoi de l'email
        msg = Message(u"Réinitialisation du mot de passe", recipients=[email_destinataire,])
        msg.body = render_template("email/lost_password.txt", confirm_url=confirm_url, dict_parametres=dict_parametres)
        msg.html = render_template("email/lost_password.html", confirm_url=confirm_url, dict_parametres=dict_parametres)
        try :
            mail.send(msg)
        except Exception as err:
            app.logger.debug("Demande reinit password identifiant=%s email=%s : ERREUR dans l'envoi de l'email.", form.identifiant.data, form.email.data)
            app.logger.debug(err)
            flash(u"L'email n'a pas pu être envoyé. Merci de contacter l'administrateur du portail !", 'error')
            return redirect(url_for('login'))

        app.logger.debug("Demande reinit password identifiant=%s email=%s : Email envoye avec succes.", form.identifiant.data, form.email.data)
        flash(u"L'email de réinitialisation a bien été envoyé. Consultez votre messagerie dans quelques instants.", 'error')
        return redirect(url_for('login'))

    # Renvoie le formulaire
    if "recaptcha" in form.errors:
        flash(u"Vous devez cocher la case 'Je ne suis pas un robot'", 'error')
    return redirect(url_for('lost_password'))

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token=None):
    # Si la fonction Mot de passe oublié est désactivés
    if models.GetParametre(nom="MDP_AUTORISER_REINITIALISATION", defaut="False") == "False":
        return redirect(url_for('login'))

    try:
        ts = URLSafeTimedSerializer(app.config["SECRET_KEY"])
        identifiant = ts.loads(token, salt="confirm-password-lost", max_age=86400)
    except:
        app.logger.debug("Lien de reinitialisation du mot de passe errone ou expire.")
        flash(u"Le lien de réinitialisation est erroné ou a expiré !", 'error')
        return redirect(url_for('login'))

    # Génération du form de login
    form = forms.ResetPassword()

    # Affiche la page de changement
    if request.method == 'GET':
        dict_parametres = models.GetDictParametres()
        conditions_utilisation = models.Element.query.filter_by(categorie="conditions_utilisation").first()
        if conditions_utilisation == None :
            conditions_utilisation = ""
        else :
            conditions_utilisation = utils.FusionDonneesOrganisateur(conditions_utilisation.texte_html, dict_parametres)
        return render_template('reset_password.html', form=form, token=token, dict_parametres=dict_parametres, conditions_utilisation=conditions_utilisation)

    # Validation du form avec Flask-WTF
    if form.validate_on_submit():
        if identifiant != form.identifiant.data :
            app.logger.debug("Reset du mot de passe identifiant=%s : Identifiant incorrect.", form.identifiant.data)
            flash(u"L'identifiant saisi est incorrect !", 'error')
            return redirect(url_for('reset_password', token=token))

        user = models.User.query.filter_by(identifiant=identifiant).first()
        if user == None :
            app.logger.debug("Reset du mot de passe identifiant=%s : Identifiant incorrect.", form.identifiant.data)
            flash(u"L'identifiant saisi est incorrect !", 'error')
            return redirect(url_for('reset_password', token=token))

        if ValiderModificationPassword(form=form, user=user) != True :
            return redirect(url_for('reset_password', token=token))

        # Renvoie vers l'accueil
        app.logger.debug("Reset du mot de passe identifiant=%s : Nouveau mot de passe valide.", form.identifiant.data)
        flash(u"Votre nouveau mot de passe a bien été enregistré !")

    return redirect(url_for('accueil'))


# ------------------------------------------------------------------------------------------------------------------

def GetHistorique(IDfamille=None, categorie=None, dict_parametres=None):
    """ Historique : Récupération de la liste des dernières actions liées à une catégorie """
    """ Si categorie == None > Toutes les catégories sont affichées """
    # Récupération de la date de la dernière synchro
    derniere_synchro = None
    if dict_parametres and "derniere_synchro" in dict_parametres:
        derniere_synchro = datetime.datetime.strptime(dict_parametres.get("derniere_synchro"), "%Y%m%d%H%M%S%f")
    else:
        m = models.Parametre.query.filter_by(nom="derniere_synchro").first()
        if m != None:
            derniere_synchro = datetime.datetime.strptime(m.parametre, "%Y%m%d%H%M%S%f")

    # Récupération des actions
    historique_delai = int(models.GetParametre(nom="HISTORIQUE_DELAI", dict_parametres=dict_parametres, defaut=0))
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
        if horodatage not in dict_actions :
            dict_actions[horodatage] = []
        dict_actions[horodatage].append(action)
        
        if action.categorie == "reservations" :
            if action.IDperiode not in dict_dernieres_reservations or (action.horodatage > dict_dernieres_reservations[action.IDperiode].horodatage and action.etat != "suppression") :
                dict_dernieres_reservations[action.IDperiode] = action
    
    return {"liste_dates" : liste_dates_actions, "dict_actions" : dict_actions, "derniere_synchro" : derniere_synchro, "categorie" : categorie}


def ValiderModificationPassword(form=None, valider_conditions=True, user=None):
    # Vérifie que les mots de passe sont identiques
    if form.password1.data != form.password2.data:
        flash(u"Les deux mots de passe saisis doivent être identiques !", 'error')
        return False

    # Vérifie que le mot de passe est bien formaté
    if len(form.password1.data) < 8:
        flash(u"Le mot de passe doit comporter au moins 8 caractères !", 'error')
        return False

    if not sum(1 for c in form.password1.data if c.islower()):
        flash(u"Le mot de passe doit comporter au moins une lettre minuscule !", 'error')
        return False

    if not sum(1 for c in form.password1.data if c.isupper()):
        flash(u"Le mot de passe doit comporter au moins une lettre majuscule !", 'error')
        return False

    if not sum(1 for c in form.password1.data if c.isdigit()):
        flash(u"Le mot de passe doit comporter au moins un chiffre !", 'error')
        return False

    #if not sum(1 for c in form.password1.data if c in u"%#:$*@-_"):
    #    flash(u"Le mot de passe doit comporter au moins un caractère spécial (%#:$*@-_!?&) !", 'error')
    #    return False

    # Vérifie que le mot de passe a bien été changé
    if user == None and current_user.check_password(form.password1.data) == True:
        flash(u"Vous ne pouvez pas conserver l'ancien mot de passe !", 'error')
        return False

    # Vérifie que la case des conditions d'utilisation a été cochée
    if valider_conditions == True :
        if form.accept.data == False:
            flash(u"Vous devez obligatoirement accepter les conditions d'utilisation !", 'error')
            return False

    # Si besoin de connecter l'user (après reset password)
    if user != None :
        login_user(user, remember=False)

    # Enregistre le nouveau mot de passe
    current_user.SetCustomPassword(form.password1.data)
    app.logger.debug("Nouveau mot de passe enregistre pour %s", current_user.identifiant)

    # Enregistre l'action
    m = models.Action(IDfamille=current_user.IDfamille, IDutilisateur=current_user.IDutilisateur, categorie="compte", action="maj_password", description=u"Mise à jour du mot de passe", etat="attente", parametres=current_user.password)
    db.session.add(m)
    db.session.commit()

    return True
