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


from .processor import AbstractProcessor


#-------------------------------------------------------------------------------------
# CONSTANTS
AUTHORIZED_EXTS = ('csv')


class CSVImporterMixin(AbstractProcessor):

    def __init__(self, parent_config):

        # TODO: document parameters
        super(CSVImporterMixin, self).__init__(parent_config)
        self.csv_separator = ","
        self.csv_string_separator = "\""
        for param in parent_config.processor_parameters:
            if param.name == u'csv_separator':
                self.csv_separator = param.value
            if param.name == u'csv_string_separator':
                self.csv_string_separator = param.value
        self.target_model = None

    #-------------------------------------------------------------------------------------
    def process_file(self, import_file, force=False):

        ext = import_file.filename.split('.')[-1]
        if (ext in AUTHORIZED_EXTS):
            super(CSVImporterMixin, self).process_file(import_file, force)
        else:
            self.logger.error("Cannot process file: Wrong extension -> %s", ext)
            self.end_processing(import_file, success=False, status='failure', any_message="Wrong file extension")
