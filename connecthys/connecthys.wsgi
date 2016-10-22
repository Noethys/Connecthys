#!/usr/bin/env python
# -*- coding: utf-8 -*-
#--------------------------------------------------------------
# Application :    Connecthys, le portail internet de Noethys
# Site internet :  www.noethys.com
# Auteur:          Ivan LUCAS
# Copyright:       (c) 2010-16 Ivan LUCAS
# Licence:         Licence GNU GPL
#--------------------------------------------------------------

import os, sys
REP_CONNECTHYS = os.path.abspath(os.path.dirname(__file__))
if not REP_CONNECTHYS in sys.path:
	sys.path.insert(0, REP_CONNECTHYS)

# Initialisation du log
import logging, sys
logging.basicConfig(stream=sys.stderr)

# Initialisation de l'application
from application import app as application