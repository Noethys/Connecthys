#!/usr/bin/env python
# -*- coding: utf-8 -*-
#--------------------------------------------------------------
# Application :    Connecthys, le portail internet de Noethys
# Site internet :  www.noethys.com
# Auteur:          Ivan LUCAS
# Copyright:       (c) 2010-20 Ivan LUCAS
# Licence:         Licence GNU GPL
#--------------------------------------------------------------

from flask_session_captcha import FlaskSessionCaptcha
import base64
import logging
from flask import session


class MyFlaskSessionCaptcha(FlaskSessionCaptcha):
    def __init__(self, *args, **kwargs):
        FlaskSessionCaptcha.__init__(self, *args, **kwargs)

    def generate(self):
        """ Remplace les 1 et les 7 par d'autres valeurs par souci de lisibilité """
        answer = self.rand.randrange(self.max)
        answer = str(answer).zfill(self.digits)
        answer = answer.replace("1", "2")
        answer = answer.replace("7", "8")
        image_data = self.image_generator.generate(answer)
        base64_captcha = base64.b64encode(image_data.getvalue()).decode("ascii")
        logging.debug('Generated captcha with answer: ' + answer)
        session['captcha_answer'] = answer
        return base64_captcha