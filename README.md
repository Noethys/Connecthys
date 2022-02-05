Connecthys
==================
Connecthys est le portail internet de Noethys, le logiciel de gestion libre et gratuit de gestion multi-activités pour 
les accueils de loisirs, crèches, garderies périscolaires, cantines, TAP ou NAP, clubs sportifs et culturels...

Plus d'infos sur www.noethys.com


Installation
------------------------

- Installez python (http://www.python.org)
- Téléchargez le code source.
- Ouvrez le répertoire dans lequel se trouve le fichier *requirements.txt*.
- Installez les dépendances :
    - `pip3 install -r requirements.txt`
- Ouvrez un terminal et tapez :
    - `python3 connecthys/run.py`
- Lancez votre navigateur internet
- Chargez la page **http://localhost:5000/** pour ouvrir le portail


Installation sur un hébergement internet mutualisé (Testé sur OVH)
-------------------------
- Installez : apt-get install python-pip python-mysqldb libapache2-python (sous debian)
- Activez le mod_cgi et mod_python (a2enmod python && a2enmod cgi && systemctl restart apache2)
- Copiez le répertoire "connecthys" à la racine de votre répertoire FTP
- Avec votre client FTP (Filezilla par exemple), appliquez la valeur 755 aux droits d'accès du fichier "connecthys.cgi" du répertoire connecthys (chmod 755 && chown -R www-data:www-data)
- Chargez la page **http://www.monsite.com/connecthys/connecthys.cgi/** pour ouvrir le portail


Installation sur un hébergement internet dédié ou sur Google App Engine
-------------------------

Connecthys peut être installé de plusieurs façons sur un hébergement internet. 
Consultez la page http://flask.pocoo.org/docs/1.0/deploying/ pour découvrir ces possibilités.
