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
from application import db, app, utils
from passlib.hash import sha256_crypt


    
class User(db.Model):
    __tablename__ = "portail_users"
    IDuser = db.Column(db.Integer, primary_key=True)
    identifiant = db.Column(db.String(20), unique=True, index=True)
    password = db.Column(db.String(200))
    nom = db.Column(db.String(80))
    email = db.Column(db.String(80))
    role = db.Column(db.String(80))
    IDfamille = db.Column(db.Integer, index=True)
    infos = {}
    
    def __init__(self , identifiant=None, password=None, nom=None, email=None, role="famille", IDfamille=None):
        self.identifiant = identifiant
        self.password = sha256_crypt.encrypt(password)
        self.nom = nom
        self.email = email
        self.role = role
        self.IDfamille = IDfamille
 
    def check_password(self, password):
        return sha256_crypt.verify(password, self.password)
        
    def is_authenticated(self):
        return True
 
    def is_active(self):
        return True
 
    def is_anonymous(self):
        return False
 
    def get_id(self):
        return unicode(self.IDuser)
 
    def __repr__(self):
        return '<User %r>' % (self.username)
    
    def get_image(self):
        return 'img/famille.png'
    
    def SetInfos(self, key="", valeur=None):
        self.infos[key] = valeur
        
    def GetInfos(self, key=""):
        if self.infos.has_key(key) :
            return self.infos[key]
        return None
        
        
        
class Facture(db.Model):
    __tablename__ = "portail_factures"
    IDfacture = db.Column(db.Integer, primary_key=True)
    IDfamille = db.Column(db.Integer, index=True)
    numero = db.Column(db.String(50))
    date_edition = db.Column(db.Date)
    date_debut = db.Column(db.Date)
    date_fin = db.Column(db.Date)
    montant = db.Column(db.Float)
    montant_regle = db.Column(db.Float)
    montant_solde = db.Column(db.Float)
    
    def __init__(self , IDfacture=None, IDfamille=None, numero=None, date_edition=None, \
                        date_debut=None, date_fin=None, montant=0.0, montant_regle=0.0, \
                        montant_solde=0.0):
        if IDfacture != None :
            self.IDfacture = IDfacture
        self.IDfamille = IDfamille
        self.numero = numero
        self.date_edition = date_edition
        self.date_debut = date_debut
        self.date_fin = date_fin
        self.montant = montant
        self.montant_regle = montant_regle
        self.montant_solde = montant_solde
 
    def __repr__(self):
        return '<Facture %d>' % (self.IDfacture)

        
    
   
class Action(db.Model):
    __tablename__ = "portail_actions"
    IDaction = db.Column(db.Integer, primary_key=True)
    horodatage = db.Column(db.DateTime, default=datetime.datetime.now)
    IDuser = db.Column(db.Integer, index=True)
    categorie = db.Column(db.String(50))
    action = db.Column(db.String(50))
    description = db.Column(db.String(300))
    commentaire = db.Column(db.String(300))
    parametres = db.Column(db.String(300))
    etat = db.Column(db.String(50))
    traitement_horodatage = db.Column(db.DateTime)
    IDperiode = db.Column(db.Integer)
    
    def __init__(self , horodatage=None, IDuser=None, categorie=None, action=None, description=None, \
                        commentaire=None, parametres=None, etat=None, traitement_horodatage=None, IDperiode=None):
        if horodatage != None :
            self.horodatage = horodatage
        self.IDuser = IDuser
        self.categorie = categorie
        self.action = action
        self.description = description
        self.commentaire = commentaire
        self.parametres = parametres
        self.etat = etat
        self.traitement_horodatage = traitement_horodatage
        self.IDperiode = IDperiode
 
    def __repr__(self):
        return '<Action %d>' % (self.IDaction)

       
       
class Reglement(db.Model):
    __tablename__ = "portail_reglements"
    IDreglement = db.Column(db.Integer, primary_key=True)
    IDfamille = db.Column(db.Integer, index=True)
    date = db.Column(db.Date)
    mode = db.Column(db.String(100))
    numero = db.Column(db.String(50))
    montant = db.Column(db.Float)
    date_encaissement = db.Column(db.Date)
    
    def __init__(self , IDreglement=None, IDfamille=None, date=None, mode=None, \
                        numero=None, montant=0.0, date_encaissement=None):
        if IDreglement != None :
            self.IDreglement = IDreglement
        self.IDfamille = IDfamille
        self.date = date
        self.mode = mode
        self.numero = numero
        self.montant = montant
        self.date_encaissement = date_encaissement
 
    def __repr__(self):
        return '<Reglement %d>' % (self.IDreglement)

    def get_description(self):
        date = utils.CallFonction("DateDDEnFr", self.date)
        montant = utils.CallFonction("Formate_montant", self.montant)
        description = u"%s de %s du %s" % (self.mode, montant, date)
        return description
        
        
        
class Piece_manquante(db.Model):
    __tablename__ = "portail_pieces_manquantes"
    IDpiece_manquante = db.Column(db.Integer, primary_key=True)
    IDfamille = db.Column(db.Integer, index=True)
    IDtype_piece = db.Column(db.Integer)
    IDindividu = db.Column(db.Integer)
    nom = db.Column(db.String(200))
    
    def __init__(self , IDpiece_manquante=None, IDfamille=None, IDtype_piece=None, IDindividu=None, nom=None):
        if IDpiece_manquante != None :
            self.IDpiece_manquante = IDpiece_manquante
        self.IDfamille = IDfamille
        self.IDtype_piece = IDtype_piece
        self.IDindividu = IDindividu
        self.nom = nom
 
    def __repr__(self):
        return '<IDpiece_manquante %d>' % (self.IDpiece_manquante)

   
class Type_piece(db.Model):
    __tablename__ = "portail_types_pieces"
    IDtype_piece = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(200))
    public = db.Column(db.String(50))
    fichier = db.Column(db.String(200))
    
    def __init__(self , IDtype_piece=None, nom=None, public=None, fichier=None):
        if IDtype_piece != None :
            self.IDtype_piece = IDtype_piece
        self.nom = nom
        self.public = public
        self.fichier = fichier
 
    def __repr__(self):
        return '<IDtype_piece %d>' % (self.IDtype_piece)
    
    def get_icone_fichier(self):
        """ Retourne une icône selon le type de fichier (pdf, word, autre) """
        if self.fichier == None :
            return None
        
        if self.fichier.endswith(".pdf"):
            return "fa-file-pdf-o"
        elif self.fichier.endswith(".doc") or self.fichier.endswith(".docx"):
            return "fa-file-word-o"
        elif self.fichier.endswith(".txt"):
            return "fa-file-text-o"
        elif self.fichier.endswith(".jpg")  or self.fichier.endswith(".png"):
            return "fa-file-image-o"
        else :
            return "fa-file-o"

            
class Cotisation_manquante(db.Model):
    __tablename__ = "portail_cotisations_manquantes"
    IDcotisation_manquante = db.Column(db.Integer, primary_key=True)
    IDfamille = db.Column(db.Integer, index=True)
    IDindividu = db.Column(db.Integer)
    nom = db.Column(db.String(200))
    
    def __init__(self , IDcotisation_manquante=None, IDfamille=None, IDindividu=None, nom=None):
        if IDcotisation_manquante != None :
            self.IDcotisation_manquante = IDcotisation_manquante
        self.IDfamille = IDfamille
        self.IDindividu = IDindividu
        self.nom = nom
 
    def __repr__(self):
        return '<IDcotisation_manquante %d>' % (self.IDcotisation_manquante)

        
class Activite(db.Model):
    __tablename__ = "portail_activites"
    IDactivite = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(300))
    coche_unique = db.Column(db.Integer)
    
    periodes = db.relationship("Periode")
    
    def __init__(self , IDactivite=None, nom=None, coche_unique=0):
        if IDactivite != None :
            self.IDactivite = IDactivite
        self.nom = nom
        self.coche_unique = coche_unique
 
    def __repr__(self):
        return '<IDactivite %d>' % (self.IDactivite)

        
class Individu(db.Model):
    __tablename__ = "portail_individus"
    IDindividu = db.Column(db.Integer, primary_key=True)
    IDfamille = db.Column(db.Integer, index=True)
    prenom = db.Column(db.String(200))
    age = db.Column(db.Integer)
    IDcivilite = db.Column(db.Integer)
    
    inscriptions = db.relationship("Inscription")
    
    def __init__(self , IDindividu=None, IDfamille=None, prenom=None, age=None, IDcivilite=None):
        if IDindividu != None :
            self.IDindividu = IDindividu
        self.IDfamille = IDfamille
        self.prenom = prenom
        self.age = age
        self.IDcivilite = IDcivilite
 
    def __repr__(self):
        return '<IDindividu %d>' % (self.IDindividu)

    def get_image(self):
        if self.IDcivilite in (1, 4) :
            return "img/homme.png"
        if self.IDcivilite in (2, 3, 5) :
            return "img/femme.png"
        return 'img/homme.png'

        
class Inscription(db.Model):
    __tablename__ = "portail_inscriptions"
    IDinscription = db.Column(db.Integer, primary_key=True)
    IDfamille = db.Column(db.Integer, index=True)

    IDindividu = db.Column(db.Integer, db.ForeignKey("portail_individus.IDindividu"))
    individu = db.relationship("Individu")  

    IDactivite = db.Column(db.Integer, db.ForeignKey("portail_activites.IDactivite"))
    activite = db.relationship("Activite")  

    IDgroupe = db.Column(db.Integer, db.ForeignKey("portail_groupes.IDgroupe"))
    groupe = db.relationship("Groupe")  
    
    def __init__(self , IDinscription=None, IDindividu=None, IDfamille=None, IDactivite=None, IDgroupe=None):
        if IDinscription != None :
            self.IDinscription = IDinscription
        self.IDindividu = IDindividu
        self.IDfamille = IDfamille
        self.IDactivite = IDactivite
        self.IDgroupe = IDgroupe
        
    def __repr__(self):
        return '<IDinscription %d>' % (self.IDinscription)

        
class Periode(db.Model):
    __tablename__ = "portail_periodes"
    IDperiode = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(300))
    date_debut = db.Column(db.Date)
    date_fin = db.Column(db.Date)
    
    IDactivite = db.Column(db.Integer, db.ForeignKey("portail_activites.IDactivite"))
    activite = db.relationship("Activite")  
    
    def __init__(self , IDperiode=None, IDactivite=None, nom=None, date_debut=None, date_fin=None):
        if IDperiode != None :
            self.IDperiode = IDperiode
        self.IDactivite = IDactivite
        self.nom = nom
        self.date_debut = date_debut
        self.date_fin = date_fin
        
    def __repr__(self):
        return '<IDperiode %d>' % (self.IDperiode)


class Groupe(db.Model):
    __tablename__ = "portail_groupes"
    IDgroupe = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(300))
    ordre = db.Column(db.Integer)
    
    IDactivite = db.Column(db.Integer, db.ForeignKey("portail_activites.IDactivite"))
    activite = db.relationship("Activite")  

    def __init__(self , IDgroupe=None, nom=None, IDactivite=None, ordre=None):
        if IDgroupe != None :
            self.IDgroupe = IDgroupe
        self.nom = nom
        self.IDactivite = IDactivite
        self.ordre = ordre
        
    def __repr__(self):
        return '<IDgroupe %d>' % (self.IDgroupe)

        
class Unite(db.Model):
    __tablename__ = "portail_unites"
    IDunite = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(300))
    ordre = db.Column(db.Integer)
    
    IDactivite = db.Column(db.Integer, db.ForeignKey("portail_activites.IDactivite"))
    activite = db.relationship("Activite")  
   
    def __init__(self , IDunite=None, IDactivite=None, nom=None, ordre=None):
        if IDunite != None :
            self.IDunite = IDunite
        self.nom = nom
        self.ordre = ordre
        self.IDactivite = IDactivite
        
    def __repr__(self):
        return '<IDunite %d>' % (self.IDunite)

class Ouverture(db.Model):
    __tablename__ = "portail_ouvertures"
    IDouverture = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date)

    IDunite = db.Column(db.Integer, db.ForeignKey("portail_unites.IDunite"))
    unite = db.relationship("Unite")  
    
    IDgroupe = db.Column(db.Integer, db.ForeignKey("portail_groupes.IDgroupe"))
    groupe = db.relationship("Groupe")  
    
    def __init__(self , IDouverture=None, date=None, IDunite=None, IDgroupe=None):
        if IDouverture != None :
            self.IDouverture = IDouverture
        self.date = date
        self.IDunite = IDunite
        self.IDgroupe = IDgroupe
        
    def __repr__(self):
        return '<IDouverture %d>' % (self.IDouverture)
        

class Consommation(db.Model):
    __tablename__ = "portail_consommations"
    IDconsommation = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date)
    etat = db.Column(db.String(20))
    
    IDunite = db.Column(db.Integer, db.ForeignKey("portail_unites.IDunite"))
    unite = db.relationship("Unite")  
    
    IDinscription = db.Column(db.Integer, db.ForeignKey("portail_inscriptions.IDinscription"))
    inscription = db.relationship("Inscription")  
    
    def __init__(self , IDconsommation=None, date=None, IDunite=None, IDinscription=None, etat=None):
        if IDconsommation != None :
            self.IDconsommation = IDconsommation
        self.date = date
        self.IDunite = IDunite
        self.IDinscription = IDinscription
        self.etat = etat
        
    def __repr__(self):
        return '<IDconsommation %d>' % (self.IDconsommation)
        

class Reservation(db.Model):
    __tablename__ = "portail_reservations"
    IDreservation = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date)
    
    IDinscription = db.Column(db.Integer, db.ForeignKey("portail_inscriptions.IDinscription"))
    inscription = db.relationship("Inscription")  
    
    IDunite = db.Column(db.Integer, db.ForeignKey("portail_unites.IDunite"))
    unite = db.relationship("Unite")  

    IDaction = db.Column(db.Integer, db.ForeignKey("portail_actions.IDaction"))
    action = db.relationship("Action")  
    
    def __init__(self , IDreservation=None, date=None, IDinscription=None, IDunite=None, IDaction=None):
        if IDreservation != None :
            self.IDreservation = IDreservation
        self.date = date
        self.IDinscription = IDinscription
        self.IDunite = IDunite
        self.IDaction = IDaction
        
    def __repr__(self):
        return '<IDreservation %d>' % (self.IDreservation)
        
