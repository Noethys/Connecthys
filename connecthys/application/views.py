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
try :
    from flask_wtf import CSRFProtect
except :
    # Pour compatibilité avec anciennes versions de flask_wtf
    from flask_wtf import CsrfProtect
from application import app, login_manager, db
from application import models, forms, utils, updater, exemples
from sqlalchemy import func
from eopayment import Payment


LISTE_PAGES = [
    {"type" : "label", "label" : u"MENU"}, 
        {"type" : "page", "page" : "accueil", "raccourci" : True}, 
    {"type" : "label", "label" : u"VOTRE DOSSIER"}, 
        {"type" : "page", "page" : "renseignements", "raccourci" : True, "affichage" : "RENSEIGNEMENTS_AFFICHER"}, 
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
    "renseignements" : {"nom" : u"Renseignements", "icone" : "fa-user", "description" : u"Consulter et modifier des renseignements", "couleur" : "purple"},
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

CHAMPS_RENSEIGNEMENTS = ["nom", "prenom", "date_naiss", "cp_naiss", "ville_naiss", "adresse_auto", "rue_resid", "cp_resid", "ville_resid", 
                                        "tel_domicile", "tel_mobile", "mail", "profession", "employeur", "travail_tel", "travail_mail"]

DICT_RENSEIGNEMENTS = {"nom" : u"Nom", "prenom" : u"Prénom", "date_naiss" : u"Date de naissance", "cp_naiss" : u"CP de naissance", "ville_naiss" : u"Ville de naissance", "rue_resid" : u"Adresse - Rue", "cp_resid" : u"Adresse - CP", "ville_resid" : u"Adresse - Ville", 
                                        "tel_domicile" : u"Tél. Domicile", "tel_mobile" : u"Tél. Mobile", "mail" : u"Email", "profession" : u"Profession", "employeur" : u"Employeur", "travail_tel" : u"Tél. Pro.", "travail_mail" : u"Email Pro."}


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
    
    app.logger.debug("Page FACTURES (%s): famille id(%s) liste_factures:(%s)", current_user.identifiant, current_user.IDfamille, liste_factures)

    if models.GetParametre(nom="PAIEMENT_EN_LIGNE_ACTIF") == "True" :
	# Récupération de la liste de tous les paiements en ligne de la famille
	liste_paiements = models.Paiement.query.filter_by(IDfamille=current_user.IDfamille).all()
        app.logger.debug("Page FACTURES (%s): famille id(%s) liste_paiements:(%s)", current_user.identifiant, current_user.IDfamille, liste_paiements)
    else :
        liste_paiements = []

    # Recherche les factures impayées
    nbre_factures_impayees = 0
    montant_factures_impayees = 0.0
    for facture in liste_factures :
        if facture.montant_solde > 0.0 :
            nbre_factures_impayees += 1
            montant_factures_impayees += facture.montant_solde

            if liste_paiements :
                for paiement in liste_paiements :
                    # un paiement validé existe pour cette facture
                    if paiement.refdet == facture.numero and paiement.resultrans == "P" :
                        facture.en_cours_paiement = "1"
                        # ce paiement solde la facture
                        if facture.montant_solde == paiement.montant :
                            nbre_factures_impayees -= 1
                            montant_factures_impayees -= paiement.montant
                            facture.montant_regle += paiement.montant
                            facture.montant_solde -= paiement.montant
                        # ce paiement ne regle que partiellement cette facture
                        else :
                            montant_factures_impayees -= paiement.montant
                            facture.montant_regle += paiement.montant
                            facture.montant_solde -= paiement.montant
                            app.logger.debug("Page FACTURES (%s): famille id(%s) IDpaiement:(%s) paiement.montant:(%s) facture.montant_solde:(%s)", current_user.identifiant, current_user.IDfamille, paiement.IDpaiement, paiement.montant, facture.montant_solde)
                            if facture.montant_regle == facture.montant:
                                nbre_factures_impayees -= 1
                    elif paiement.refdet == facture.numero and paiement.resultrans == None :
                        if datetime.datetime.strptime(paiement.IDtransaction[:12], "%Y%m%d%H%M") + datetime.timedelta(minutes=5) > datetime.datetime.utcnow() :
                            app.logger.debug("Paiement(%s) en cours", paiement.IDpaiement)
                            facture.en_cours_paiement = "1"
                        else :
                            app.logger.debug("Paiement(%s) hors delai", paiement.IDpaiement)
    
    # Recherche l'historique des demandes liées aux factures
    historique = GetHistorique(IDfamille=current_user.IDfamille, categorie="factures")
    
    dict_parametres = models.GetDictParametres()
    app.logger.debug("Page FACTURES (%s): famille id(%s)", current_user.identifiant, current_user.IDfamille)
    return render_template('factures.html', active_page="factures", liste_factures=liste_factures, \
                            nbre_factures_impayees=nbre_factures_impayees, \
                            montant_factures_impayees=montant_factures_impayees, \
                            liste_paiements=liste_paiements, \
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
                            
                            
@app.route('/effectuer_paiement_en_ligne')
@login_required
def effectuer_paiement_en_ligne():
    # Récupération de la liste des factures
    liste_factures = models.Facture.query.filter_by(IDfamille=current_user.IDfamille).order_by(models.Facture.date_debut.desc()).all()
    app.logger.debug("Page EFFECTUER_PAIEMENT EN LIGNE (%s): famille id(%s) liste_factures(%s)", current_user.identifiant, current_user.IDfamille, liste_factures)

    # Récupération de la liste des paiements 
    liste_paiements = models.Paiement.query.filter_by(IDfamille=current_user.IDfamille, resultrans="P").all()
    app.logger.debug("Page EFFECTUER_PAIEMENT EN LIGNE (%s): famille id(%s) liste_paiement(%s)", current_user.identifiant, current_user.IDfamille, liste_paiements)

    if models.GetParametre(nom="PAIEMENT_EN_LIGNE_SYSTEME") == "1" :
        systeme_paiement = "tipi_regie"
        liste_regies = models.Regie.query.all()
        saisie_type = models.GetParametre(nom="PAIEMENT_EN_LIGNE_TIPI_SAISIE")
        app.logger.debug("Page EFFECTUER_PAIEMENT EN LIGNE (%s): famille id(%s) saisie_type(%s)", current_user.identifiant, current_user.IDfamille, saisie_type)
        # validation
        if saisie_type == '1':
            saisie = 'X'
        # production
        elif saisie_type == '2':
            saisie = 'A'
        else :
            saisie = 'T'
        
        app.logger.debug("Page EFFECTUER_PAIEMENT EN LIGNE (%s): famille id(%s) liste_regie(%s)", current_user.identifiant, current_user.IDfamille, liste_regies)
    else :
        systeme_paiement = ""

    try:
        id = request.args.get("id", 0, type=int)
        IDfactures_a_debiter = request.args.get("liste_factures", ",", type=str)
        montant_reglement = request.args.get("montant_reglement", ",", type=float)

        liste_IDfactures_a_debiter = IDfactures_a_debiter.split(',')
        liste_IDfactures_a_debiter = map(int, liste_IDfactures_a_debiter)

        # on cree un dictionnaire avec les infos des factures a debiter
        dict_facture_a_debiter = {}
        for facture in liste_factures :
            for ID_a_debiter in liste_IDfactures_a_debiter :
                if facture.IDfacture == ID_a_debiter :
                    if not dict_facture_a_debiter.has_key(ID_a_debiter) :
                        dict_facture_a_debiter[ID_a_debiter] = {}
                    dict_facture_a_debiter[ID_a_debiter]['Numero'] = facture.numero
                    dict_facture_a_debiter[ID_a_debiter]['IDregie'] = facture.IDregie
                    dict_facture_a_debiter[ID_a_debiter]['en_cours_paiement'] = facture.en_cours_paiement
                    dict_facture_a_debiter[ID_a_debiter]['date_debut'] = facture.date_debut
                    if facture.en_cours_paiement == "1" :
                        for paiement in liste_paiements :
                            if paiement.IDfacture == facture.IDfacture :
                                dict_facture_a_debiter[ID_a_debiter]['Solde'] = (facture.montant_solde - paiement.montant)
                    else :
                        dict_facture_a_debiter[ID_a_debiter]['Solde'] = facture.montant_solde

        # il y a plus d une facture sélectionnée
        if len(dict_facture_a_debiter) > 1 :
            num = ""
            montant = 0.00
            for key, valeur in dict_facture_a_debiter.iteritems() :
                num += valeur["Numero"] + " // "
                montant += valeur["Solde"]
            app.logger.debug("Page EFFECTUER_PAIEMENT_EN_LIGNE (%s): plus d une facture selectionnee NON TRAITE factures(%s) montant: %s €", current_user.identifiant, num, montant)
            flash(u"Votre demande de paiement en ligne de plusieurs factures est impossible")
            return jsonify(success=0, error_msg="Paiement en ligne multi factures impossible")
        # une seule facture sélectionnée
        elif len(dict_facture_a_debiter) == 1 :
            infos_facture = {}
            infos_facture = dict_facture_a_debiter.values()[0]
            regie = models.Regie.query.filter_by(IDregie=infos_facture["IDregie"]).first()

            app.logger.debug("Page EFFECTUER_PAIEMENT_EN_LIGNE : infos_facture: (%s) regie.nom: (%s) type(regie.nom): (%s) regie.numclitipi: (%s)", infos_facture, regie.nom, type(regie.nom), regie.numclitipi)
            p = Payment(systeme_paiement, {'numcli': regie.numclitipi})
            requete = p.request(amount=str(montant_reglement),
                exer=str(infos_facture["date_debut"].year()),
                refdet=infos_facture["Numero"],
                objet="Paiement " + regie.nom.encode("ascii", 'ignore'),
                email=current_user.email,
                urlcl=url_for('retour_tipi', _external=True),
                saisie=saisie)
            app.logger.debug("Page EFFECTUER_PAIEMENT_EN_LIGNE (%s): requete: %s // systeme_paiement(%s)", current_user.identifiant, requete, systeme_paiement)
            description = u'Paiement en ligne de la facture n° %s pour un montant de %s €: TransactionID %s' % (infos_facture["Numero"], infos_facture["Solde"], requete[0])

            m = models.Paiement(IDfamille=current_user.IDfamille, factures_ID=IDfactures_a_debiter, IDtransaction=requete[0], refdet=infos_facture["Numero"], montant=montant_reglement, objet=requete[3], saisie=saisie)
            db.session.add(m)
            db.session.commit()

        flash(u"Votre demande de paiement en ligne d une facture est en cours")
        return jsonify(success=1, urltoredirect=requete[2])
    except Exception, erreur:
        app.logger.debug("Page EFFECTUER_PAIEMENT_EN_LIGNE (%s): ERREUR: %s)", current_user.identifiant, erreur)
        return jsonify(success=0, error_msg=str(erreur))


# -----------------------RETOUR TIPI REGIE-------------------------------
from application import csrf
@app.route('/retour_tipi', methods=['POST'])
@csrf.exempt
def retour_tipi():

    try:
        tipiform = forms.RetourTipi(request.form)
        resultats = request.form
        resultat = {}
        resultat["numcli"] = request.form.get("numcli", 0, type=str)
        resultat["refdet"] = request.form.get("refdet", 0, type=str)
        resultat["objet"] = request.form.get("objet", 0, type=str)
        resultat["resultrans"] = request.form.get("resultrans", 0, type=str)
        resultat["numauto"] = request.form.get("numauto", 0, type=str)
        resultat["dattrans"] = request.form.get("dattrans", 0, type=str)
        resultat["heurtrans"] = request.form.get("heurtrans", 0, type=str)

        # Récupération de la liste des paiements
        liste_paiements = models.Paiement.query.filter_by(refdet=resultat["refdet"], objet=resultat["objet"]).all()

        for paiement in liste_paiements:
            if paiement.objet == resultat["objet"]:
                IDpaiement_a_modif = paiement.IDpaiement

        paiement_a_modif = models.Paiement.query.filter_by(IDpaiement=IDpaiement_a_modif).first()
        paiement_a_modif.numauto = resultat["numauto"]
        paiement_a_modif.resultrans = resultat["resultrans"]
        paiement_a_modif.dattrans = resultat["dattrans"]
        paiement_a_modif.heurtrans = resultat["heurtrans"]
        db.session.commit()

        if paiement_a_modif.resultrans == "P" :
            parametres = u"factures_ID=%s#IDpaiement=%s#IDtransaction=%s#refdet=%s#montant=%s#objet=%s#numauto=%s#dattrans=%s#heurtrans=%s" % (paiement_a_modif.factures_ID, paiement_a_modif.IDpaiement, paiement_a_modif.IDtransaction, paiement_a_modif.refdet, paiement_a_modif.montant, paiement_a_modif.objet, paiement_a_modif.numauto, paiement_a_modif.dattrans, paiement_a_modif.heurtrans)
            commentaire = ""
            description = "Paiement en ligne de la facture %s" % paiement_a_modif.refdet
            m = models.Action(IDfamille=paiement_a_modif.IDfamille, categorie="reglements", action="paiement_en_ligne", description=description, etat="attente", commentaire=commentaire, parametres=parametres)
            db.session.add(m)
            db.session.commit()

        app.logger.debug("Page RETOUR_TIPI: resultats:%s liste_paiements: %s refdet: %s)", resultats, liste_paiements, resultat["refdet"])
        return render_template('retour_tipi.html', title='Retour TIPI', form=tipiform)
    except Exception, erreur:
        app.logger.debug("Page RETOUR_TIPI: ERREUR: %s", erreur)
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
        
        # Récupération de la liste des paiements validés
        liste_paiements = models.Paiement.query.filter_by(IDfamille=current_user.IDfamille, resultrans="P").all()
        app.logger.debug("Page REGLEMENTS (%s): famille id(%s) liste_paiements:(%s)", current_user.identifiant, current_user.IDfamille, liste_paiements)

        # Recherche les factures impayées
        nbre_factures_impayees = 0
        montant_factures_impayees = 0.0
        for facture in liste_factures :
            if facture.montant_solde > 0.0 :
                nbre_factures_impayees += 1
                montant_factures_impayees += facture.montant_solde
                if liste_paiements :
                    for paiement in liste_paiements :
                        # un paiement validé existe pour cette facture
                        if paiement.refdet == facture.numero:
                            facture.en_cours_paiement = "1"
                            # ce paiement solde la facture
                            if facture.montant_solde == paiement.montant :
                                nbre_factures_impayees -= 1
                                montant_factures_impayees -= paiement.montant
                                facture.montant_regle += paiement.montant
                                facture.montant_solde -= paiement.montant
                            # ce paiement ne regle que partiellement cette facture
                            else :
                                montant_factures_impayees -= paiement.montant
                                facture.montant_regle += paiement.montant
                                facture.montant_solde -= paiement.montant
                                app.logger.debug("Page REGLEMENTS (%s): famille id(%s) IDpaiement:(%s) paiement.montant:(%s) facture.montant_solde:(%s)", current_user.identifiant, current_user.IDfamille, paiement.IDpaiement, paiement.montant, facture.montant_solde)
                                if facture.montant_regle == facture.montant:
                                    nbre_factures_impayees -= 1
    
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
        if len(individu.get_inscriptions()) > 0 :
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
   
   

   
# ------------------------- RENSEIGNEMENTS ---------------------------------- 

@app.route('/renseignements')
@login_required
def renseignements():
    # Récupération des renseignements modifiés
    dict_renseignements = GetDictRenseignements(IDfamille=current_user.IDfamille)
    
    # Récupération des individus
    liste_individus_temp = models.Individu.query.filter_by(IDfamille=current_user.IDfamille).order_by(models.Individu.prenom).all()
    
    liste_individus = []
    for individu in liste_individus_temp :
        # Attribution d'une couleur
        index_couleur = random.randint(0, len(COULEURS)-1)
        individu.index_couleur = index_couleur
        individu.couleur = COULEURS[index_couleur]
        liste_individus.append(individu)
        
        individu.renseignements = dict_renseignements[individu.IDindividu]
        
    # Recherche l'historique des demandes liées aux renseignements
    historique = GetHistorique(IDfamille=current_user.IDfamille, categorie="renseignements")
    dict_parametres = models.GetDictParametres()
    
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
        if dict_valeurs.has_key(IDindividu) == False :
            dict_valeurs[individu.IDindividu] = {"individu" : individu, "champs_modifies" : []}
            
        for champ in CHAMPS_RENSEIGNEMENTS :
            valeur = getattr(individu, champ)
            if "date" in champ :
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
            valeur = renseignement.valeur
            if renseignement.champ == "adresse_auto" and valeur == None :
                valeur = 0
            dict_valeurs[action.IDindividu][renseignement.champ] = valeur
            dict_valeurs[action.IDindividu]["champs_modifies"].append(renseignement.champ)
    
    for IDindividu, dictChamps in dict_valeurs.iteritems() :
        if type(dictChamps) == dict :
            if dictChamps["adresse_auto"] != 0 :
                IDindividuTemp = int(dictChamps["adresse_auto"])
                rue =  dict_valeurs[IDindividuTemp]["rue_resid"]
                cp = dict_valeurs[IDindividuTemp]["cp_resid"]
                ville = dict_valeurs[IDindividuTemp]["ville_resid"]
                prenom = dict_valeurs[IDindividuTemp]["prenom"]
                dict_valeurs[IDindividu]["adresse"] = u"%s %s %s (L'adresse de %s)" % (rue, cp, ville, prenom)
            else :
                rue = dict_valeurs[IDindividu]["rue_resid"]
                cp = dict_valeurs[IDindividu]["cp_resid"]
                ville = dict_valeurs[IDindividu]["ville_resid"]
                dict_valeurs[IDindividu]["adresse"] = u"%s %s %s" % (rue, cp, ville)
            
                dict_valeurs["liste_choix_adresses"].append((IDindividu, u"La même adresse que %s" % dictChamps["prenom"])) 
            
    return dict_valeurs
    
    
@app.route('/modifier_renseignements')
@login_required
def modifier_renseignements():
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
    try:
        # Récupération du form rempli
        form = forms.Renseignements(request.form)   
        
        # Récupération des valeurs
        IDindividu = int(form.idindividu.data)
        
        # Récupération des valeurs initiales
        dict_renseignements = GetDictRenseignements(IDfamille=current_user.IDfamille)
        
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
            if nouvelle_valeur != ancienne_valeur :
                dict_champs_modifies[champ] = nouvelle_valeur
        
        # Description
        nbre_champs_modifies = len(dict_champs_modifies)
        if nbre_champs_modifies == 0 :
            return jsonify(success=0, error_msg=u"Vous n'avez modifié aucun renseignement !")
        elif nbre_champs_modifies == 1 :
            description = u"Modification de 1 renseignement pour %s" % dict_renseignements[IDindividu]["individu"].prenom
        else :
            description = u"Modification de %d renseignements pour %s" % (nbre_champs_modifies, dict_renseignements[IDindividu]["individu"].prenom)
        
        # Enregistrement de l'action
        action = models.Action(IDfamille=current_user.IDfamille, IDindividu=IDindividu, categorie="renseignements", action="envoyer", description=description, etat="attente", parametres=None)
        db.session.add(action)
        db.session.flush()
        
        # Enregistrement des renseignements
        for champ, valeur in dict_champs_modifies.iteritems():
            if champ == "adresse_auto" and valeur == 0 :
                valeur = None
            renseignement = models.Renseignement(champ=champ, valeur=valeur, IDaction=action.IDaction)
            db.session.add(renseignement)

        db.session.commit()

            
        flash(u"Votre demande de modification a bien été enregistrée")
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
        if True :#len(individu.get_inscriptions()) > 0 :
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
            return jsonify(success=0, error_msg=u"%s est déjà inscrit(e) à l'activité sélectionnée !" % inscription.get_individu().prenom)
                    
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
            
                label = None
                if DICT_RENSEIGNEMENTS.has_key(renseignement.champ) :
                    label = u"- %s : %s\n" % (DICT_RENSEIGNEMENTS[renseignement.champ], renseignement.valeur)
                    
                if renseignement.champ == "adresse_auto" and renseignement.valeur != None :
                    individuTemp = models.Individu.query.filter_by(IDindividu=int(renseignement.valeur)).first()
                    label = u"- Adresse associée à celle de %s\n" % individuTemp.prenom
                    
                if label != None :
                    liste_lignes.append(label)
                    
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
    