#!/usr/bin/env python
# -*- coding: utf-8 -*-
#--------------------------------------------------------------
# Application :    Connecthys, le portail internet de Noethys
# Site internet :  www.noethys.com
# Auteur:          Ivan LUCAS
# Copyright:       (c) 2010-16 Ivan LUCAS
# Licence:         Licence GNU GPL
#--------------------------------------------------------------

from flask import Flask, render_template
from application import app

import os.path
REP_APPLICATION = os.path.abspath(os.path.dirname(__file__))
REP_CONNECTHYS = os.path.dirname(REP_APPLICATION)


@app.route('/')
def index():
    fichier = open(os.path.join(REP_CONNECTHYS, "redirection_noethysweb.txt"), "r")
    url = fichier.readlines()[0]
    fichier.close()
    return render_template("redirection_noethysweb.html", url=url)
