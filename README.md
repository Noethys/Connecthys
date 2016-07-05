Connecthys
==================
Connecthys est le portail internet de Noethys, le logiciel de gestion libre et gratuit de gestion multi-activités pour 
les accueils de loisirs, crèches, garderies périscolaires, cantines, 
TAP ou NAP, clubs sportifs et culturels...

Plus d'infos sur www.noethys.com

*****Avertissement : A ce jour, Connecthys n'est qu'un prototype d'interface web. La synchronisation avec Noethys sera développée
prochainement.*****


Utilisation sur Windows
------------------------

- Installez python 2.7 (http://www.python.org)
- Placez-vous dans le répertoire connecthys 
- Chargez l'invite de commandes de Windows et tapez "C:\Python27\python.exe run.py"
- Lancez votre navigateur internet
- Chargez la page **http://localhost:5000/initdb** pour initialiser la base de données
- Chargez la page **http://localhost:5000/accueil** pour ouvrir le portail


Utilisation sur Linux
-------------------------

- Placez-vous dans le répertoire connecthys 
- Chargez la console de Linux et tapez "python run.py"
- Lancez votre navigateur internet
- Chargez la page **http://localhost:5000/initdb** pour initialiser la base de données
- Chargez la page **http://localhost:5000/accueil** pour ouvrir le portail


Utilisation sur un hébergement internet mutualisé (Testé sur OVH)
-------------------------

- Copiez le répertoire "connecthys" à la racine de votre répertoire FTP
- Avec votre client FTP (Filezilla par exemple), appliquez la valeur 755 aux droits d'accès du fichier "portail.cgi" du répertoire connecthys
- Chargez la page **http://www.monsite.com/connecthys/portail.cgi/initdb** pour initialiser la base de données
- Chargez la page **http://www.monsite.com/connecthys/portail.cgi/accueil** pour ouvrir le portail
