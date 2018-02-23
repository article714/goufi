# -*- coding: utf-8 -*-
# ©2016 Openflexo
# License: TBD


{
    'name': u'Certificare Data import Application',
    'version': u'10.0.1.0.0',
    'category': u'Applications',
    'author': u'Openflexo',
    'license': u'LGPL-3',
    'website': u'https://www.certificare.fr',
    'description': u"""
Certificare
======================

Un module importer les données de l'application certificare

Nécessite l'installation de nouvelles bibliothèques Python:


**Credits:** Certificare.
""",
    'depends': ['certificare_app', 'mail' ],
    'data': ['security/access_model.xml',
            'views/certificare_import_actions.xml',
            'views/certificare_import_menus.xml',
            'views/import_file_views.xml', ],
    'installable': True,
    'images': [],
    'application': True,
}
