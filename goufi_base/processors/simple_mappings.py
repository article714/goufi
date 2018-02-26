# -*- coding: utf-8 -*-
'''
Created on 23 deb. 2018

@author: C. Guychard
@copyright: ©2018 Article 714
@license: AGPL v3
'''

import logging

from odoo.addons.goufi_base.utils.converters  import toString
from .processor import AbstractProcessor

#-------------------------------------------------------------------------------------
# CONSTANTS
AUTHORIZED_EXTS = ('xlsx', 'xls', 'csv')

#-------------------------------------------------------------------------------------
# MAIN CLASS


class Processor(AbstractProcessor):

    #-------------------------------------------------------------------------------------
    def is_data_file(self, filename):
        ext = filename.split('.')[-1]
        return (ext in AUTHORIZED_EXTS)

    #-------------------------------------------------------------------------------------
    def process_file(self, import_file):
        if import_file and self.is_data_file(import_file.filename):
            logging.warning("Goufi Simple Mappings Import: " + toString(import_file.filename))
        else:
            logging.error("GOUFI: cannot import " + toString(import_file.filename))
