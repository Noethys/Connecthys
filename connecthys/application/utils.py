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
from cryptage import AESCipher
import six

    
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

def DateDTEnFr(datetm):
    """ Transforme une datetime en FR """
    if datetm == None : return ""
    return datetm.strftime("%d/%m/%Y %H:%M")

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

def GetEvenementsOuverts(unite=None, date=None, dict_planning={}):
    liste_evenements = []
    for IDunite_conso in unite.Get_unites_principales() :
        if date in dict_planning["dict_evenements"] :
            if IDunite_conso in dict_planning["dict_evenements"][date]:
                for evenement in dict_planning["dict_evenements"][date][IDunite_conso]:
                    liste_evenements.append(evenement)
    return liste_evenements

def IsUniteModifiable(unite=None, date=None, dict_planning={}):
    # Recherche si l'activité autorise la modification
    modification_allowed = unite.activite.Is_modification_allowed(date, dict_planning)
    
    # Recherche si la date est passée
    if date < datetime.date.today() :
        modification_allowed = False
    
    # Si coche multiple désactivée, recherche si des unités de la ligne sont pointées
    if modification_allowed == True and dict_planning["periode"].activite.unites_multiples == 0 :
        for unite_temp in dict_planning["liste_unites"] :
            etat_case = GetEtatFondCase(unite_temp, date, dict_planning)
            if etat_case in ("present", "absenti", "absentj") :
                modification_allowed = False
    
    return modification_allowed

def GetEtatFondCase(unite=None, date=None, dict_planning={}):
    dict_conso_par_unite_resa = dict_planning["dict_conso_par_unite_resa"]
    if date in dict_conso_par_unite_resa :
        if unite in dict_conso_par_unite_resa[date] :
            etat = dict_conso_par_unite_resa[date][unite]
            return etat
    return None
    
def GetEtatCocheCase(unite=None, date=None, dict_planning={}):
    dict_reservations = dict_planning["dict_reservations"]
    if dict_reservations != None :
        
        # Recherche dans le dictionnaire des réservations si la case est cochée
        if date in dict_reservations :
            if unite.IDunite in dict_reservations[date] :
                if dict_reservations[date][unite.IDunite] == 1:
                    return True
                else :
                    return False
        
    # S'il n'y a aucune réservation sur cette ligne, on coche la conso
    if GetEtatFondCase(unite, date, dict_planning) != None :
        return True
    
    return False

def GetDictDatesAttente(dict_planning={}):
    dict_conso_par_unite_resa = dict_planning["dict_conso_par_unite_resa"]
    dict_dates_attente = {}
    for date, dict_unites in dict_conso_par_unite_resa.items() :
        for unite, etat in dict_unites.items() :
            if etat == "attente" or etat == "refus" :
                if date not in dict_dates_attente :
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
    
def GetNbrePeriodesActives(individu):
    nbre_periodes_actives = 0
    for inscription in individu.get_inscriptions() :
        if inscription.activite.Get_nbre_periodes_actives() > 0 :
            nbre_periodes_actives += 1
    return nbre_periodes_actives

def GetParametre(nom="", dict_parametres=None, defaut=""):
    parametre = None
    # Si un dict_parametre est donné
    if dict_parametres != None :
        if nom in dict_parametres :
            parametre = dict_parametres[nom]
    if parametre == None :
        return defaut
    else :
        return parametre

def GetJoursOuverts(dict_planning={}):
    liste_jours = []
    for date in dict_planning["liste_dates"] :
        num_jour = date.weekday()
        if num_jour not in liste_jours :
            liste_jours.append(num_jour)
    liste_jours.sort()
    return liste_jours

def EstFerie(date=None, dict_planning={}):
    jour = date.day
    mois = date.month
    annee = date.year        
    for ferie in dict_planning["liste_feries"] :
        if ferie.type == "fixe" :
            if ferie.jour == jour and ferie.mois == mois :
                return True
        else:
            if ferie.jour == jour and ferie.mois == mois and ferie.annee == annee :
                return True
    return False

def HasActivitesDisponiblesPourInscriptions(liste_activites=[]):
    for activite in liste_activites :
        if activite.inscriptions_affichage == 1 and (activite.inscriptions_date_debut == None or (activite.inscriptions_date_debut <= GetNow() and activite.inscriptions_date_fin >= GetNow())) :
            return True
    return False

def ConvertToUnicode(valeur=None):
    if valeur == None :
        return ""
    else :
        return valeur
    
def GetIndividu(IDindividu=None, liste_individus=[]):
    for individu in liste_individus :
        if individu.IDindividu == IDindividu :
            return individu
    return None
    
def IsRenseignementDisabled(dict_parametres=None, individu=None, categorie="", champ=""):
    if categorie == "nom" or champ in ("nom", "prenom") :
        return (individu.IDcategorie == 1 and GetParametre("RENSEIGNEMENTS_ADULTE_NOM", dict_parametres) == 'consultation') or (individu.IDcategorie == 2 and GetParametre("RENSEIGNEMENTS_ENFANT_NOM", dict_parametres) == 'consultation')
    if categorie == "naissance" or champ in ("date_naiss", "cp_naiss", "ville_naiss") :
        return (individu.IDcategorie == 1 and GetParametre("RENSEIGNEMENTS_ADULTE_NAISSANCE", dict_parametres) == 'consultation') or (individu.IDcategorie == 2 and GetParametre("RENSEIGNEMENTS_ENFANT_NAISSANCE", dict_parametres) == 'consultation')
    if categorie == "adresse" or champ in ("adresse_auto", "rue_resid", "cp_resid", "ville_resid") :
        return GetParametre("RENSEIGNEMENTS_ADRESSE", dict_parametres) == 'consultation'
    if categorie == "coords" or champ in ("tel_domicile", "tel_mobile", "mail") :
        return (individu.IDcategorie == 1 and GetParametre("RENSEIGNEMENTS_ADULTE_COORDS", dict_parametres) == 'consultation') or (individu.IDcategorie == 2 and GetParametre("RENSEIGNEMENTS_ENFANT_COORDS", dict_parametres) == 'consultation')
    if categorie == "profession" or champ in ("profession", "employeur", "travail_tel", "travail_mail") :
        return (individu.IDcategorie == 1 and GetParametre("RENSEIGNEMENTS_ADULTE_PROFESSION", dict_parametres) == 'consultation')
    return False

def DecrypteChaine(liste_chaines=[]):
    if isinstance(liste_chaines, six.text_type) or isinstance(liste_chaines, str) :
        type_donnee = "CHAINE"
        liste_chaines = [liste_chaines,]
    elif isinstance(liste_chaines, list) :
        type_donnee = "LISTE"
    else :
        return liste_chaines
    cryptage = AESCipher(app.config['SECRET_KEY'][10:20], bs=16, prefixe=u"#@#")
    liste_resultats = []
    for chaine in liste_chaines :
        resultat = cryptage.decrypt(chaine)
        liste_resultats.append(resultat)
    if type_donnee == "CHAINE" :
        return liste_resultats[0]
    return liste_resultats

def CrypteChaine(chaine=""):
    if chaine in ("", None):
        return chaine
    cryptage = AESCipher(app.config['SECRET_KEY'][10:20], bs=16, prefixe=u"#@#")
    resultat = cryptage.encrypt(chaine)
    return resultat

def TriElementsPourBlog(liste_elements=[]):
    """ Tri les éléments pour les pages perso de type blog """
    liste_temp = []
    for element in liste_elements :
        if element.date_debut <= datetime.datetime.now() and (element.date_fin == None or element.date_fin >= datetime.datetime.now()):
            liste_temp.append((element.date_debut, element))
    liste_temp.sort(reverse=True)
    return liste_temp

def FusionDonneesOrganisateur(texte="", dict_parametres={}):
    for key, valeur in dict_parametres.items():
        if key.startswith("ORGANISATEUR_") :
            if six.PY3:
                texte = texte.replace(b"{%s}" % key.encode('utf-8'), valeur.encode('utf-8'))
            else:
                texte = texte.replace(u"{%s}" % key, valeur)
    return texte

def Convert_liste_to_texte_virgules(liste=[]):
    """ Convertit un liste ['a', 'b', 'c'] en un texte 'a, b et c' """
    if len(liste) == 0:
        return ""
    elif len(liste) == 1:
        return liste[0]
    else:
        return ", ".join(liste[:-1]) + " et " + liste[-1]




def CallFonction(fonction="", *args):
    """ Pour appeller directement une fonction Utils depuis Python """
    return utility_processor()[fonction](*args)
    
@app.context_processor
def utility_processor():
    """ Variables accessibles dans tous les templates """        
        
    return dict(
        GetNow=GetNow,
        GetToday=GetToday,
        Formate_montant=Formate_montant,
        DateDDEnFr=DateDDEnFr,
        DateDDEnFrComplet=DateDDEnFrComplet,
        DateDTEnFr=DateDTEnFr,
        DateDTEnHeureFr=DateDTEnHeureFr,
        IsUniteOuverte=IsUniteOuverte,
        GetEvenementsOuverts=GetEvenementsOuverts,
        IsUniteModifiable=IsUniteModifiable,
        GetEtatFondCase=GetEtatFondCase,
        GetEtatCocheCase=GetEtatCocheCase,
        DateDDEnEng=DateDDEnEng,
        DateEngEnDD=DateEngEnDD,
        DateEngFr=DateEngFr,
        GetDictDatesAttente=GetDictDatesAttente,
        GetNbreDatesAttente=GetNbreDatesAttente,
        GetNumSemaine=GetNumSemaine,
        GetIconeFichier=GetIconeFichier,
        GetNbrePeriodesActives=GetNbrePeriodesActives,
        GetParametre=GetParametre,
        GetJoursOuverts=GetJoursOuverts,
        EstFerie=EstFerie,
        HasActivitesDisponiblesPourInscriptions=HasActivitesDisponiblesPourInscriptions,
        ConvertToUnicode=ConvertToUnicode,
        GetIndividu=GetIndividu,
        IsRenseignementDisabled=IsRenseignementDisabled,
        DecrypteChaine=DecrypteChaine,
        CrypteChaine=CrypteChaine,
        TriElementsPourBlog=TriElementsPourBlog,
        FusionDonneesOrganisateur=FusionDonneesOrganisateur,
        Convert_liste_to_texte_virgules=Convert_liste_to_texte_virgules,
        )
