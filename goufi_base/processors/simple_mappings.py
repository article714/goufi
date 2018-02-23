# -*- coding: utf-8 -*-
'''
Created on 23 deb. 2018

@author: C. Guychard
@copyright: ©2018 Article 714
@license: AGPL v3
'''

import logging

from odoo.addons.goufi_base.utils.converters  import toString

#-------------------------------------------------------------------------------------
# CONSTANTS
AUTHORIZED_EXTS = ('xlsx', 'xls', 'csv')

#-------------------------------------------------------------------------------------
# MAIN CLASS


class Processor():

    def __init__(self, parent_config):
        self.parent_config = parent_config

    #-------------------------------------------------------------------------------------
    def is_data_file(self, filename):
        ext = filename.split('.')[-1]
        return (ext in AUTHORIZED_EXTS)

    #-------------------------------------------------------------------------------------
    def process_file(self, import_file):
        logging.warning("Goufi Simple Mappings Import: " + toString(import_file.filename))

