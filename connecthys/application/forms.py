#!/usr/bin/env python
# -*- coding: utf-8 -*-
#--------------------------------------------------------------
# Application :    Connecthys, le portail internet de Noethys
# Site internet :  www.noethys.com
# Auteur:          Ivan LUCAS
# Copyright:       (c) 2010-16 Ivan LUCAS
# Licence:         Licence GNU GPL
#--------------------------------------------------------------

from flask_wtf import Form  
from wtforms import BooleanField, TextField, HiddenField, PasswordField, DateTimeField, validators, IntegerField, SubmitField


class LoginForm(Form):  
   identifiant = TextField('identifiant', [validators.Required(), validators.Length(min=0, max=20)])
   password  = PasswordField('password',  [validators.Required(), validators.Length(min=0, max=10)])
   remember = BooleanField("remember", default=False)