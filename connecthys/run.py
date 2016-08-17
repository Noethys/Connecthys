#!/usr/bin/env python
# -*- coding: utf-8 -*-
#--------------------------------------------------------------
# Application :    Connecthys, le portail internet de Noethys
# Site internet :  www.noethys.com
# Auteur:          Ivan LUCAS
# Copyright:       (c) 2010-16 Ivan LUCAS
# Licence:         Licence GNU GPL
#--------------------------------------------------------------

import imports

# Ajoute au path le chemin des librairies
imports.AjouteCheminLibs()

# Activation du SSL/TLS
#import ssl
#context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
#context.load_cert_chain('path/mon_certificat.crt', 'path/mon_certificat.key')


from application import app
# host='0.0.0.0': écoute sur toutes les interfaces réseaux de la machine (y compris loopback)
# host='192.168.0.1': écoute sur l'interface ayant l'IP 192.168.0.1 uniquement
# host='127.0.0.1': écoute uniquement sur l'interface loopback
# host non défini: écoute uniquement sur l'interface loopback
app.run(host='0.0.0.0', port=5000, debug=True)
