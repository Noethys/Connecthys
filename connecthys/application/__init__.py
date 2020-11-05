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

import os.path
REP_APPLICATION = os.path.abspath(os.path.dirname(__file__))
REP_CONNECTHYS = os.path.dirname(REP_APPLICATION)


# Récupération du numéro de version de l'application
import updater
__version__ = updater.GetVersionActuelle()

# Init application
app = Flask(__name__)

# Configuration de flask
try :
    from data.config import Config_application
    app.config.from_object(Config_application)
    app.config["VERSION_APPLICATION"] = __version__
    config_ok = True
except :
    config_ok = False
    
# Flask compress
# from flask_compress import Compress
# compress = Compress()
# compress.init_app(app)

# Connexion avec le journal d'évènements
handler = RotatingFileHandler(os.path.join(REP_CONNECTHYS, "journal.log"), maxBytes=100000, backupCount=10)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('[%(asctime)s][%(levelname)s][%(filename)s:%(lineno)d] %(message)s')
handler.setFormatter(formatter)
app.logger.addHandler(handler)

# Connexion avec le journal de debug
handlerdebug = RotatingFileHandler(os.path.join(REP_CONNECTHYS, "debug.log"), maxBytes=204800, backupCount=30)
handlerdebug.setLevel(logging.DEBUG)
formatterdebug = logging.Formatter('[%(asctime)s][%(levelname)s][%(filename)s:%(lineno)d] %(message)s')
handlerdebug.setFormatter(formatterdebug)
app.logger.addHandler(handlerdebug)

app.logger.setLevel(logging.DEBUG)

if config_ok == True :

    # Debugtoolbar
    if Config_application.DEBUG == True :
        app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
        app.config['DEBUG_TB_PROFILER_ENABLED'] = True
        app.config['DEBUG_TB_PANELS'] = (
            'flask_debugtoolbar.panels.versions.VersionDebugPanel',
            # 'flask_debugtoolbar.panels.timer.TimerDebugPanel', # Désactivé car cause un bug
            'flask_debugtoolbar.panels.headers.HeaderDebugPanel',
            'flask_debugtoolbar.panels.request_vars.RequestVarsDebugPanel',
            'flask_debugtoolbar.panels.config_vars.ConfigVarsDebugPanel',
            'flask_debugtoolbar.panels.template.TemplateDebugPanel',
            'flask_debugtoolbar.panels.sqlalchemy.SQLAlchemyDebugPanel',
            'flask_debugtoolbar.panels.logger.LoggingPanel',
            'flask_debugtoolbar.panels.route_list.RouteListDebugPanel',
            'flask_debugtoolbar.panels.profiler.ProfilerDebugPanel',
            'flask_debugtoolbar.panels.g.GDebugPanel',
        )
        from flask_debugtoolbar import DebugToolbarExtension
        toolbar = DebugToolbarExtension(app)

    # Flask Talisman
    if not Config_application.DEBUG and hasattr(Config_application, "TALISMAN") and Config_application.TALISMAN:
        from flask_talisman import Talisman
        Talisman(app, force_https=False, content_security_policy=None)

    # Recaptcha
    # try:
    #     from data.config_extra import Config_extra
    #     app.config.from_object(Config_extra)
    # except:
    #     app.config['RECAPTCHA_ACTIVATION'] = False

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
    if db.engine.url.drivername == 'sqlite':
        migrate = Migrate(app, db, compare_type=True, render_as_batch=True)
    else:
        migrate = Migrate(app, db, compare_type=True)
    manager = Manager(app)
    manager.add_command('db', MigrateCommand)

    # Captcha
    if app.config.get('CAPTCHA', 1) == 1:
        from flask_sessionstore import Session, SqlAlchemySessionInterface
        # from flask_session_captcha import FlaskSessionCaptcha
        from captchas import MyFlaskSessionCaptcha as FlaskSessionCaptcha
        app.config['SESSION_TYPE'] = 'sqlalchemy'
        session = Session(app)
        SqlAlchemySessionInterface(app, db, "sessions", "sess_")
        # session.app.session_interface.db.create_all()
        app.config['CAPTCHA_ENABLE'] = True
        app.config['CAPTCHA_LENGTH'] = 5
        app.config['CAPTCHA_WIDTH'] = 320
        app.config['CAPTCHA_HEIGHT'] = 50
        captcha = FlaskSessionCaptcha(app)
    else:
        captcha = None

    # Connexion avec Flask_mail
    try :
        from flask_mail import Mail
        mail = Mail(app)
    except:
        mail = None
        app.logger.error("Impossible d'importer flask_mail")

    # Connexion avec AdminLTE
    AdminLTE(app)

    # Flask-WTF csrf protection
    try :
        from flask_wtf.csrf import CSRFProtect
    except :
        # Pour compatibilité avec anciennes versions de flask_wtf
        from flask_wtf.csrf import CsrfProtect as CSRFProtect
    csrf = CSRFProtect()  
    csrf.init_app(app)

    # Import des views et des models
    import models, views, utils

    # Recherche la version de la base de données
    versionDB = models.GetVersionDB()

    # Création de la base de données si nécessaire
    if versionDB == None :
        models.CreationDB()

    # Vérifie que la DB est à jour
    if versionDB != None :
        if updater.GetVersionTuple(__version__) > updater.GetVersionTuple(versionDB) :
            models.UpgradeDB()

# Si configuration absente     
if config_ok == False :
    AdminLTE(app)
    import noconfig
    
