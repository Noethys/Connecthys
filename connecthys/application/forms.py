#!/usr/bin/env python
# -*- coding: utf-8 -*-
#--------------------------------------------------------------
# Application :    Connecthys, le portail internet de Noethys
# Site internet :  www.noethys.com
# Auteur:          Ivan LUCAS
# Copyright:       (c) 2010-16 Ivan LUCAS
# Licence:         Licence GNU GPL
#--------------------------------------------------------------

try:
    from flask_wtf import FlaskForm
    # from flask_wtf import RecaptchaField
except:
    # Pour la compatibilit� avec les anciennes version de flask_wtf
    from flask_wtf import Form as FlaskForm

from application import app
from wtforms import BooleanField, HiddenField, PasswordField, validators, SelectField, StringField, FileField, TextAreaField
from flask_wtf.file import FileRequired

try:
    from wtforms import TextField
except:
    from wtforms import StringField as TextField


class LoginFormWithCaptcha(FlaskForm):
    identifiant = TextField('identifiant', [validators.DataRequired(), validators.Length(min=0, max=20)])
    password = PasswordField('password',  [validators.DataRequired(), validators.Length(min=0, max=20)])
    remember = BooleanField("remember", default=False)
    # recaptcha = RecaptchaField()
    captcha = StringField("captcha", validators=[validators.DataRequired()])

class LoginForm(FlaskForm):
    identifiant = TextField('identifiant', [validators.DataRequired(), validators.Length(min=0, max=20)])
    password = PasswordField('password',  [validators.DataRequired(), validators.Length(min=0, max=20)])
    remember = BooleanField("remember", default=False)

class ChangePassword(FlaskForm):
    password1 = PasswordField('password1',  [validators.DataRequired(), validators.Length(min=0, max=20)])
    password2 = PasswordField('password2',  [validators.DataRequired(), validators.Length(min=0, max=20)])
    accept = BooleanField("accept", default=False)

class ResetPassword(FlaskForm):
    identifiant = TextField('identifiant', [validators.DataRequired(), validators.Length(min=1, max=20)])
    password1 = PasswordField('password1',  [validators.DataRequired(), validators.Length(min=0, max=20)])
    password2 = PasswordField('password2',  [validators.DataRequired(), validators.Length(min=0, max=20)])
    accept = BooleanField("accept", default=False)

class LostPasswordWithCaptcha(FlaskForm):
    identifiant = TextField('identifiant', [validators.DataRequired(), validators.Length(min=1, max=20)])
    email = TextField('email',  [validators.DataRequired(), validators.Length(min=3, max=50)])
    # recaptcha = RecaptchaField()
    captcha = StringField("captcha", validators=[validators.DataRequired()])

class LostPassword(FlaskForm):
    identifiant = TextField('identifiant', [validators.DataRequired(), validators.Length(min=1, max=20)])
    email = TextField('email',  [validators.DataRequired(), validators.Length(min=3, max=50)])

class RetourTipi(FlaskForm):
    NUMCLI = TextField('numcli', [validators.DataRequired(), validators.Length(min=0, max=20)])
    EXER = TextField('exer', [validators.DataRequired(), validators.Length(min=0, max=4)])
    REFDET = TextField('refdet', [validators.DataRequired(), validators.Length(min=0, max=30)])
    OBJET = TextField('objet', [validators.DataRequired(), validators.Length(min=0, max=30)])
    MONTANT = TextField('montant', [validators.DataRequired(), validators.Length(min=0, max=20)])
    MEL = TextField('mel', [validators.DataRequired(), validators.Length(min=0, max=30)])
    SAISIE = TextField('saisie', [validators.DataRequired(), validators.Length(min=0, max=5)])
    RESULTRANS = TextField('resultrans', [validators.DataRequired(), validators.Length(min=0, max=50)])
    NUMAUTO = TextField('numauto', [validators.DataRequired(), validators.Length(min=0, max=20)])
    DATTRANS = TextField('dattrans', [validators.DataRequired(), validators.Length(min=0, max=20)])
    HEURTRANS = TextField('heurtrans', [validators.DataRequired(), validators.Length(min=0, max=20)])
    
class Renseignements(FlaskForm):
    idindividu = HiddenField("idindividu")
    nom = TextField('nom')
    prenom = TextField('prenom')
    date_naiss = TextField('date_naiss')
    cp_naiss = TextField('cp_naiss')
    ville_naiss = TextField('ville_naiss')
    rue_resid = TextField('rue_resid')
    cp_resid = TextField('cp_resid')
    ville_resid = TextField('ville_resid')
    tel_domicile = TextField('tel_domicile')
    tel_mobile = TextField('tel_mobile')
    mail = TextField('mail')
    profession = TextField('profession')
    employeur = TextField('employeur')
    travail_tel = TextField('travail_tel')
    travail_mail = TextField('travail_mail')
    adresse_auto = SelectField('adresse_auto', coerce=int)

class Piece(FlaskForm):
    piece = FileField('piece', validators=[FileRequired(),])
    titre_piece = TextField('titre_piece')
    commentaire = TextAreaField('commentaire')

class Location(FlaskForm):
    description = TextField('description')
