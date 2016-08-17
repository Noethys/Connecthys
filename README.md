Connecthys
==================
Connecthys est le portail internet de Noethys, le logiciel de gestion libre et gratuit de gestion multi-activités pour 
les accueils de loisirs, crèches, garderies périscolaires, cantines, TAP ou NAP, clubs sportifs et culturels...

Plus d'infos sur www.noethys.com


Installation depuis Noethys (sur Windows ou Linux)
------------------------

- Depuis Noethys allez dans le menu **Outils > Connecthys**
- Renseignez les champs demandés puis cliquez sur **Installer**.


Installation sur Windows
------------------------

- Installez python 2.7 (http://www.python.org)
- Placez-vous dans le répertoire connecthys 
- Chargez l'invite de commandes de Windows et tapez "C:\Python27\python.exe run.py"
- Lancez votre navigateur internet
- Chargez la page **http://localhost:5000/** pour ouvrir le portail


Installation sur Linux
-------------------------

- Placez-vous dans le répertoire connecthys 
- Chargez la console de Linux et tapez "python run.py"
- Lancez votre navigateur internet
- Chargez la page **http://localhost:5000/** pour ouvrir le portail


Installation sur un hébergement internet mutualisé (Testé sur OVH)
-------------------------

- Copiez le répertoire "connecthys" à la racine de votre répertoire FTP
- Avec votre client FTP (Filezilla par exemple), appliquez la valeur 755 aux droits d'accès du fichier "portail.cgi" du répertoire connecthys
- Chargez la page **http://www.monsite.com/connecthys/portail.cgi/** pour ouvrir le portail


Installation sur un hébergement internet dédié ou sur Google App Engine
-------------------------

Connecthys peut être installé de plusieurs façons sur un hébergement internet. 
Consultez la page http://flask.pocoo.org/docs/0.11/deploying/ pour découvrir ces possibilités.