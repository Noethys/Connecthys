#!/usr/bin/env python
# -*- coding: utf-8 -*-
#--------------------------------------------------------------
# Application :    Connecthys, le portail internet de Noethys
# Site internet :  www.noethys.com
# Auteur:          Ivan LUCAS
# Copyright:       (c) 2010-16 Ivan LUCAS
# Licence:         Licence GNU GPL
#--------------------------------------------------------------

import os
import os.path
REP_APPLICATION = os.path.abspath(os.path.dirname(__file__))
REP_CONNECTHYS = os.path.dirname(REP_APPLICATION)

import urllib
import urllib2
import zipfile


def GetVersionFromInt(version_int):
    version_liste = []
    for caract in str(version_int) :
        try :
            version_liste.append(int(caract))
        except :
            pass
    return tuple(version_liste)
    
def GetVersionTuple(version=""):
    """ Renvoie un numéro de version donné au format tuple """
    temp = []
    for caract in version.split(".") :
        temp.append(int(caract))
    return tuple(temp)

def GetVersionStr(version=()):
    """ Convertit un numéro de version tuple en str """
    return ".".join([str(x) for x in version]) 
    
def LectureFichierVersion(liste_lignes=[]):
    """ Lit un fichier de versions """
    liste_versions = []
    for ligne in liste_lignes :
        if ligne.startswith("version") :
            ligne = ligne.replace("\n", "")
            dict_elements = {}
            liste_elements = ligne.split(" # ")
            for element in liste_elements :
                cle, valeur = element.split("=")
                dict_elements[cle] = valeur
            liste_versions.append(dict_elements)
    return liste_versions

def GetLastVersionFromListe(liste_versions=[], format_version=tuple):
    """ Retourne le dernier numéro de version de la liste. Format_version = tuple ou str """
    version = liste_versions[-1]["version"]
    if format_version == str :
        return version
    if format_version == tuple :
        return GetVersionTuple(version)

def GetVersionActuelle(format_version=str):
    # Lecture du fichier des versions
    cheminFichier = os.path.join(REP_CONNECTHYS, "versions.txt")
    fichier = open(cheminFichier, mode='r')
    liste_lignes = fichier.readlines()
    fichier.close()
    
    # Formatage du fichier des versions en dict
    liste_versions = LectureFichierVersion(liste_lignes)
    
    # Recherche la version locale de Connecthys
    version_connecthys = GetLastVersionFromListe(liste_versions, format_version)
    return version_connecthys
    
def GetListeVersionOnline():
    # Recherche la version de Connecthys disponible sur Github
    fichier = urllib2.urlopen("https://raw.githubusercontent.com/Noethys/Connecthys/master/connecthys/versions.txt", timeout=5)
    liste_lignes_online = fichier.readlines()
    fichier.close()
    
    # Formatage du fichier des versions en dict
    liste_versions_online = LectureFichierVersion(liste_lignes_online)
    return liste_versions_online
    
def Recherche_update(version_noethys=[], mode="", app=None):
    app.logger.debug("Recherche d'une update...")
    app.logger.debug("Version de Noethys : %s (Mode : %s)" % (GetVersionStr(version_noethys), mode))
    
    # Recherche version actuelle de Connecthys
    version_connecthys = GetVersionActuelle(format_version=tuple)
    app.logger.debug("Version actuelle de connecthys: %s" % GetVersionStr(version_connecthys))
    
    # Recherche la liste des version en ligne sur Github
    try :
        liste_versions_online = GetListeVersionOnline()
    except Exception, err :
        app.logger.debug("La liste des versions n'a pas pu etre telechargee sur Github.")
        app.logger.debug(err)
        return u"La liste des versions n'a pas pu être téléchargée."
        
    # Analyse la liste pour trouver la version la plus adaptée
    version_ideale = [0, 0, 0]
    for ligne in liste_versions_online :
        if ligne.has_key("version") and ligne.has_key("version_min_noethys") :
            version_ligne = GetVersionTuple(ligne["version"])
            version_min_noethys = GetVersionTuple(ligne["version_min_noethys"])
            if version_noethys >= version_min_noethys :
                version_ideale = version_ligne
    
    if version_ideale > version_connecthys :
        app.logger.debug("Nouvelle version trouvee : %s" % GetVersionStr(version))
        return Update(version_ideale, mode, app)
    else :
        app.logger.debug("Pas de nouvelle version disponible.")
        return u"Pas de nouvelle version disponible."
            
def Update(version=[], mode="", app=None):
    """ Procédure de mise à jour de Connecthys """
    
    # Téléchargement
    try :
        app.logger.debug("Telechargement de la version %s sur Github..." % GetVersionStr(version))
        url_telechargement = "https://github.com/Noethys/Connecthys/archive/%s.zip" % GetVersionStr(version)
        fichier_zip = os.path.join(REP_CONNECTHYS, "connecthys.zip")
        urllib.urlretrieve(url_telechargement, fichier_zip)
    except Exception, err :
        app.logger.debug("La nouvelle version '%s' n'a pas pu etre telechargee." % GetVersionStr(version))
        app.logger.debug(err)
        return "La nouvelle version %s n'a pas pu etre téléchargée." % GetVersionStr(version)

    # Dezippage
    app.logger.debug("Dezippage du zip...")
    zfile = zipfile.ZipFile(fichier_zip, 'r')
    liste_fichiers = zfile.namelist()
    
    # Liste des exceptions
    if mode == "wsgi" :
        liste_exceptions = ["/lib/", "connecthys.cgi", "run.py"]
    else :
        liste_exceptions = []
        
    prefixe = "Connecthys-%s/connecthys/" % GetVersionStr(version)
    chemin_dest = os.path.join(REP_CONNECTHYS, "")
    
    for i in liste_fichiers:
        
        valide = True
        for exception in liste_exceptions :
            if exception in i :
                valide = False
            
        if i.startswith(prefixe) and valide == True :
            d = i.replace(prefixe, "")
            if len(d) > 1 :
                if os.path.isdir(os.path.join(chemin_dest, i)) or "2.5" in i or "." not in d :
                    try: os.makedirs(os.path.join(chemin_dest, d))
                    except: pass
                else:
                    try: os.makedirs(os.path.join(chemin_dest, os.path.dirname(d)))
                    except: pass
                    data = zfile.read(i)
                    fp = open(os.path.join(chemin_dest, d), "wb")
                    fp.write(data)
                    fp.close()

    zfile.close()
    
    # Suppression du fichier ZIP
    app.logger.debug("Suppression du zip...")
    os.remove(fichier_zip)
    
    app.logger.debug("Mise a jour effectuee.")
    return u"Mise à jour vers la version %s effectuée avec succès." % GetVersionStr(version)
    