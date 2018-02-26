# -*- coding: utf-8 -*-
'''
Created on 26 feb. 2018

@author: C. Guychard
@copyright: ©2018 Article 714
@license: AGPL v3
'''

import logging

from odoo.addons.goufi_base.models.import_configuration import ImportConfiguration
from odoo.addons.goufi_base.utils.converters  import toString


#-------------------------------------------------------------------------------------
# MAIN CLASS
class AbstractProcessor():
    """
    A base class to provide standard utilities an default implementation of any Processor method

    Initialize logger specific of the current instance of processor
    """

    def __init__(self, parent_config):
        """
        Constructor
        parent_config should be an instance of ImportConfiguration
        """

        self.logger = logging.getLogger("GoufiImportProcessor")

        if isinstance(parent_config, ImportConfiguration):
            self.parent_config = parent_config
        else:
            self.parent_config = None
            self.logger.error("GOUFI: error- wrong parameter type given when creating a new Processor instance")

    def create_dedicated_filelogger(self):
        """
        Creates a instance of a dedicated logger that will log to a file the current processing results
        """

        # fichier de log
        logpath = self.getConfigValue("output_directory") + os.path.sep + "LOG" + os.path.sep
        filename_TS = datetime.datetime.now().strftime("%Y-%m-%d")
        fh = logging.FileHandler(filename = logpath + self.name + '_' + filename_TS + '.log', mode = 'w')
        fh.setLevel(level = logging.INFO)
        self.logger = fh

    def close_and_reset_logger(self):
        """
        close existing logger and reset self.logger to default one
        """
        default_logger = logging.getLogger("GoufiImportProcessor")
        if self.logger != default_logger:
            self.logger.close()
            self.logger = default_logger

    #-------------------------------------------------------------------------------------
    def process_file(self, import_file):
        logging.warning("Goufi Simple Mappings Import: " + toString(import_file.filename))
        return True

