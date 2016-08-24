#!/usr/bin/env python
# -*- coding: utf-8 -*-
#--------------------------------------------------------------
# Application :    Connecthys, le portail internet de Noethys
# Site internet :  www.noethys.com
# Auteur:          Ivan LUCAS
# Copyright:       (c) 2010-16 Ivan LUCAS
# Licence:         Licence GNU GPL
#--------------------------------------------------------------

import sys, os

LISTE_LIBS = [
	"", "application", "lib/", "lib/flask", "lib/flask_sqlalchemy", 
	"lib/flask_wtf", "lib/itsdangerous", "lib/markupsafe", "lib/sqlalchemy", 
	"lib/werkzeug", "lib/jinja2", "lib/wtforms", "lib/flask_debugtoolbar",
	"lib/pkg_resources", "lib/blinker", "lib/click", "lib/alembic",
    "lib/flask_script", "lib/mako", "lib/flask_migrate", "lib/flask_compress",
	]
    
def AjouteCheminLibs(chemin=os.path.dirname(__name__)) :
    for lib in LISTE_LIBS :
        sys.path.append(os.path.join(chemin, lib))
