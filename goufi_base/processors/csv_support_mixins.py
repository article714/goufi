# -*- coding: utf-8 -*-
'''
Created on 17 may 2018

@author: C. Guychard
@copyright: ©2018 Article 714
@license: AGPL v3
'''

"""
a set of classes to be used in mixins for processor that provide support for importing CSV files
"""

import csv
import logging


#-------------------------------------------------------------------------------------
# CONSTANTS
AUTHORIZED_EXTS = ('csv')


class CSVImporterMixin(object):

    def __init__(self, parent_config):

        self.csv_file = None

        # TODO: document parameters
        self.csv_separator = ","
        self.csv_string_separator = "\""
        for param in parent_config.processor_parameters:
            if param.name == u'csv_separator':
                self.csv_separator = param.value
            if param.name == u'csv_string_separator':
                self.csv_string_separator = param.value
        self.target_model = None

    #-------------------------------------------------------------------------------------
    def _open_csv(self, import_file, asDict=True):
        try:
            self.csv_file = open(import_file.filename, 'rt', encoding='utf-8')
            if asDict:
                reader = csv.DictReader(self.csv_file, quotechar=str(
                    self.csv_string_separator), delimiter=str(self.csv_separator))
            else:
                reader = csv.reader(self.csv_file, quotechar=str(
                    self.csv_string_separator), delimiter=str(self.csv_separator))
            return reader
        except:
            if self.csv_file != None:
                self.csv_file.close()
                self.csv_file = None
            if import_file:
                self.logger.error("Cannot open the file %s", import_file.filename)
            else:
                self.logger.error("Cannot open CSV file: None given")
            return None

    #-------------------------------------------------------------------------------------
    def _close_csv(self):
        if self.csv_file != None:
            self.csv_file.close()
            self.csv_file = None

    #-------------------------------------------------------------------------------------
    # Provides a dictionary of values in a row
    def get_row_values_as_dict(self, tab=None, row=None, tabheader=None):

        if isinstance(row, dict):
            return row
        else:
            resultDict = {}
            for idx in range(len(tabheader)):
                resultDict[tabheader[idx]] = row[idx]
            return resultDict

    #-------------------------------------------------------------------------------------
    # Provides a dictionary of values in a row
    def get_row_values(self, tab=None, row=None):
        logging.warning("POUET PUE get_row_values %s", str(type(row)))
        if isinstance(row, dict):
            values = []
            logging.warning("POUET PUE get_row_values dict")
            for k in row:
                logging.warning("POUET PUE get_row_values dict %s %s", k, str(row))
                values.append(row[k])
            return values
        else:
            logging.warning("POUET PUE get_row_values PAS dict")
            return row

    #-------------------------------------------------------------------------------------
    def process_file(self, import_file, force=False):

        ext = import_file.filename.split('.')[-1]
        if (ext in AUTHORIZED_EXTS):
            super(CSVImporterMixin, self).process_file(import_file, force)
        else:
            self.logger.error("Cannot process file: Wrong extension -> %s", ext)
            self.end_processing(import_file, success=False, status='failure', any_message="Wrong file extension")
