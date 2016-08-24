#!/usr/bin/env python
# -*- coding: utf-8 -*-
#--------------------------------------------------------------
# Application :    Connecthys, le portail internet de Noethys
# Site internet :  www.noethys.com
# Auteur:          Ivan LUCAS
# Copyright:       (c) 2010-16 Ivan LUCAS
# Licence:         Licence GNU GPL
#--------------------------------------------------------------

# Exclusions possibles : ["application", "flask_adminlte", "lib"]

VERSIONS = [
    {"version" : "0.0.1",  "exclusions" : []},
    {"version" : "0.0.2",  "exclusions" : ["flask_adminlte", "lib"]},
    {"version" : "0.0.4",  "exclusions" : ["flask_adminlte", "lib"]},
    {"version" : "0.0.5",  "exclusions" : ["flask_adminlte", "lib"]},
    ]

    
def GetVersion():
    """ Retourne le num�ro de version actuel """
    return VERSIONS[-1]["version"]
