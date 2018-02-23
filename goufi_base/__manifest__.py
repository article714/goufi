# -*- coding: utf-8 -*-
# ©2017 - C. Guychard
# License: AGPL v3

{
    'name': u'Goufi: Generic, user-friendly, data import application',
    'version': u'10.0.1.0.0',
    'category': u'Applications',
    'author': u'Openflexo',
    'license': u'LGPL-3',
    'website': u'https://www.article714.org',
    'description': u"""
Goufi: Base module
======================

TODO


**Credits:** .
""",
    'depends': [ 'mail' ],
    'data': ['security/access_model.xml',
            'views/goufi_import_actions.xml',
            'views/goufi_import_menus.xml',
            'views/import_file_views.xml', ],
    'installable': True,
    'images': [],
    'application': True,
}
