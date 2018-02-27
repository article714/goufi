# -*- coding: utf-8 -*-
'''
Created on 23 deb. 2018

@author: C. Guychard
@copyright: ©2018 Article 714
@license: AGPL v3
'''

from os import path
import logging

from odoo import exceptions

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
    def does_file_need_processing(self, import_file):
        """
        Returns true if the given ImportFile is to be processed
        """
        result = super(Processor, self).does_file_need_processing(import_file)
        return (self.is_data_file(import_file.filename) and result)

    #-------------------------------------------------------------------------------------
    def process_data(self, import_file):
        """
        Method that actually process data
        """
        self.logger.info("Simple mapping IMPORT; process DATA: " + toString(import_file.filename))

    #-------------------------------------------------------------------------------------
    def process_header(self, import_file):
        """
        Method that process header and configure processing depending on import configuration
        """
        self.logger.info("Simple mapping IMPORT; process HEADERS: " + toString(import_file.filename))

