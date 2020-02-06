#!/usr/bin/env python
# -*- coding: utf-8 -*-
#--------------------------------------------------------------
# Application :    Connecthys, le portail internet de Noethys
# Site internet :  www.noethys.com
# Auteur:          Ivan LUCAS
# Copyright:       (c) 2010-16 Ivan LUCAS
# Licence:         Licence GNU GPL
#--------------------------------------------------------------

u"""

USAGE :

'python run.py -s <serveur> -h <host> -p <port>'

Vous pouvez lancer simplement 'python run.py' pour démarrer le serveur
web intégré à Connecthys.

-- Choix du serveur --

Attention, ce serveur n'est pas très puissant et ne convient pas
forcément à un usage en production. Vous pouvez également utiliser
un des autres serveurs supportés :

Tornado peut permettre à Connecthys de supporter plusieurs milliers
de connexions simultanées. Tapez "pip install tornado" pour l'installer.
Puis il suffit de taper 'python run.py -s tornado' pour lancer Connecthys
en utilisant tornado.

Gevent est également une alternative. Tapez "pip install gevent" pour
l'installer. Puis tapez 'python run.py -s gevent' pour lancer Connecthys
en utilisant gevent.

-- Choix de l'hôte --

host='0.0.0.0': écoute sur toutes les interfaces réseaux de la machine (y compris loopback)
host='192.168.0.1': écoute sur l'interface ayant l'IP 192.168.0.1 uniquement
host='127.0.0.1': écoute uniquement sur l'interface loopback
host non défini: écoute uniquement sur l'interface loopback

-- Choix du port --

Par défaut 5000

"""


import sys, getopt
import imports

# Vérification des arguments
try:
    opts, args = getopt.getopt(sys.argv[1:], "s:h:p:", ["serveur=", "host=", "port="])
except getopt.GetoptError:
    print("run.py -s <serveur> -h <host> -p <port>")
    print("serveur = None | tornado | gevent")
    print("host = 127.0.0.1")
    print("port = 5000")
    sys.exit(2)

# Serveur = None (serveur intégré à Flask) | tornado | gevent
serveur = None

# Le port peut être modifié librement
port = 5000

# Choix de l'hôte
host = "0.0.0.0"

# Lecture des arguments
for opt, arg in opts:
    if opt in ("-s", "--serveur"):
        serveur = arg
    if opt in ("-h", "--host"):
        host = arg
    if opt in ("-p", "--port"):
        port = int(arg)    

print("Lancement de Connecthys...")
print("serveur=%s host=%s port=%s" % (serveur, host, port))

# Ajoute au path le chemin des librairies
imports.AjouteCheminLibs()

# Activation du SSL/TLS
#import ssl
#context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
#context.load_cert_chain('path/mon_certificat.crt', 'path/mon_certificat.key')

# Chargement de l'application
from application import app

# Lancement du serveur
if "tornado" in sys.argv :

    # Serveur Tornado
    # Installation préalable : "pip install tornado"
    
    from tornado.wsgi import WSGIContainer
    from tornado.httpserver import HTTPServer
    from tornado.ioloop import IOLoop

    http_server = HTTPServer(WSGIContainer(app))
    http_server.listen(port)
    IOLoop.instance().start()

elif "gevent" in sys.argv :
    
    # Serveur Gevent
    # Installation préalable : "pip install gevent"

    from gevent.wsgi import WSGIServer

    http_server = WSGIServer(('', port), app)
    http_server.serve_forever()

else :
    
    # Serveur intégré à Flask
    
    app.run(host=host, port=port, debug=False)
