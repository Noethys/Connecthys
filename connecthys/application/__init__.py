#!/usr/bin/env python
# -*- coding: utf-8 -*-
#--------------------------------------------------------------
# Application :    Connecthys, le portail internet de Noethys
# Site internet :  www.noethys.com
# Auteur:          Ivan LUCAS
# Copyright:       (c) 2010-16 Ivan LUCAS
# Licence:         Licence GNU GPL
#--------------------------------------------------------------

import logging
from logging.handlers import RotatingFileHandler
from flask import Flask
from flask_adminlte import AdminLTE

# Récupération du numéro de version de l'application
import versions
__version__ = versions.GetVersion()

# Init application
app = Flask(__name__)

# Configuration de flask
from data.config import Config_application, Config_utilisateur
app.config.from_object(Config_application)
app.config.from_object(Config_utilisateur)
app.config["VERSION_APPLICATION"] = __version__

# Connexion avec le journal d'évènements
handler = RotatingFileHandler('journal.log', maxBytes=10000, backupCount=1)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('[%(asctime)s][%(levelname)s][%(filename)s:%(lineno)d] %(message)s')
handler.setFormatter(formatter)
app.logger.addHandler(handler)
    
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

# Connexion avec flask_migrate
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
migrate = Migrate(app, db)
manager = Manager(app)
manager.add_command('db', MigrateCommand)

# Connexion avec AdminLTE
AdminLTE(app)

# Flask-WTF csrf protection
from flask_wtf.csrf import CsrfProtect 
csrf = CsrfProtect()  
csrf.init_app(app)

# Import des views et des models
from application import views, models, utils

# Recherche la version de la base de données
versionDB = models.GetVersionDB()

# Création de la base de données si nécessaire
if versionDB == None :
    models.CreationDB()

# Vérifie que la DB est à jour
if versionDB != None :
    if utils.GetVersionTuple(__version__) > utils.GetVersionTuple(versionDB) :
        models.UpgradeDB()

