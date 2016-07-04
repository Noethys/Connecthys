#!/usr/bin/env python
# -*- coding: utf-8 -*-
#--------------------------------------------------------------
# Application :    Connecthys, le portail internet de Noethys
# Site internet :  www.noethys.com
# Auteur:          Ivan LUCAS
# Copyright:       (c) 2010-16 Ivan LUCAS
# Licence:         Licence GNU GPL
#--------------------------------------------------------------


from flask import Flask
from flask_adminlte import AdminLTE


# Init application
app = Flask(__name__)

# Configuration de flask
from config import Config_application, Config_utilisateur
app.config.from_object(Config_application)
app.config.from_object(Config_utilisateur)

# Debugtoolbar
if Config_application.DEBUG == True :
    app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
    app.config['DEBUG_TB_PROFILER_ENABLED'] = True
    from flask_debugtoolbar import DebugToolbarExtension
    toolbar = DebugToolbarExtension(app)

# Connexion avec flask_login
from flask_login import LoginManager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Connexion avec SqlAlchemy
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy(app)

# Connexion avec AdminLTE
AdminLTE(app)

# Flask-WTF csrf protection
from flask_wtf.csrf import CsrfProtect 
csrf = CsrfProtect()  
csrf.init_app(app)

# Import des views et des models
from application import views, models

