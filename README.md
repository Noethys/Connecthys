Connecthys
==================
Connecthys est le portail internet de Noethys, le logiciel de gestion libre et gratuit de gestion multi-activit�s pour 
les accueils de loisirs, cr�ches, garderies p�riscolaires, cantines, TAP ou NAP, clubs sportifs et culturels...

Plus d'infos sur www.noethys.com


Installation depuis Noethys (sur Windows ou Linux)
------------------------

- Installez python et pycrypto si besoin (voir ci-dessous)
- Depuis Noethys allez dans le menu **Outils > Connecthys**
- Renseignez les champs demand�s puis cliquez sur **Installer**.


Installation sur Windows
------------------------

- Installez python 2.7 (http://www.python.org)
- Installez pycrypto (http://www.voidspace.org.uk/downloads/pycrypto26/pycrypto-2.6.win32-py2.7.exe)
- Placez-vous dans le r�pertoire connecthys 
- Chargez l'invite de commandes de Windows et tapez "C:\Python27\python.exe run.py"
- Lancez votre navigateur internet
- Chargez la page **http://localhost:5000/** pour ouvrir le portail


Installation sur Linux
-------------------------

- Installez pycrypto : "sudo pip install pycrypto"
- Placez-vous dans le r�pertoire connecthys 
- Chargez la console de Linux et tapez "python run.py"
- Lancez votre navigateur internet
- Chargez la page **http://localhost:5000/** pour ouvrir le portail


Installation sur un h�bergement internet mutualis� (Test� sur OVH)
-------------------------

- Copiez le r�pertoire "connecthys" � la racine de votre r�pertoire FTP
- Avec votre client FTP (Filezilla par exemple), appliquez la valeur 755 aux droits d'acc�s du fichier "portail.cgi" du r�pertoire connecthys
- Chargez la page **http://www.monsite.com/connecthys/portail.cgi/** pour ouvrir le portail


Installation sur un h�bergement internet d�di� ou sur Google App Engine
-------------------------

Connecthys peut �tre install� de plusieurs fa�ons sur un h�bergement internet. 
Consultez la page http://flask.pocoo.org/docs/0.11/deploying/ pour d�couvrir ces possibilit�s.