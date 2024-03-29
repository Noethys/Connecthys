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
from Crypto.Hash import SHA256
import shutil
import os.path
import traceback
import six
from dateutil import relativedelta
import sqlalchemy
from sqlalchemy.dialects import mysql


try :
    # Imports Sqlalchemy_flask pour Connecthys
    from application import db, app, utils
    if app.config.get("PREFIXE_TABLES","") == "" :
        PREFIXE_TABLES = ""
    else :
        PREFIXE_TABLES = app.config["PREFIXE_TABLES"] + "_"
    Base = db.Model
    ForeignKey = db.ForeignKey
    Column = db.Column
    Date = db.Date
    DateTime = db.DateTime
    Integer = db.Integer
    String = db.String
    Float = db.Float
    Text = db.Text
    relationship = db.relationship
    import flask_migrate
    
    REP_APPLICATION = os.path.abspath(os.path.dirname(__file__))
    REP_CONNECTHYS = os.path.dirname(REP_APPLICATION)
    REP_MIGRATIONS = os.path.join(REP_CONNECTHYS, "migrations")
    
except Exception as err:
    # Imports Sqlalchemy pour Noethys
    from sqlalchemy import create_engine, ForeignKey, Column, Date, Integer, String, Float, DateTime, Text
    from sqlalchemy.orm import relationship, sessionmaker
    from sqlalchemy.ext.declarative import declarative_base
    Base = declarative_base()
    PREFIXE_TABLES = ""


def GetVersionDB():
    try :
        version = Parametre.query.filter_by(nom="version").first().parametre
    except Exception as err :
        return None
    return version
    

def CreationDB():
    """ Création de la DB """
    with app.app_context():
        if "mysql" in app.config["SQLALCHEMY_DATABASE_URI"] :
            
            # Création d'une base MySQL
            app.logger.info("Creation de la base de donnees MySQL si besoin...")
            import sqlalchemy
            temp = app.config["SQLALCHEMY_DATABASE_URI"].split("/")
            url = temp[0] + "//" + temp[2]
            nom_db = temp[3].split("?")[0]
            engine = sqlalchemy.create_engine(url)
            engine.execute("CREATE DATABASE IF NOT EXISTS %s;" % nom_db)
            engine.execute("USE %s;" % nom_db) 
            engine.dispose()

        app.logger.info("Creation des tables des donnees...")
        db.create_all()
        app.logger.info("Creation ok.")
        
        if os.path.isdir(REP_MIGRATIONS) :
            app.logger.info("Suppression du repertoire migrations...")
            shutil.rmtree(REP_MIGRATIONS)
        
        app.logger.info("Initialisation de la migration de sqlalchemy...")
        flask_migrate.init(directory=REP_MIGRATIONS)
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
            flask_migrate.migrate(directory=REP_MIGRATIONS)
            app.logger.info("Migrate - Migration ok.")
        except SystemExit as e:
            app.logger.info("SystemQuit -> Erreur dans migration > migrate")
            app.logger.info(traceback.format_exc())
        except Exception as err :
            app.logger.info("Erreur dans migration > migrate.")
            app.logger.info(err)

        app.logger.info("Upgrade de la base de donnees...")
        try :
            flask_migrate.upgrade(directory=REP_MIGRATIONS)
            app.logger.info("Migrate - Upgrade ok.")
        except SystemExit as e:
            app.logger.info("SystemQuit -> Erreur dans migration > upgrade.")
            app.logger.info(traceback.format_exc())
        except Exception as err :
            app.logger.info("Erreur dans migration > upgrade.")
            app.logger.info(err)
            
            # Si la revision n'existe pas
            if "Can't locate revision" in str(err) :
                app.logger.info("Suppression table alembic_version...")
                result = db.session.execute("DROP TABLE IF EXISTS alembic_version;")
                app.logger.info("Suppression du repertoire migrations...")
                shutil.rmtree(REP_MIGRATIONS)
                flask_migrate.init(directory=REP_MIGRATIONS)
                flask_migrate.migrate()

        # Mémorisation du nouveau numéro de version dans la DB
        m = Parametre.query.filter_by(nom="version").first()
        m.parametre=app.config["VERSION_APPLICATION"]
        db.session.commit()

def RepairDB():
    """ Tentative de réparation de la DB """
    with app.app_context():
        app.logger.info("Tentative de reparation de la DB")

        # Création du répertoire migrations si manquant
        if os.path.isdir(REP_MIGRATIONS) == False :
            app.logger.info("Repertoire Migrations manquant -> Initialisation de flask_migrate maintenant...")
            try :
                flask_migrate.init(directory=REP_MIGRATIONS)
            except SystemExit as e:
                pass
            except Exception as err:
                pass
        else:
            # Suppression de la table alembic et du répertoire des versions
            app.logger.info("Suppression table alembic_version...")
            result = db.session.execute("DROP TABLE IF EXISTS alembic_version;")
            app.logger.info("Suppression du repertoire migrations...")
            shutil.rmtree(REP_MIGRATIONS)
            flask_migrate.init(directory=REP_MIGRATIONS)
            flask_migrate.migrate()

        # Enregistre la dernière num_version dans la table alembic
        app.logger.info("Stamp...")
        try:
            flask_migrate.stamp(directory=REP_MIGRATIONS)
        except Exception as err:
            app.logger.info("Erreur dans migration > repair.")
            app.logger.info(err)



class Parametre(Base):
    __tablename__ = "%sportail_parametres" % PREFIXE_TABLES
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
    __tablename__ = "%sportail_users" % PREFIXE_TABLES
    IDuser = Column(Integer, primary_key=True)
    identifiant = Column(String(20), unique=True, index=True)
    password = Column(String(300))
    nom = Column(String(300))
    email = Column(String(300))
    role = Column(String(80))
    IDfamille = Column(Integer, index=True)
    IDutilisateur = Column(Integer, index=True)
    actif = Column(Integer)
    session_token = Column(String(200))
    last_maj_password = Column(DateTime)
    parametres = Column(String(400))
    infos = {}
    
    def __init__(self , IDuser=None, identifiant=None, decryptpassword=None, cryptpassword=None, nom=None, email=None, role="famille", IDfamille=None, IDutilisateur=None, actif=1, session_token=None, parametres=None):
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
        self.IDutilisateur = IDutilisateur
        self.actif = actif
        self.session_token = session_token
        self.parametres = parametres

    def SetCustomPassword(self, password=""):
        self.password = "custom" + SHA256.new(password.encode('utf-8')).hexdigest()
        self.last_maj_password = datetime.datetime.now()
        db.session.commit()

    def check_password(self, password):
        #resultat = sha256_crypt.verify(password, self.password) # Version passlib
        try :
            resultat = SHA256.new(password.encode('utf-8')).hexdigest() == self.password.replace("custom", "")
            return resultat
        except :
            return False
        
    def is_authenticated(self):
        return True
 
    def is_active(self):
        if self.actif == 0 :
            return False
        else :
            return True
 
    def is_anonymous(self):
        return False
 
    def get_id(self):
        return six.text_type(self.session_token)
 
    def __repr__(self):
        return '<User %d>' % (self.IDuser)
    
    def get_image(self):
        # if self.role == "utilisateur" :
        #     return 'img/admin.png'
        return 'img/utilisateur.png'
    
    def SetInfos(self, key="", valeur=None):
        self.infos[key] = valeur
        
    def GetInfos(self, key=""):
        if key in self.infos :
            return self.infos[key]
        return None

    def GetNom(self):
        return utils.CallFonction("DecrypteChaine", self.nom)

    def GetParametres(self):
        dict_parametres = {}
        if self.parametres:
            for parametre in self.parametres.split("##"):
                nom, valeur = parametre.split("==")
                dict_parametres[nom] = valeur
        return dict_parametres

    def Is_paiement_ligne_actif(self, dict_parametres=None):
        if GetParametre(nom="PAIEMENT_EN_LIGNE_ACTIF", dict_parametres=dict_parametres, defaut="False") == "True":
            if GetParametre(nom="PAIEMENT_OFF_SI_PRELEVEMENT", dict_parametres=dict_parametres, defaut="False") == "True" and self.GetParametres().get("prelevement_auto", "0") == "1":
                return False
            return True
        return False


        
class Facture(Base):
    __tablename__ = "%sportail_factures" % PREFIXE_TABLES
    IDfacture = Column(Integer, primary_key=True)
    IDfamille = Column(Integer, index=True)
    numero = Column(String(50))
    date_edition = Column(Date)
    date_debut = Column(Date)
    date_fin = Column(Date)
    montant = Column(Float)
    montant_regle = Column(Float)
    montant_solde = Column(Float)
    IDregie = Column(Integer)
    en_cours_paiement = Column(Integer)
    
    def __init__(self , IDfacture=None, IDfamille=None, numero=None, date_edition=None, \
                        date_debut=None, date_fin=None, montant=0.0, montant_regle=0.0, \
                        montant_solde=0.0, IDregie=0, en_cours_paiement=0):
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
        self.IDregie = IDregie
        self.en_cours_paiement = en_cours_paiement
 
    def __repr__(self):
        return '<Facture %d>' % (self.IDfacture)


class Prefacturation(Base):
    __tablename__ = "%sportail_prefacturation" % PREFIXE_TABLES
    IDprefacturation = Column(Integer, primary_key=True)
    IDfamille = Column(Integer, index=True)
    IDperiode = Column(Integer)
    montant = Column(Float)
    montant_regle = Column(Float)
    montant_solde = Column(Float)

    def __init__(self, IDprefacturation=None, IDfamille=None, IDperiode=None, montant=0.0, montant_regle=0.0, montant_solde=0.0):
        if IDprefacturation != None:
            self.IDprefacturation = IDprefacturation
        self.IDfamille = IDfamille
        self.IDperiode = IDperiode
        self.montant = montant
        self.montant_regle = montant_regle
        self.montant_solde = montant_solde

    def __repr__(self):
        return '<Prefacturation %d>' % (self.IDprefacturation)

    def get_periode(self):
        periode = Periode.query.filter_by(IDperiode=self.IDperiode).first()
        return periode

    def get_activite(self, periode=None):
        activite = Activite.query.filter_by(IDactivite=periode.IDactivite).first()
        return activite


class Paiement(Base):
    __tablename__ = "%sportail_paiements" % PREFIXE_TABLES
    IDpaiement = Column(Integer, primary_key=True)
    factures_ID = Column(String(50))
    IDfamille = Column(Integer, index=True)
    IDtransaction = Column(String(50))
    refdet = Column(String(50))
    montant = Column(Float)
    objet = Column(String(50))
    saisie = Column(String(5))
    resultrans = Column(String(5))
    numauto = Column(String(10))
    dattrans = Column(String(15))
    heurtrans = Column(String(15))
    systeme_paiement = Column(String(50))
    resultat = Column(String(50))
    message = Column(String(450))
    ventilation = Column(String(100000))
    horodatage = Column(DateTime)

    def __init__(self, IDpaiement=None, factures_ID=None, IDfamille=None, IDtransaction=None, refdet=None, \
                        montant = 0.0, objet=None, saisie=None, resultrans=None, numauto=None, dattrans=None, \
                        heurtrans=None, systeme_paiement=None, resultat=None, message=None, ventilation=None, horodatage=None):
        if IDpaiement != None :
            self.IDpaiement = IDpaiement
        self.factures_ID = factures_ID
        self.IDfamille = IDfamille
        self.IDtransaction = IDtransaction
        self.refdet = refdet
        self.montant = montant
        self.objet = objet
        self.saisie = saisie
        self.resultrans = resultrans
        self.numauto = numauto
        self.dattrans = dattrans
        self.heurtrans = heurtrans
        self.systeme_paiement = systeme_paiement
        self.resultat = resultat
        self.message = message
        self.ventilation = ventilation
        self.horodatage = horodatage

    def __repr__(self):
        return '<Paiement %d>' % (self.IDpaiement)


        
class Renseignement(Base):
    __tablename__ = "%sportail_renseignements" % PREFIXE_TABLES
    IDrenseignement = Column(Integer, primary_key=True)
    champ = Column(String(100))
    valeur = Column(String(255))
    IDaction = Column(Integer, ForeignKey("%sportail_actions.IDaction" % PREFIXE_TABLES))
    action = relationship("Action")  
    
    def __init__(self , IDrenseignement=None, champ=None, valeur=None, IDaction=None):
        if IDrenseignement != None :
            self.IDrenseignement = IDrenseignement
        self.champ = champ
        self.valeur = valeur
        self.IDaction = IDaction
        
    def __repr__(self):
        return '<IDrenseignement %d>' % (self.IDrenseignement)
        
    def as_dict(self):
        dict_temp = {}
        for c in self.__table__.columns :
            dict_temp[c.name] = getattr(self, c.name)
        return dict_temp


class Action(Base):
    __tablename__ = "%sportail_actions" % PREFIXE_TABLES
    IDaction = Column(Integer, primary_key=True)
    horodatage = Column(DateTime)
    IDfamille = Column(Integer, index=True)
    IDindividu = Column(Integer)
    IDutilisateur = Column(Integer)
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
    IDpaiement = Column(Integer)
    ventilation = Column(String(100000))
    
    reservations = relationship("Reservation")
    renseignements = relationship("Renseignement")
    reservations_locations = relationship("Reservation_location")
    
    def __init__(self, horodatage=None, IDfamille=None, IDindividu=None, IDutilisateur=None, categorie=None, action=None, description=None, \
                        commentaire=None, parametres=None, etat=None, traitement_date=None, IDperiode=None, ref_unique=None, reponse=None, \
                        IDpaiement=None, ventilation=None):
        if horodatage == None :
            self.horodatage = datetime.datetime.now()
        else :
            self.horodatage = horodatage
        self.IDfamille = IDfamille
        self.IDindividu = IDindividu
        self.IDutilisateur = IDutilisateur
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
        self.IDpaiement = IDpaiement
        self.ventilation = ventilation

    def GetParametres(self):
        dict_parametres = {}
        for param in self.parametres.split("#"):
            if "=" in param:
                key, valeur = param.split("=")
                dict_parametres[key] = valeur
        return dict_parametres
        
    def GetRefUnique(self):
        horodatage = self.horodatage.strftime("%Y%m%d%H%M%S%f")
        if self.IDfamille != None :
            ID = self.IDfamille
        if self.IDutilisateur != None :
            ID = self.IDutilisateur
        ref_unique = "%s%06d" % (horodatage, ID)
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
            
        # Ajout des renseignements dans le dict
        dict_temp["renseignements"] = []
        for renseignement in self.renseignements :
            dict_temp["renseignements"].append(renseignement.as_dict())

        # Ajout des locations dans le dict
        dict_temp["locations"] = []
        try:
            for reservation_location in self.reservations_locations :
                dict_temp["locations"].append(reservation_location.as_dict())
        except:
            pass

        return dict_temp

        
       
class Reglement(Base):
    __tablename__ = "%sportail_reglements" % PREFIXE_TABLES
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
    __tablename__ = "%sportail_pieces_manquantes" % PREFIXE_TABLES
    IDpiece_manquante = Column(Integer, primary_key=True)
    IDfamille = Column(Integer, index=True)
    IDtype_piece = Column(Integer)
    IDindividu = Column(Integer)
    nom = Column(String(300))
    
    def __init__(self , IDpiece_manquante=None, IDfamille=None, IDtype_piece=None, IDindividu=None, nom=None):
        if IDpiece_manquante != None :
            self.IDpiece_manquante = IDpiece_manquante
        self.IDfamille = IDfamille
        self.IDtype_piece = IDtype_piece
        self.IDindividu = IDindividu
        self.nom = nom
 
    def __repr__(self):
        return '<IDpiece_manquante %d>' % (self.IDpiece_manquante)

    def GetNom(self):
        return utils.CallFonction("DecrypteChaine", self.nom)


   
class Type_piece(Base):
    __tablename__ = "%sportail_types_pieces" % PREFIXE_TABLES
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
    __tablename__ = "%sportail_cotisations_manquantes" % PREFIXE_TABLES
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



class Cotisation(Base):
    __tablename__ = "%sportail_cotisations" % PREFIXE_TABLES
    IDcotisation = Column(Integer, primary_key=True)
    IDfamille = Column(Integer, index=True)
    IDindividu = Column(Integer)
    numero = Column(String(50))
    date_debut = Column(Date)
    date_fin = Column(Date)
    nom_cotisation = Column(String(200))
    nom_unite = Column(String(200))
    prenom_individu = Column(String(200))

    def __init__(self, IDcotisation=None, IDfamille=None, IDindividu=None, numero=None, date_debut=None, date_fin=None,
                 nom_cotisation=None, nom_unite=None, prenom_individu=None):
        if IDcotisation != None:
            self.IDcotisation = IDcotisation
        self.IDfamille = IDfamille
        self.IDindividu = IDindividu
        self.numero = numero
        self.date_debut = date_debut
        self.date_fin = date_fin
        self.nom_cotisation = nom_cotisation
        self.nom_unite = nom_unite
        self.prenom_individu = prenom_individu

    def __repr__(self):
        return '<IDcotisation %d>' % (self.IDcotisation)

    def GetNumero(self):
        if self.numero != None :
            return self.numero
        else :
            return ""

    def GetNomComplet(self):
        return u"%s - %s" % (self.nom_cotisation, self.nom_unite)

    def GetBeneficiaire(self):
        if self.prenom_individu != None:
            return utils.CallFonction("DecrypteChaine", self.prenom_individu)
        else:
            return u"Famille"


class Categorie_produit(Base):
    __tablename__ = "%sportail_categories_produits" % PREFIXE_TABLES
    IDcategorie = Column(Integer, primary_key=True)
    nom = Column(String(200))

    def __init__(self, IDcategorie=None, nom=None):
        if IDcategorie != None:
            self.IDcategorie = IDcategorie
        self.nom = nom

    def __repr__(self):
        return '<IDcategorie %d>' % (self.IDcategorie)


class Produit(Base):
    __tablename__ = "%sportail_produits" % PREFIXE_TABLES
    IDproduit = Column(Integer, primary_key=True)
    IDcategorie = Column(Integer, index=True)
    nom = Column(String(200))
    quantite = Column(Integer)
    montant = Column(Float)
    nom_categorie = Column(String(200))
    activation_partage = Column(Integer)

    def __init__(self, IDproduit=None, IDcategorie=None, nom=None, quantite=None, montant=None, nom_categorie=None, activation_partage=None):
        if IDproduit != None:
            self.IDproduit = IDproduit
        self.IDcategorie = IDcategorie
        self.nom = nom
        self.quantite = quantite
        self.montant = montant
        self.nom_categorie = nom_categorie
        self.activation_partage = activation_partage

    def __repr__(self):
        return '<IDproduit %d>' % (self.IDproduit)


class Location(Base):
    __tablename__ = "%sportail_locations" % PREFIXE_TABLES
    IDlocation = Column(Integer, primary_key=True)
    IDfamille = Column(Integer, index=True)
    IDproduit = Column(Integer)
    date_debut = Column(DateTime)
    date_fin = Column(DateTime)
    quantite = Column(Integer)
    partage = Column(Integer)
    description = Column(String(200))

    def __init__(self, IDlocation=None, IDfamille=None, IDproduit=None, date_debut=None, date_fin=None, quantite=None, partage=None, description=None):
        if IDlocation != None:
            self.IDlocation = IDlocation
        self.IDfamille = IDfamille
        self.IDproduit = IDproduit
        self.date_debut = date_debut
        self.date_fin = date_fin
        self.quantite = quantite
        self.partage = partage
        self.description = description

    def __repr__(self):
        return '<IDlocation %d>' % (self.IDlocation)


class Reservation_location(Base):
    __tablename__ = "%sportail_reservations_locations" % PREFIXE_TABLES
    IDreservation = Column(Integer, primary_key=True)
    IDlocation = Column(String(100))
    date_debut = Column(DateTime)
    date_fin = Column(DateTime)
    IDproduit = Column(Integer)
    etat = Column(String(100))
    IDaction = Column(Integer, ForeignKey("%sportail_actions.IDaction" % PREFIXE_TABLES))
    action = relationship("Action")
    partage = Column(Integer)
    description = Column(String(200))

    def __init__(self, IDreservation=None, IDlocation=None, date_debut=None, date_fin=None, IDproduit=None, etat=None, IDaction=None, partage=None, description=None):
        if IDreservation != None:
            self.IDreservation = IDreservation
        self.IDlocation = IDlocation
        self.date_debut = date_debut
        self.date_fin = date_fin
        self.IDproduit = IDproduit
        self.etat = etat
        self.IDaction = IDaction
        self.partage = partage
        self.description = description

    def __repr__(self):
        return '<IDreservation %d>' % (self.IDreservation)

    def as_dict(self):
        dict_temp = {}
        for c in self.__table__.columns:
            dict_temp[c.name] = getattr(self, c.name)
        return dict_temp


class Activite(Base):
    __tablename__ = "%sportail_activites" % PREFIXE_TABLES
    IDactivite = Column(Integer, primary_key=True)
    nom = Column(String(300))
    inscriptions_affichage = Column(Integer)
    inscriptions_date_debut = Column(DateTime)
    inscriptions_date_fin = Column(DateTime)
    reservations_affichage = Column(Integer)
    unites_multiples = Column(Integer)
    reservations_limite = Column(String(50))
    reservations_absenti = Column(String(20))
    nbre_inscrits_max = Column(Integer)
    
    periodes = relationship("Periode")
    
    def __init__(self , IDactivite=None, nom=None, inscriptions_affichage=1, \
                inscriptions_date_debut=None, inscriptions_date_fin=inscriptions_date_debut, \
                reservations_affichage=1, unites_multiples=0, \
                reservations_limite=None, reservations_absenti=None, \
                nbre_inscrits_max=None):
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
        self.nbre_inscrits_max = nbre_inscrits_max
 
    def __repr__(self):
        return '<IDactivite %d>' % (self.IDactivite)
    
    def Get_nbre_periodes_actives(self):
        """ Compte le nombre de périodes actives ce jour """
        nbre = 0
        for periode in self.periodes :
            if periode.Is_active_today() :
                nbre += 1
        return nbre
    
    def Is_modification_allowed(self, date=None, dict_planning={}):
        """ Demande s'il est possible d'ajouter, modifier ou supprimer la réservation en fonction de la date """
        if self.reservations_limite != None :
            limite = self.reservations_limite.split("#")
            nbre_jours = int(limite[0])
            heure = limite[1]
            if len(limite) > 2 :
                options = limite[2]
            else :
                options = ""

            jours_semaine = [relativedelta.MO, relativedelta.TU, relativedelta.WE, relativedelta.TH, relativedelta.FR, relativedelta.SA, relativedelta.SU]
            date_limite = datetime.datetime(year=date.year, month=date.month, day=date.day, hour=int(heure[:2]), minute=int(heure[3:]))

            # Jour J-x
            if 0 <= nbre_jours <= 999:
                x = 1
                while x <= nbre_jours :
                    date_limite = date_limite - datetime.timedelta(days=1)
                    date_valide = True

                    # Vérifie que la date est hors week-end
                    if "weekends" in options and date_limite.weekday() in (5, 6) :
                        date_valide = False

                    # Vérifie que la date est hors fériés
                    if "feries" in options and utils.CallFonction("EstFerie", date_limite, dict_planning) == True :
                        date_valide = False

                    if date_valide == True :
                        x += 1

            # Lundi, mardi, mercredi... précédent
            if 1000 <= nbre_jours <= 1006:
                date_limite = date_limite - relativedelta.relativedelta(days=1, weekday=jours_semaine[nbre_jours-1000](-1))

            # Lundi, mardi, mercredi... de la semaine précédente
            if 2000 <= nbre_jours <= 2006:
                date_limite = date_limite - relativedelta.relativedelta(weekday=relativedelta.SU(-1)) - relativedelta.relativedelta(weekday=jours_semaine[nbre_jours-2000](-1))

            # Validation de la date limite
            if datetime.datetime.now() > date_limite:
                return False

        return True
        
        
class Individu(Base):
    __tablename__ = "%sportail_individus" % PREFIXE_TABLES
    IDrattachement = Column(Integer, primary_key=True)
    IDindividu = Column(Integer, index=True)
    IDfamille = Column(Integer)
    nom = Column(String(300))
    prenom = Column(String(300))
    IDcivilite = Column(Integer)
    IDcategorie = Column(Integer)
    date_naiss = Column(String(300))
    cp_naiss = Column(String(300))
    ville_naiss = Column(String(300))
    adresse_auto = Column(Integer)
    rue_resid = Column(String(300))
    cp_resid = Column(String(300))
    ville_resid = Column(String(300))
    tel_domicile = Column(String(300))
    tel_mobile = Column(String(300))
    mail = Column(String(300))
    profession = Column(String(300))
    employeur = Column(String(300))
    travail_tel = Column(String(300))
    travail_mail = Column(String(300))
                                    
    def __init__(self , IDrattachement=None, IDindividu=None, IDfamille=None, IDcategorie=None,
                                    nom=None, prenom=None, IDcivilite=None,
                                    date_naiss=None, cp_naiss=None, ville_naiss=None, 
                                    adresse_auto=None, rue_resid=None, cp_resid=None, ville_resid=None,
                                    tel_domicile=None, tel_mobile=None, mail=None, 
                                    profession=None, employeur=None, travail_tel=None, travail_mail=None, 
        ):
        if IDrattachement != None :
            self.IDrattachement = IDrattachement
        self.IDfamille = IDfamille
        self.IDindividu = IDindividu
        self.nom = nom
        self.prenom = prenom
        self.IDcivilite = IDcivilite
        self.IDcategorie = IDcategorie
        self.date_naiss = date_naiss
        self.cp_naiss = cp_naiss
        self.ville_naiss = ville_naiss
        self.adresse_auto = adresse_auto
        self.rue_resid = rue_resid
        self.cp_resid = cp_resid
        self.ville_resid = ville_resid
        self.tel_domicile = tel_domicile
        self.tel_mobile = tel_mobile
        self.mail = mail
        self.profession = profession
        self.employeur = employeur
        self.travail_tel = travail_tel
        self.travail_mail = travail_mail 

    def __repr__(self):
        return '<IDindividu %d>' % (self.IDindividu)

    def get_image(self):
        if self.IDcivilite in (1, 4) :
            return "img/homme.png"
        if self.IDcivilite in (2, 3, 5) :
            return "img/femme.png"
        if self.IDcivilite in (6, 7, 8, 9):
            return "img/organisme.png"
        return 'img/homme.png'

    def get_date_naiss(self):
        if self.date_naiss in (None, "") :
            return ""
        today = datetime.date.today()
        if isinstance(self.date_naiss, six.text_type) or isinstance(self.date_naiss, str) :
            datenaiss = utils.CallFonction("DecrypteChaine", self.date_naiss)
            datenaiss = utils.CallFonction("DateEngEnDD", datenaiss)
        else :
            datenaiss = self.date_naiss
        age = today.year - datenaiss.year - ((today.month, today.day) < (datenaiss.month, datenaiss.day))
        return u"%d ans" % age

    def get_inscriptions(self, avec_periode_actives=False):
        liste_inscriptions = []
        liste_temp = Inscription.query.filter_by(IDfamille=self.IDfamille, IDindividu=self.IDindividu).filter((Inscription.date_desinscription==None)|(Inscription.date_desinscription>datetime.date.today())).all()
        if avec_periode_actives == True:
            for inscription in liste_temp :
                if inscription.activite.Get_nbre_periodes_actives() > 0:
                    liste_inscriptions.append(inscription)
        else :
            liste_inscriptions = liste_temp
        return liste_inscriptions

    def get_adresse(self):
        if self.adresse_auto == None :
            rue = utils.CallFonction("ConvertToUnicode", self.rue_resid)
            cp = utils.CallFonction("ConvertToUnicode", self.cp_resid)
            ville = utils.CallFonction("ConvertToUnicode", self.ville_resid)
        else :
            autre_individu = Individu.query.filter_by(IDindividu=self.adresse_auto).first()
            rue = utils.CallFonction("ConvertToUnicode", autre_individu.rue_resid)
            cp = utils.CallFonction("ConvertToUnicode", autre_individu.cp_resid)
            ville = utils.CallFonction("ConvertToUnicode", autre_individu.ville_resid)
        
        modifiee = False
        
        complete = u"%s %s %s" % (rue, cp, ville)
        
        dict_adresse = {"rue" : rue, "cp" : cp, "ville" : ville, "complete" : complete, "modifiee" : modifiee}
        return dict_adresse

    def GetRenseignement(self, nom=""):
        valeur = getattr(self, nom)
        return utils.CallFonction("DecrypteChaine", valeur)
    
    
        
class Inscription(Base):
    __tablename__ = "%sportail_inscriptions" % PREFIXE_TABLES
    IDinscription = Column(Integer, primary_key=True)
    IDfamille = Column(Integer, index=True)
    IDindividu = Column(Integer, index=True)
    date_desinscription = Column(Date)

    IDactivite = Column(Integer, ForeignKey("%sportail_activites.IDactivite" % PREFIXE_TABLES))
    activite = relationship("Activite")  

    IDgroupe = Column(Integer, ForeignKey("%sportail_groupes.IDgroupe" % PREFIXE_TABLES))
    groupe = relationship("Groupe")  
    
    def __init__(self , IDinscription=None, IDindividu=None, IDfamille=None, IDactivite=None, IDgroupe=None, date_desinscription=None):
        if IDinscription != None :
            self.IDinscription = IDinscription
        self.IDindividu = IDindividu
        self.IDfamille = IDfamille
        self.IDactivite = IDactivite
        self.IDgroupe = IDgroupe
        self.date_desinscription = date_desinscription
        
    def __repr__(self):
        return '<IDinscription %d>' % (self.IDinscription)

    def get_individu(self):
        individu = Individu.query.filter_by(IDindividu=self.IDindividu).first()
        return individu


                    
class Periode(Base):
    __tablename__ = "%sportail_periodes" % PREFIXE_TABLES
    IDperiode = Column(Integer, primary_key=True)
    nom = Column(String(300))
    date_debut = Column(Date)
    date_fin = Column(Date)
    affichage_date_debut = Column(DateTime)
    affichage_date_fin = Column(DateTime)
    introduction = Column(String(1000))
    prefacturation = Column(Integer)
    
    IDactivite = Column(Integer, ForeignKey("%sportail_activites.IDactivite" % PREFIXE_TABLES))
    activite = relationship("Activite")  
    
    def __init__(self , IDperiode=None, IDactivite=None, nom=None, date_debut=None, date_fin=None, \
                        affichage_date_debut=None, affichage_date_fin=None, introduction=None, prefacturation=None):
        if IDperiode != None :
            self.IDperiode = IDperiode
        self.IDactivite = IDactivite
        self.nom = nom
        self.date_debut = date_debut
        self.date_fin = date_fin
        self.affichage_date_debut = affichage_date_debut
        self.affichage_date_fin = affichage_date_fin
        self.introduction = introduction
        self.prefacturation = prefacturation
        
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
    __tablename__ = "%sportail_groupes" % PREFIXE_TABLES
    IDgroupe = Column(Integer, primary_key=True)
    nom = Column(String(300))
    ordre = Column(Integer)
    IDactivite = Column(Integer)
    nbre_inscrits_max = Column(Integer)

    def __init__(self , IDgroupe=None, nom=None, IDactivite=None, ordre=None, nbre_inscrits_max=None):
        if IDgroupe != None :
            self.IDgroupe = IDgroupe
        self.nom = nom
        self.IDactivite = IDactivite
        self.ordre = ordre
        self.nbre_inscrits_max = nbre_inscrits_max
        
    def __repr__(self):
        return '<IDgroupe %d>' % (self.IDgroupe)
    
    def IsComplet(self):
        # Importation du nombre d'inscrits
        nbre_inscriptions_activite = Inscription.query.filter_by(IDactivite=self.IDactivite).filter(Inscription.date_desinscription==None).count()
        nbre_inscriptions_groupe = Inscription.query.filter_by(IDgroupe=self.IDgroupe).filter(Inscription.date_desinscription==None).count()
        
        # Importation des capacités max.
        nbre_inscrits_max_activite = Activite.query.filter_by(IDactivite=self.IDactivite).first().nbre_inscrits_max
        nbre_inscrits_max_groupe = self.nbre_inscrits_max
        
        # Vérification du groupe
        if nbre_inscrits_max_groupe != None :
            if nbre_inscriptions_groupe >= nbre_inscrits_max_groupe :
                return True
        
        # Vérification de l'activité
        if nbre_inscrits_max_activite != None :
            if nbre_inscriptions_activite >= nbre_inscrits_max_activite :
                return True

        # Sinon pas complet
        return False
    
    
    
        
class Unite(Base):
    __tablename__ = "%sportail_unites" % PREFIXE_TABLES
    IDunite = Column(Integer, primary_key=True)
    nom = Column(String(300))
    unites_principales = Column(String(300))
    unites_secondaires = Column(String(300))
    ordre = Column(Integer)
    
    IDactivite = Column(Integer, ForeignKey("%sportail_activites.IDactivite" % PREFIXE_TABLES))
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
    __tablename__ = "%sportail_ouvertures" % PREFIXE_TABLES
    IDouverture = Column(Integer, primary_key=True)
    date = Column(Date)
    IDunite = Column(Integer)
    IDgroupe = Column(Integer)
    
    def __init__(self , IDouverture=None, date=None, IDunite=None, IDgroupe=None):
        if IDouverture != None :
            self.IDouverture = IDouverture
        self.date = date
        self.IDunite = IDunite
        self.IDgroupe = IDgroupe
        
    def __repr__(self):
        return '<IDouverture %d>' % (self.IDouverture)


class Evenement(Base):
    __tablename__ = "%sportail_evenements" % PREFIXE_TABLES
    IDevenement = Column(Integer, primary_key=True)
    IDactivite = Column(Integer)
    IDunite = Column(Integer)
    IDgroupe = Column(Integer)
    date = Column(Date)
    nom = Column(String(200))
    description = Column(String(500))
    heure_debut = Column(String(20))
    heure_fin = Column(String(20))

    def __init__(self, IDevenement=None, IDactivite=None, IDunite=None, IDgroupe=None, date=None, nom=None, description=None, heure_debut=None, heure_fin=None):
        if IDevenement != None:
            self.IDevenement = IDevenement
        self.IDactivite = IDactivite
        self.IDunite = IDunite
        self.IDgroupe = IDgroupe
        self.date = date
        self.nom = nom
        self.description = description
        self.heure_debut = heure_debut
        self.heure_fin = heure_fin

    def __repr__(self):
        return '<IDevenement %d>' % (self.IDevenement)



class Ferie(Base):
    __tablename__ = "%sportail_feries" % PREFIXE_TABLES
    IDferie = Column(Integer, primary_key=True)
    type = Column(String(10))
    nom = Column(String(100))
    jour = Column(Integer)
    mois = Column(Integer)
    annee = Column(Integer)
    
    def __init__(self , IDferie=None, type=None, nom=None, jour=None, mois=None, annee=None):
        if IDferie != None :
            self.IDferie = IDferie
        self.type = type
        self.nom = nom
        self.jour = jour
        self.mois = mois
        self.annee = annee
        
    def __repr__(self):
        return '<IDferie %d>' % (self.IDferie)       
        
        
class Consommation(Base):
    __tablename__ = "%sportail_consommations" % PREFIXE_TABLES
    IDconsommation = Column(Integer, primary_key=True)
    date = Column(Date)
    etat = Column(String(20))
    IDunite = Column(Integer)
    IDinscription = Column(Integer)
    IDevenement = Column(Integer)

    def __init__(self , IDconsommation=None, date=None, IDunite=None, IDinscription=None, etat=None, IDevenement=None):
        if IDconsommation != None :
            self.IDconsommation = IDconsommation
        self.date = date
        self.IDunite = IDunite
        self.IDinscription = IDinscription
        self.etat = etat
        self.IDevenement = IDevenement
        
    def __repr__(self):
        return '<IDconsommation %d>' % (self.IDconsommation)
        

class Reservation(Base):
    __tablename__ = "%sportail_reservations" % PREFIXE_TABLES
    IDreservation = Column(Integer, primary_key=True)
    date = Column(Date)
    etat = Column(Integer)
    IDinscription = Column(Integer)
    IDunite = Column(Integer)
    IDaction = Column(Integer, ForeignKey("%sportail_actions.IDaction" % PREFIXE_TABLES))
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

        
       
        

class Message(Base):
    __tablename__ = "%sportail_messages" % PREFIXE_TABLES
    IDmessage = Column(Integer, primary_key=True)
    titre = Column(String(255))
    texte = Column(String(1000))
    IDfamille = Column(Integer, index=True)
    affichage_date_debut = Column(DateTime)
    affichage_date_fin = Column(DateTime)

    def __init__(self, IDmessage=None, titre=None, texte=None, IDfamille=None, \
                        affichage_date_debut=affichage_date_debut, affichage_date_fin=affichage_date_fin):
        if IDmessage != None :
            self.IDmessage = IDmessage
        self.titre = titre
        self.texte = texte
        self.IDfamille = IDfamille
        self.affichage_date_debut = affichage_date_debut
        self.affichage_date_fin = affichage_date_fin
 
    def __repr__(self):
        return '<IDmessage %d>' % (self.IDmessage)
    
    def Is_actif_today(self):
        """ Vérifie si le message est actif ce jour """
        now = datetime.datetime.now()
        if self.affichage_date_debut == None or (now >= self.affichage_date_debut and now <= self.affichage_date_fin) :
            return True
        else :
            return False

    def Is_nouveau(self):
        """ Retourne si le message est nouveau ou non """
        if self.affichage_date_debut != None :
            now = datetime.datetime.now()
            if now >= self.affichage_date_debut and now <= (self.affichage_date_debut + datetime.timedelta(days=3)) :
                return True
        return False
        
        
        
class Regie(Base) :
    __tablename__ = "%sportail_regies" % PREFIXE_TABLES
    IDregie = Column(Integer, primary_key=True)
    nom = Column(String(255))
    numclitipi = Column(String(8))
    email_regisseur = Column(String(255))

    def __init__(self, IDregie=None, nom=None, numclitipi=None, email_regisseur=None) :
        if IDregie != None :
            self.IDregie = IDregie
        self.nom = nom
        self.numclitipi = numclitipi
        self.email_regisseur = email_regisseur

    def __repr__(self):
        return '<IDregie %d>' % (self.IDregie)



class Page(Base):
    __tablename__ = "%sportail_pages" % PREFIXE_TABLES
    IDpage = Column(Integer, primary_key=True)
    titre = Column(String(300))
    couleur = Column(String(100))
    ordre = Column(Integer)

    def __init__(self, IDpage=None, titre=None, couleur=None, ordre=None):
        if IDpage != None:
            self.IDpage = IDpage
        self.titre = titre
        self.couleur = couleur
        self.ordre = ordre

    def __repr__(self):
        return '<IDpage %d>' % (self.IDpage)



class Bloc(Base):
    __tablename__ = "%sportail_blocs" % PREFIXE_TABLES
    IDbloc = Column(Integer, primary_key=True)
    IDpage = Column(Integer)
    titre = Column(String(300))
    couleur = Column(String(100))
    categorie = Column(String(200))
    ordre = Column(Integer)
    parametres = Column(Text)

    def __init__(self, IDbloc=None, IDpage=None, titre=None, couleur=None, categorie=None, ordre=None, parametres=None):
        if IDbloc != None:
            self.IDbloc = IDbloc
        self.IDpage = IDpage
        self.titre = titre
        self.couleur = couleur
        self.categorie = categorie
        self.ordre = ordre
        self.parametres = parametres

    def __repr__(self):
        return '<IDbloc %d>' % (self.IDbloc)



class Element(Base):
    __tablename__ = "%sportail_elements" % PREFIXE_TABLES
    IDelement = Column(Integer, primary_key=True)
    IDbloc = Column(Integer)
    ordre = Column(Integer)
    titre = Column(String(300))
    categorie = Column(String(200))
    date_debut = Column(DateTime)
    date_fin = Column(DateTime)
    parametres = Column(Text)
    texte_html = Column(Text().with_variant(sqlalchemy.dialects.mysql.LONGTEXT, "mysql"))

    def __init__(self, IDelement=None, IDbloc=None, ordre=None, titre=None, categorie=None, date_debut=None, date_fin=None, parametres=None, texte_html=None):
        if IDelement != None:
            self.IDelement = IDelement
        self.IDbloc = IDbloc
        self.ordre = ordre
        self.titre = titre
        self.categorie = categorie
        self.date_debut = date_debut
        self.date_fin = date_fin
        self.parametres = parametres
        self.texte_html = texte_html

    def __repr__(self):
        return '<IDelement %d>' % (self.IDelement)






def GetParametre(nom="", dict_parametres=None, defaut=""):
    parametre = None
    # Si un dict_parametre est donné
    if dict_parametres != None :
        if nom in dict_parametres :
            parametre = dict_parametres[nom]
    else :
        # Sinon on cherche directement dans la base
        m = Parametre.query.filter_by(nom=nom).first()
        if m != None :
            parametre = m.parametre
    if parametre == None :
        return defaut
    else :
        return parametre

def GetDictParametres():
    liste_parametres = Parametre.query.all()
    dict_parametres = {}
    for parametre in liste_parametres :
        dict_parametres[parametre.nom] = parametre.parametre
    return dict_parametres
