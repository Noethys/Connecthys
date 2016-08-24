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
from application import app


# ------  Fonctions importables depuis les templates ----------

def CallFonction(fonction="", *args):
    """ Pour appeller directement une fonction Utils depuis Python """
    return utility_processor()[fonction](*args)
    
@app.context_processor
def utility_processor():
    """ Variables accessibles dans tous les templates """
    
    def GetNow():
        return datetime.datetime.now() 
        
    def GetToday():
        return datetime.date.today() 
        
    def Formate_montant(montant, symbole=u'€'):
        return u"{0:.2f} {1}".format(montant, symbole)

    def DateDDEnFr(date):
        """ Transforme une date DD en date FR """
        if date == None : return ""
        return date.strftime("%d/%m/%Y")
        
    def DateDDEnEng(date):
        """ Transforme une date DD en date Eng avec tirets """
        if date == None : return ""
        return date.strftime("%Y-%m-%d")

    def DateDDEnFrComplet(date):
        """ Transforme une date DD en date FR """
        if date == None : return ""
        jours = [u"Lundi", u"Mardi", u"Mercredi", u"Jeudi", u"Vendredi", u"Samedi", u"Dimanche"]
        mois = ["janvier", u"février", "mars", "avril", "mai", "juin", "juillet", u"août", "Septembre", "Octobre", u"novembre", u"décembre"]
        return u"%s %d %s %d" % (jours[date.weekday()], date.day, mois[date.month-1], date.year)

    def DateEngEnDD(date):
        if date in (None, "", "None") : return None
        if type(date) == datetime.date : return date
        return datetime.date(int(date[:4]), int(date[5:7]), int(date[8:10]))

    def DateDTEnHeureFr(datetm):
        """ Transforme une datetime en Heure FR """
        if datetm == None : return ""
        return datetm.strftime("%H:%M")
    
    def DateEngFr(textDate):
        if textDate in (None, "") : return ""
        if type(textDate) == datetime.date : return DateDDEnFr(textDate)
        text = str(textDate[8:10]) + "/" + str(textDate[5:7]) + "/" + str(textDate[:4])
        return text
    
    def IsUniteOuverte(unite=None, date=None, dict_planning={}):
        for IDunite_conso in unite.Get_unites_principales() :
            if not IDunite_conso in dict_planning["dict_ouvertures"][date] :
                return False
        return True
    
    def GetEtatFondCase(unite=None, date=None, dict_planning={}):
        dict_conso_par_unite_resa = dict_planning["dict_conso_par_unite_resa"]
        if dict_conso_par_unite_resa.has_key(date) :
            if dict_conso_par_unite_resa[date].has_key(unite) :
                etat = dict_conso_par_unite_resa[date][unite]
                return etat
        return None
        
    def GetEtatCocheCase(unite=None, date=None, dict_planning={}):
        dict_reservations = dict_planning["dict_reservations"]
        if dict_reservations != None :
        
            # Recherche dans le dictionnaire des réservations si la case est cochée
            if dict_reservations.has_key(date) :
                if dict_reservations[date].has_key(unite.IDunite) :
                    #return True
                    if dict_reservations[date][unite.IDunite] == 1:
                        return True
                    else :
                        return False
            
        else :
            # S'il n'y a aucune réservation sur cette ligne, on coche la conso
            if GetEtatFondCase(unite, date, dict_planning) != None :
                return True
        
        return False
    
    def GetDictDatesAttente(dict_planning={}):
        dict_conso_par_unite_resa = dict_planning["dict_conso_par_unite_resa"]
        dict_dates_attente = {}
        for date, dict_unites in dict_conso_par_unite_resa.iteritems() :
            for unite, etat in dict_unites.iteritems() :
                if etat == "attente" :
                    if not dict_dates_attente.has_key(date) :
                        dict_dates_attente[date] = 0
                    dict_dates_attente[date] += 1
        return dict_dates_attente
    
    def GetNbreDatesAttente(dict_planning={}):
        return len(GetDictDatesAttente(dict_planning))
    
    def GetNumSemaine(date):
        return date.isocalendar()[1]
        
    def GetIconeFichier(nomFichier=""):
        """ Retourne une icône selon le type de fichier (pdf, word, autre) """
        if nomFichier in (None, "") :
            return None
        if nomFichier.endswith(".pdf"):
            return "fa-file-pdf-o"
        elif nomFichier.endswith(".doc") or nomFichier.endswith(".docx"):
            return "fa-file-word-o"
        elif nomFichier.endswith(".txt"):
            return "fa-file-text-o"
        elif nomFichier.endswith(".jpg") or nomFichier.endswith(".png"):
            return "fa-file-image-o"
        else :
            return "fa-file-o"

        
    return dict(
        GetNow=GetNow,
        GetToday=GetToday,
        Formate_montant=Formate_montant,
        DateDDEnFr=DateDDEnFr,
        DateDDEnFrComplet=DateDDEnFrComplet,
        DateDTEnHeureFr=DateDTEnHeureFr,
        IsUniteOuverte=IsUniteOuverte,
        GetEtatFondCase=GetEtatFondCase,
        GetEtatCocheCase=GetEtatCocheCase,
        DateDDEnEng=DateDDEnEng,
        DateEngEnDD=DateEngEnDD,
        DateEngFr=DateEngFr,
        GetDictDatesAttente=GetDictDatesAttente,
        GetNbreDatesAttente=GetNbreDatesAttente,
        GetNumSemaine=GetNumSemaine,
        GetIconeFichier=GetIconeFichier,
        )

        
# ------  Fonctions non importables depuis les templates ----------

def GetVersionTuple(version=""):
    """ Renvoie un numéro de version donné au format tuple """
    temp = []
    for caract in version.split(".") :
        temp.append(int(caract))
    return tuple(temp)

    