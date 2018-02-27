# -*- coding: utf-8 -*-
'''
Created on 26 feb. 2018

@author: C. Guychard
@copyright: ©2018 Article 714
@license: AGPL v3
'''

from calendar import timegm
from datetime import datetime
from os import path, remove
import base64
import logging

from odoo import exceptions
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

from odoo.addons.goufi_base.models.import_configuration import ImportConfiguration
from odoo.addons.goufi_base.models.import_file import ImportFile
from odoo.addons.goufi_base.utils.converters  import toString

#-------------------------------------------------------------------------------------
# STATIC GLOBAL Properties
procLogFmt = logging.Formatter('%(relativeCreated)6d %(message)s')
procLogDefaultLogger = logging.getLogger("GoufiImportProcessor")


#-------------------------------------------------------------------------------------
# MAIN CLASS
class AbstractProcessor(object):
    """
    A base class to provide standard utilities an default implementation of any Processor method

    Initialize logger specific of the current instance of processor
    """

    #-------------------------------------------------------------------------------------
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

    #-------------------------------------------------------------------------------------
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

    #-------------------------------------------------------------------------------------
    def close_and_reset_logger(self):
        """
        close existing logger and reset self.logger to default one
        """
        if self.logger_fh:

            # deletes log file
            filename = self.logger_fh.baseFilename
            self.logger.removeHandler(self.logger_fh)
            self.logger_fh.close()
            self.logger_fh = None
            try:
                remove(filename)
            except OSError:
                pass

    #-------------------------------------------------------------------------------------
    def does_file_need_processing(self, import_file):
        """
        Returns true if the given ImportFile is to be processed
        """
        if isinstance(import_file, ImportFile):

            result = import_file.to_process
            result = result and (import_file.processing_status == 'new' or import_file.process_when_updated)
            result = result and (import_file.processing_status != 'running')
            if import_file.process_when_updated:
                upd_time = timegm(datetime.strptime(import_file.date_updated, DEFAULT_SERVER_DATETIME_FORMAT).timetuple())
                if import_file.date_stop_processing:
                    lastproc_time = timegm(datetime.strptime(import_file.date_stop_processing, DEFAULT_SERVER_DATETIME_FORMAT).timetuple())
                else:
                    lastproc_time = 0
                result = result and (upd_time > lastproc_time)
            return result
        else:
            return False

    #-------------------------------------------------------------------------------------
    def start_processing(self, import_file):
        """
        Method that prepares the processing
        """
        self.logger.info("Start processing of file " + toString(import_file.filename))
        import_file.processing_status = 'running'
        import_file.date_start_processing = datetime.now()
        return True

    #-------------------------------------------------------------------------------------
    def process_data(self, import_file):
        """
        Method that actually process data
        Should return True on success and False on failure
        """
        raise exceptions.ValidationError("GOUFI: un-implemented process_data method")

    #-------------------------------------------------------------------------------------
    def process_header(self, import_file):
        """
        Method that process header and configure processing depending on import configuration
        """
        raise exceptions.ValidationError("GOUFI: un-implemented process_header method")

    #-------------------------------------------------------------------------------------
    def end_processing(self, import_file, success = True):
        """
        Method that closes-up the processing
        """
        self.logger.info("End processing of file " + toString(import_file.filename))
        if success:
            import_file.processing_status = 'ended'
        else:
            import_file.processing_status = 'failure'

        # uploads log file
        # TODO: deal with big log files
        if self.logger_fh:
            file_base64 = ''
            with open(self.logger_fh.baseFilename, "rb") as file:
                file_base64 = base64.b64encode(file.read())
            import_file.processing_logs = file_base64

        import_file.date_stop_processing = datetime.now()
        return True

    #-------------------------------------------------------------------------------------
    def process_file(self, import_file, force = False):
        """
        Generic method to run all processing steps
        """
        if import_file:
            if (self.does_file_need_processing(import_file)or force):
                self.create_dedicated_filelogger(path.basename(import_file.filename))
                if self.start_processing(import_file):
                    self.process_header(import_file)
                    self.process_data(import_file)
                    self.end_processing(import_file)
                else:
                    self.logger.error("Issue when initiliazing processing")
                self.close_and_reset_logger()
        else:
            logging.error("GOUFI: cannot import " + toString(import_file.filename))

