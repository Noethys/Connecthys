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
#from passlib.hash import sha256_crypt
from Crypto.Hash import SHA256

try :
    # Imports Sqlalchemy_flask pour Connecthys
    from application import db, app, utils
    Base = db.Model
    ForeignKey = db.ForeignKey
    Column = db.Column
    Date = db.Date
    DateTime = db.DateTime
    Integer = db.Integer
    String = db.String
    Float = db.Float
    relationship = db.relationship
    import flask_migrate
    
except :
    # Imports Sqlalchemy pour Noethys
    from sqlalchemy import create_engine, ForeignKey, Column, Date, Integer, String, Float, DateTime
    from sqlalchemy.orm import relationship, sessionmaker
    from sqlalchemy.ext.declarative import declarative_base
    Base = declarative_base()

    
def GetVersionDB():
    try :
        version = Parametre.query.filter_by(nom="version").first().parametre
    except Exception, err :
        return None
    return version
    
def CreationDB():
    """ Création de la DB """
    with app.app_context():
        app.logger.info("Creation de la base de donnees...")
        db.create_all()
        app.logger.info("Creation ok.")
        app.logger.info("Initialisation de la migration de sqlalchemy...")
        flask_migrate.init()
        app.logger.info("Initialisation ok.")
    
    # Mémorisation du numéro de version dans la DB
    m = Parametre(nom="version", parametre=app.config["VERSION_APPLICATION"])
    db.session.add(m)
    db.session.commit()

def UpgradeDB():
    """ Mise à jour de la DB """
    with app.app_context():
        app.logger.info("Migration de la base de donnees...")
        try :
            flask_migrate.migrate()
        except Exception, err :
            if "Path doesn't exist" in str(err) :
                app.logger.info("Repertoire Migrations manquant -> Initialisation de flask_migrate maintenant...")
                flask_migrate.init()
                flask_migrate.migrate()
            
        app.logger.info("Migration ok.")
        app.logger.info("Upgrade de la base de donnees...")
        flask_migrate.upgrade()
        app.logger.info("Upgrade ok.")
            
    # Mémorisation du nouveau numéro de version dans la DB
    m = Parametre.query.filter_by(nom="version").first()
    m.parametre=app.config["VERSION_APPLICATION"]
    db.session.commit()

      
class Parametre(Base):
    __tablename__ = "portail_parametres"
    IDparametre = Column(Integer, primary_key=True)
    nom = Column(String(200))
    parametre = Column(String(400))
    
    def __init__(self , IDparametre=None, nom=None, parametre=None):
        if IDparametre != None :
            self.IDparametre = IDparametre
        self.nom = nom
        self.parametre = parametre
 
    def __repr__(self):
        return '<Parametre %d>' % (self.IDparametre)
        
        
    
class User(Base):
    __tablename__ = "portail_users"
    IDuser = Column(Integer, primary_key=True)
    identifiant = Column(String(20), unique=True, index=True)
    password = Column(String(200))
    nom = Column(String(80))
    email = Column(String(80))
    role = Column(String(80))
    IDfamille = Column(Integer, index=True)
    infos = {}
    
    def __init__(self , IDuser=None, identifiant=None, decryptpassword=None, cryptpassword=None, nom=None, email=None, role="famille", IDfamille=None):
        if IDuser != None :
            self.IDuser = IDuser
        self.identifiant = identifiant
        if cryptpassword != None :
            self.password = cryptpassword
        else :
            #self.password = sha256_crypt.encrypt(decryptpassword) # Version passlib
            self.password = SHA256.new(decryptpassword).hexdigest()
        self.nom = nom
        self.email = email
        self.role = role
        self.IDfamille = IDfamille
 
    def check_password(self, password):
        #resultat = sha256_crypt.verify(password, self.password) # Version passlib
        resultat = SHA256.new(password).hexdigest() == self.password
        return resultat
        
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
        
        
        
class Facture(Base):
    __tablename__ = "portail_factures"
    IDfacture = Column(Integer, primary_key=True)
    IDfamille = Column(Integer, index=True)
    numero = Column(String(50))
    date_edition = Column(Date)
    date_debut = Column(Date)
    date_fin = Column(Date)
    montant = Column(Float)
    montant_regle = Column(Float)
    montant_solde = Column(Float)
    
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

        
    
   
class Action(Base):
    __tablename__ = "portail_actions"
    IDaction = Column(Integer, primary_key=True)
    horodatage = Column(DateTime)
    IDfamille = Column(Integer, index=True)
    IDindividu = Column(Integer)
    categorie = Column(String(50))
    action = Column(String(50))
    description = Column(String(300))
    commentaire = Column(String(300))
    parametres = Column(String(300))
    etat = Column(String(50))
    traitement_date = Column(Date)
    IDperiode = Column(Integer)
    ref_unique = Column(String(50), index=True)
    reponse = Column(String(450))
    
    reservations = relationship("Reservation")
    
    def __init__(self, horodatage=None, IDfamille=None, IDindividu=None, categorie=None, action=None, description=None, \
                        commentaire=None, parametres=None, etat=None, traitement_date=None, IDperiode=None, ref_unique=None, reponse=None):
        if horodatage == None :
            self.horodatage = datetime.datetime.now()
        else :
            self.horodatage = horodatage
        self.IDfamille = IDfamille
        self.IDindividu = IDindividu
        self.categorie = categorie
        self.action = action
        self.description = description
        self.commentaire = commentaire
        self.parametres = parametres
        self.etat = etat
        self.traitement_date = traitement_date
        self.IDperiode = IDperiode
        if ref_unique == None :
            self.ref_unique = self.GetRefUnique()
        else :
            self.ref_unique = ref_unique
        self.reponse = reponse
        
    def GetRefUnique(self):
        horodatage = self.horodatage.strftime("%Y%m%d%H%M%S%f")
        ref_unique = "%s%06d" % (horodatage, self.IDfamille)
        return ref_unique
        
    def __repr__(self):
        return '<Action %d>' % (self.IDaction)

    def as_dict(self):
        dict_temp = {}
        for c in self.__table__.columns :
            dict_temp[c.name] = getattr(self, c.name)
        
        # Ajout des réservations dans le dict
        dict_temp["reservations"] = []
        for reservation in self.reservations :
            dict_temp["reservations"].append(reservation.as_dict())
            
        return dict_temp

        
       
class Reglement(Base):
    __tablename__ = "portail_reglements"
    IDreglement = Column(Integer, primary_key=True)
    IDfamille = Column(Integer, index=True)
    date = Column(Date)
    mode = Column(String(100))
    numero = Column(String(50))
    montant = Column(Float)
    date_encaissement = Column(Date)
    
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
        
        
        
class Piece_manquante(Base):
    __tablename__ = "portail_pieces_manquantes"
    IDpiece_manquante = Column(Integer, primary_key=True)
    IDfamille = Column(Integer, index=True)
    IDtype_piece = Column(Integer)
    IDindividu = Column(Integer)
    nom = Column(String(200))
    
    def __init__(self , IDpiece_manquante=None, IDfamille=None, IDtype_piece=None, IDindividu=None, nom=None):
        if IDpiece_manquante != None :
            self.IDpiece_manquante = IDpiece_manquante
        self.IDfamille = IDfamille
        self.IDtype_piece = IDtype_piece
        self.IDindividu = IDindividu
        self.nom = nom
 
    def __repr__(self):
        return '<IDpiece_manquante %d>' % (self.IDpiece_manquante)

   
class Type_piece(Base):
    __tablename__ = "portail_types_pieces"
    IDtype_piece = Column(Integer, primary_key=True)
    nom = Column(String(200))
    public = Column(String(50))
    fichiers = Column(String(400))
    
    def __init__(self , IDtype_piece=None, nom=None, public=None, fichiers=None):
        if IDtype_piece != None :
            self.IDtype_piece = IDtype_piece
        self.nom = nom
        self.public = public
        self.fichiers = fichiers
 
    def __repr__(self):
        return '<IDtype_piece %d>' % (self.IDtype_piece)
    
    def GetListeFichiers(self):
        liste_fichiers = []
        if self.fichiers not in ("", None):
            for temp in self.fichiers.split("##") :
                label, nomFichier = temp.split(";")
                if label == "" :
                    label = self.nom
                liste_fichiers.append((label, nomFichier))
        return liste_fichiers
            
            
class Cotisation_manquante(Base):
    __tablename__ = "portail_cotisations_manquantes"
    IDcotisation_manquante = Column(Integer, primary_key=True)
    IDfamille = Column(Integer, index=True)
    IDindividu = Column(Integer)
    IDtype_cotisation = Column(Integer)
    nom = Column(String(200))
    
    def __init__(self , IDcotisation_manquante=None, IDfamille=None, IDindividu=None, IDtype_cotisation=None, nom=None):
        if IDcotisation_manquante != None :
            self.IDcotisation_manquante = IDcotisation_manquante
        self.IDfamille = IDfamille
        self.IDindividu = IDindividu
        self.IDtype_cotisation = IDtype_cotisation
        self.nom = nom
 
    def __repr__(self):
        return '<IDcotisation_manquante %d>' % (self.IDcotisation_manquante)

        
class Activite(Base):
    __tablename__ = "portail_activites"
    IDactivite = Column(Integer, primary_key=True)
    nom = Column(String(300))
    inscriptions_affichage = Column(Integer)
    inscriptions_date_debut = Column(DateTime)
    inscriptions_date_fin = Column(DateTime)
    reservations_affichage = Column(Integer)
    unites_multiples = Column(Integer)
    reservations_limite = Column(String(20))
    reservations_absenti = Column(String(20))
    
    periodes = relationship("Periode")
    
    def __init__(self , IDactivite=None, nom=None, inscriptions_affichage=1, \
                inscriptions_date_debut=None, inscriptions_date_fin=inscriptions_date_debut, \
                reservations_affichage=1, unites_multiples=0, \
                reservations_limite=None, reservations_absenti=None):
        if IDactivite != None :
            self.IDactivite = IDactivite
        self.nom = nom
        self.inscriptions_affichage = inscriptions_affichage
        self.inscriptions_date_debut = inscriptions_date_debut
        self.inscriptions_date_fin = inscriptions_date_fin
        self.reservations_affichage = reservations_affichage
        self.unites_multiples = unites_multiples
        self.reservations_limite = reservations_limite
        self.reservations_absenti = reservations_absenti
 
    def __repr__(self):
        return '<IDactivite %d>' % (self.IDactivite)
    
    def Get_nbre_periodes_actives(self):
        """ Compte le nombre de périodes actives ce jour """
        nbre = 0
        for periode in self.periodes :
            if periode.Is_active_today() :
                nbre += 1
        return nbre
    
    def Is_modification_allowed(self, date=None):
        """ Demande s'il est possible d'ajouter, modifier ou supprimer la réservation en fonction de la date """
        if self.reservations_limite != None :
            nbre_jours, heure = self.reservations_limite.split("#")
            dt_limite = datetime.datetime(year=date.year, month=date.month, day=date.day, hour=int(heure[:2]), minute=int(heure[3:])) - datetime.timedelta(days=int(nbre_jours))
            if datetime.datetime.now() > dt_limite :
                return False
        return True
        
        
class Individu(Base):
    __tablename__ = "portail_individus"
    IDrattachement = Column(Integer, primary_key=True)
    IDindividu = Column(Integer, index=True)
    IDfamille = Column(Integer)
    prenom = Column(String(200))
    date_naiss = Column(Date)
    IDcivilite = Column(Integer)
    
    inscriptions = relationship("Inscription")
    
    def __init__(self , IDrattachement=None, IDindividu=None, IDfamille=None, prenom=None, date_naiss=None, IDcivilite=None):
        if IDrattachement != None :
            self.IDrattachement = IDrattachement
        self.IDfamille = IDfamille
        self.IDindividu = IDindividu
        self.prenom = prenom
        self.date_naiss = date_naiss
        self.IDcivilite = IDcivilite
 
    def __repr__(self):
        return '<IDindividu %d>' % (self.IDindividu)

    def get_image(self):
        if self.IDcivilite in (1, 4) :
            return "img/homme.png"
        if self.IDcivilite in (2, 3, 5) :
            return "img/femme.png"
        return 'img/homme.png'

    def get_date_naiss(self):
        if self.date_naiss == None :
            return ""
        today = datetime.date.today()
        age = today.year - self.date_naiss.year - ((today.month, today.day) < (self.date_naiss.month, self.date_naiss.day))
        return u"%d ans" % age
        
        
class Inscription(Base):
    __tablename__ = "portail_inscriptions"
    IDinscription = Column(Integer, primary_key=True)
    IDfamille = Column(Integer, index=True)

    IDindividu = Column(Integer, ForeignKey("portail_individus.IDindividu"))
    individu = relationship("Individu")  

    IDactivite = Column(Integer, ForeignKey("portail_activites.IDactivite"))
    activite = relationship("Activite")  

    IDgroupe = Column(Integer, ForeignKey("portail_groupes.IDgroupe"))
    groupe = relationship("Groupe")  
    
    def __init__(self , IDinscription=None, IDindividu=None, IDfamille=None, IDactivite=None, IDgroupe=None):
        if IDinscription != None :
            self.IDinscription = IDinscription
        self.IDindividu = IDindividu
        self.IDfamille = IDfamille
        self.IDactivite = IDactivite
        self.IDgroupe = IDgroupe
        
    def __repr__(self):
        return '<IDinscription %d>' % (self.IDinscription)

        
class Periode(Base):
    __tablename__ = "portail_periodes"
    IDperiode = Column(Integer, primary_key=True)
    nom = Column(String(300))
    date_debut = Column(Date)
    date_fin = Column(Date)
    affichage_date_debut = Column(DateTime)
    affichage_date_fin = Column(DateTime)
    
    IDactivite = Column(Integer, ForeignKey("portail_activites.IDactivite"))
    activite = relationship("Activite")  
    
    def __init__(self , IDperiode=None, IDactivite=None, nom=None, date_debut=None, date_fin=None, \
                        affichage_date_debut=None, affichage_date_fin=None):
        if IDperiode != None :
            self.IDperiode = IDperiode
        self.IDactivite = IDactivite
        self.nom = nom
        self.date_debut = date_debut
        self.date_fin = date_fin
        self.affichage_date_debut = affichage_date_debut
        self.affichage_date_fin = affichage_date_fin
        
    def __repr__(self):
        return '<IDperiode %d>' % (self.IDperiode)
    
    def Is_active_today(self):
        """ Vérifie si la période est active ce jour """
        now = datetime.datetime.now()
        if self.affichage_date_debut == None or (now >= self.affichage_date_debut and now <= self.affichage_date_fin) :
            if self.date_fin < datetime.date.today() :
                return False
            return True
        else :
            return False
        
        

class Groupe(Base):
    __tablename__ = "portail_groupes"
    IDgroupe = Column(Integer, primary_key=True)
    nom = Column(String(300))
    ordre = Column(Integer)
    
    IDactivite = Column(Integer, ForeignKey("portail_activites.IDactivite"))
    activite = relationship("Activite")  

    def __init__(self , IDgroupe=None, nom=None, IDactivite=None, ordre=None):
        if IDgroupe != None :
            self.IDgroupe = IDgroupe
        self.nom = nom
        self.IDactivite = IDactivite
        self.ordre = ordre
        
    def __repr__(self):
        return '<IDgroupe %d>' % (self.IDgroupe)

        
class Unite(Base):
    __tablename__ = "portail_unites"
    IDunite = Column(Integer, primary_key=True)
    nom = Column(String(300))
    unites_principales = Column(String(300))
    unites_secondaires = Column(String(300))
    ordre = Column(Integer)
    
    IDactivite = Column(Integer, ForeignKey("portail_activites.IDactivite"))
    activite = relationship("Activite")  
   
    def __init__(self , IDunite=None, IDactivite=None, nom=None, \
                        unites_principales=None, unites_secondaires=None, \
                        ordre=None):
        if IDunite != None :
            self.IDunite = IDunite
        self.nom = nom
        self.unites_principales = unites_principales
        self.unites_secondaires = unites_secondaires
        self.ordre = ordre
        self.IDactivite = IDactivite
        
    def __repr__(self):
        return '<IDunite %d>' % (self.IDunite)
    
    def Get_unites_principales(self):
        return self.ConvertStrToListe(self.unites_principales) 

    def Get_unites_secondaires(self):
        return self.ConvertStrToListe(self.unites_secondaires) 
        
    def ConvertStrToListe(self, champ=None):
        if champ in ("", None) :
            return []
        listeID = []
        for IDunite in champ.split(";") :
            listeID.append(int(IDunite))
        return listeID
    
    
class Ouverture(Base):
    __tablename__ = "portail_ouvertures"
    IDouverture = Column(Integer, primary_key=True)
    date = Column(Date)

    IDunite = Column(Integer, ForeignKey("portail_unites.IDunite"))
    unite = relationship("Unite")  
    
    IDgroupe = Column(Integer, ForeignKey("portail_groupes.IDgroupe"))
    groupe = relationship("Groupe")  
    
    def __init__(self , IDouverture=None, date=None, IDunite=None, IDgroupe=None):
        if IDouverture != None :
            self.IDouverture = IDouverture
        self.date = date
        self.IDunite = IDunite
        self.IDgroupe = IDgroupe
        
    def __repr__(self):
        return '<IDouverture %d>' % (self.IDouverture)
        

class Consommation(Base):
    __tablename__ = "portail_consommations"
    IDconsommation = Column(Integer, primary_key=True)
    date = Column(Date)
    etat = Column(String(20))
    
    IDunite = Column(Integer, ForeignKey("portail_unites.IDunite"))
    unite = relationship("Unite")  
    
    IDinscription = Column(Integer, ForeignKey("portail_inscriptions.IDinscription"))
    inscription = relationship("Inscription")  
    
    def __init__(self , IDconsommation=None, date=None, IDunite=None, IDinscription=None, etat=None):
        if IDconsommation != None :
            self.IDconsommation = IDconsommation
        self.date = date
        self.IDunite = IDunite
        self.IDinscription = IDinscription
        self.etat = etat
        
    def __repr__(self):
        return '<IDconsommation %d>' % (self.IDconsommation)
        

class Reservation(Base):
    __tablename__ = "portail_reservations"
    IDreservation = Column(Integer, primary_key=True)
    date = Column(Date)
    etat = Column(Integer)
    
    #IDinscription = Column(Integer, ForeignKey("portail_inscriptions.IDinscription"))
    #inscription = relationship("Inscription")  
    
    #IDunite = Column(Integer, ForeignKey("portail_unites.IDunite"))
    #unite = relationship("Unite")  
    
		IDinscription = Column(Integer)
    IDunite = Column(Integer)

    IDaction = Column(Integer, ForeignKey("portail_actions.IDaction"))
    action = relationship("Action")  
    
    def __init__(self , IDreservation=None, date=None, IDinscription=None, IDunite=None, IDaction=None, etat=None):
        if IDreservation != None :
            self.IDreservation = IDreservation
        self.date = date
        self.IDinscription = IDinscription
        self.IDunite = IDunite
        self.IDaction = IDaction
        self.etat = etat
        
    def __repr__(self):
        return '<IDreservation %d>' % (self.IDreservation)
        
    def as_dict(self):
        dict_temp = {}
        for c in self.__table__.columns :
            dict_temp[c.name] = getattr(self, c.name)
        return dict_temp
