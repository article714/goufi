# -*- coding: utf-8 -*-
# @author: C. Guychard
# @copyright: ©2018 Article 714
# @license: AGPL v3

{
    'name': u'Goufi: Generic, user-friendly, data import application',
    'version': u'11.0.6.0.0',
    'category': u'Applications',
    'author': u'Article714',
    'license': u'AGPL-3',
    'website': u'https://www.article714.org',
    'description': u"""
Goufi: Base module, importing data files 
=========================================

TODO


**Credits:** .
""",
    'depends': ['mail'],
    'data': ['security/goufi_security.xml',
             'security/access_model.xml',
             'data/import_processors.xml',
             'views/import_file_default_filters.xml',
             'actions/goufi_base_actions.xml',
             'actions/goufi_automation.xml',
             'views/goufi_config_view.xml',
             'views/goufi_import_menus.xml',
             'views/import_file_views.xml',
             'views/import_processor_views.xml',
             'views/processor_parameters_views.xml',
             'views/import_column_mapping_views.xml',
             'views/import_tab_mapping_views.xml',
             'views/import_configuration_views.xml', ],
    'installable': True,
    'images': [],
    'application': True,
}
