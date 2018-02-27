# -*- coding: utf-8 -*-
'''
Created on 26 feb. 2018

@author: C. Guychard
@copyright: ©2018 Article 714
@license: AGPL v3
'''

from datetime import datetime
from os import path
import logging

from odoo.addons.goufi_base.models.import_configuration import ImportConfiguration
from odoo.addons.goufi_base.models.import_file import ImportFile
from odoo.addons.goufi_base.utils.converters  import toString

#-------------------------------------------------------------------------------------
# STATIC GLOBAL Properties

procLogFmt = logging.Formatter('%(relativeCreated)6d %(message)s')
procLogDefaultLogger = logging.getLogger("GoufiImportProcessor")


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

        self.logger = procLogDefaultLogger
        self.logger_fh = None

        if isinstance(parent_config, ImportConfiguration):
            self.parent_config = parent_config
        else:
            self.parent_config = None
            self.logger.error("GOUFI: error- wrong parameter type given when creating a new Processor instance")

    def create_dedicated_filelogger(self, name_complement = "hello"):
        """
        Creates a instance of a dedicated logger that will log to a file the current processing results

        """

        # fichier de log
        if self.parent_config.working_dir and path.exists(self.parent_config.working_dir) and path.isdir(self.parent_config.working_dir):

            logpath = self.parent_config.working_dir + path.sep
            filename_TS = datetime.now().strftime("%Y-%m-%d")
            fh = logging.FileHandler(filename = logpath + "goufi" + name_complement + '_' + filename_TS + '.log', mode = 'w')
            fh.setFormatter(procLogFmt)
            fh.setLevel(level = logging.INFO)
            self.logger_fh = fh
            self.logger.addHandler(fh)
        else:
            self.logger.error("GOUFI: error- wrong working dir")

    def close_and_reset_logger(self):
        """
        close existing logger and reset self.logger to default one
        """
        if self.logger_fh:
            self.logger.removeHandler(self.logger_fh)
            self.logger_fh.close()
            self.logger_fh = None

    def does_file_need_processing(self, import_file):

        if isinstance(import_file, ImportFile):
            return True

    #-------------------------------------------------------------------------------------
    def process_file(self, import_file):
        logging.warning("Goufi Simple Mappings Import: " + toString(import_file.filename))
        return True

