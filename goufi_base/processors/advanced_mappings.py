# -*- coding: utf-8 -*-
'''
Created on 23 feb. 2018

@author: C. Guychard
@copyright: ©2018 Article 714
@license: AGPL v3
'''

import logging

from odoo.addons.goufi_base.utils.converters import toString

from .processor import AbstractProcessor

#-------------------------------------------------------------------------------------
# CONSTANTS
AUTHORIZED_EXTS = ('xlsx', 'xls', 'csv')

#-------------------------------------------------------------------------------------
# MAIN CLASS


class Processor(AbstractProcessor):

    def __init__(self, parent_config):
        super(Processor, self).__init__(parent_config)

    #-------------------------------------------------------------------------------------
    def does_file_need_processing(self, import_file):
        """
        Returns true if the given ImportFile is to be processed
        """
        result = super(Processor, self).does_file_need_processing(import_file)
        ext = import_file.filename.split('.')[-1]
        return ((ext in AUTHORIZED_EXTS) and result)

    #-------------------------------------------------------------------------------------
    def process_data(self, import_file):
        logging.warning("Goufi Advanced Mappings Import: " + toString(import_file.filename))

