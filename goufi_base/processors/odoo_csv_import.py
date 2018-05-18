# -*- coding: utf-8 -*-
'''
Created on 3 mai 2018

@author: C. Guychard
@copyright: ©2018 Article 714
@license: AGPL v3
'''


import re

from odoo.tools.misc import ustr

from odoo.addons.goufi_base.utils.converters import toString

from .csv_support_mixins import CSVImporterMixin
from .processor import AbstractProcessor


#-----------------------------------------------4--------------------------------------
# Global private variables
_reHeader = re.compile(r'[0-9]+\_')

#-----------------------------------------------4--------------------------------------
# MAIN CLASS


class OdooCSVProcessor(CSVImporterMixin, AbstractProcessor):
    """
    A processor that import csv files that are Odoo compatible (same as in modules source code

    Can use the following parameters:
        * csv_separator => define the seperator between fields

    """

    #----------------------------------------------------------
    def __init__(self, parent_config):
        AbstractProcessor.__init__(self, parent_config)
        CSVImporterMixin.__init__(self, parent_config)

    #-------------------------------------------------------------------------------------
    def process_data(self, import_file):
        """
        Method that actually process data
        """

        self.logger.info("Odoo csv data import: " + toString(import_file.filename))

        if self.parent_config:
            if self.parent_config.target_object:
                self.target_model = self.parent_config.target_object.model
        if self.target_model == None:
            # Search for target model
            self.search_target_model_from_filename(import_file)
        if self.target_model == None:
            self.logger.exception("Not able to guess target model: " + toString(import_file.filename))
            return False

        try:

            reader = self._open_csv(import_file, asDict=False)
            if reader == None:
                self.logger.error("Cannot load CSV reader")
                self.end_processing(import_file, False, 'failure', "Cannot load CSV reader")
                return False

            fields = reader.next()

            if not ('id' in fields):
                self.logger.error("Import specification does not contain 'id', Cannot continue.")
                return False

            datas = []
            for line in reader:
                if not (line and any(line)):
                    continue
                try:
                    datas.append(map(ustr, line))
                except Exception:
                    self.logger.error("Cannot import the line: %s", line)

            result = self.target_model.load(fields, datas)
            if any(msg['type'] == 'error' for msg in result['messages']):
                # Report failed import and abort module install
                warning_msg = "\n".join(msg['message'] for msg in result['messages'])
                self.logger.error('Processing of file %s failed: %s', import_file.filename,  warning_msg)
                self.end_processing(import_file, False, 'failure', warning_msg)
                return False

            return True

        except Exception as e:
            self.logger.exception("Processing Failed: " + str(e))
            self.end_processing(import_file, False, 'failure',  str(e))
            return False
        finally:
            self._close_csv()
