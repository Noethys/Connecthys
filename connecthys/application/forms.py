#!/usr/bin/env python
# -*- coding: utf-8 -*-
#--------------------------------------------------------------
# Application :    Connecthys, le portail internet de Noethys
# Site internet :  www.noethys.com
# Auteur:          Ivan LUCAS
# Copyright:       (c) 2010-16 Ivan LUCAS
# Licence:         Licence GNU GPL
#--------------------------------------------------------------

try :
    from flask_wtf import FlaskForm
except :
    # Pour la compatibilité avec les anciennes version de flask_wtf
    from flask_wtf import Form as FlaskForm

from wtforms import BooleanField, TextField, HiddenField, PasswordField, DateTimeField, validators, IntegerField, SubmitField


class LoginForm(FlaskForm):  
    identifiant = TextField('identifiant', [validators.Required(), validators.Length(min=0, max=20)])
    password  = PasswordField('password',  [validators.Required(), validators.Length(min=0, max=10)])
    remember = BooleanField("remember", default=False)

class RetourTipi(FlaskForm):
    NUMCLI = TextField('numcli', [validators.Required(), validators.Length(min=0, max=20)])
    EXER = TextField('exer', [validators.Required(), validators.Length(min=0, max=4)])
    REFDET = TextField('refdet', [validators.Required(), validators.Length(min=0, max=30)])
    OBJET = TextField('objet', [validators.Required(), validators.Length(min=0, max=30)])
    MONTANT = TextField('montant', [validators.Required(), validators.Length(min=0, max=20)])
    MEL = TextField('mel', [validators.Required(), validators.Length(min=0, max=30)])
    SAISIE = TextField('saisie', [validators.Required(), validators.Length(min=0, max=5)])
    RESULTRANS = TextField('resultrans', [validators.Required(), validators.Length(min=0, max=50)])
    NUMAUTO = TextField('numauto', [validators.Required(), validators.Length(min=0, max=20)])
    DATTRANS = TextField('dattrans', [validators.Required(), validators.Length(min=0, max=20)])
    HEURTRANS = TextField('heurtrans', [validators.Required(), validators.Length(min=0, max=20)])
