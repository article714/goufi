# -*- coding: utf-8 -*-
'''
Created on 26 feb. 2018

@author: C. Guychard
@copyright: ©2018 Article 714
@license: AGPL v3
'''

from datetime import datetime
from os import path, remove
import base64
import logging

from odoo.exceptions import ValidationError

from odoo.addons.goufi_base.models.import_configuration import ImportConfiguration
from odoo.addons.goufi_base.models.import_file import ImportFile
from odoo.addons.goufi_base.utils.converters  import toString

#-------------------------------------------------------------------------------------
# STATIC GLOBAL Properties
procLogFmt = logging.Formatter('%(asctime)s -(%(filename)s,%(lineno)d) - [%(levelname)s] - %(message)s')
procLogDefaultLogger = logging.Logger("GoufiImportProcessor", logging.INFO)


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
        procLogDefaultLogger.setLevel(logging.INFO)
        self.logger = procLogDefaultLogger
        self.logger_fh = None
        self.odooenv = None

        if isinstance(parent_config, ImportConfiguration):
            self.parent_config = parent_config
            self.odooenv = self.parent_config.env
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
            self.logger_fh.flush()
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
    def start_processing(self, import_file):
        """
        Method that prepares the processing
        """
        self.logger.info("Start processing of file " + toString(import_file.filename))
        import_file.processing_status = 'running'
        import_file.date_start_processing = datetime.now()
        import_file.date_stop_processing = False
        import_file.processing_result = ''
        self.odooenv.cr.commit()
        return True

    #-------------------------------------------------------------------------------------
    def process_data(self, import_file):
        """
        Method that actually process data
        Should return True on success and False on failure
        """
        raise ValidationError("GOUFI: un-implemented process_data method")

    #-------------------------------------------------------------------------------------
    def end_processing(self, import_file, success = True):
        """
        Method that closes-up the processing
        """
        self.logger.info("End processing of aFile " + toString(import_file.filename))
        if success:
            import_file.processing_status = 'ended'
            import_file.processing_result = 'OK'
        else:
            self.odooenv.cr.rollback()
            import_file.processing_status = 'failure'

        # unset the processing marker

        import_file.to_process = import_file.process_when_updated

        # uploads log aFile
        # TODO: deal with big log files
        if self.logger_fh:
            file_base64 = ''
            with open(self.logger_fh.baseFilename, "rb") as aFile:
                file_base64 = base64.b64encode(aFile.read())
            import_file.processing_logs = file_base64

        import_file.date_stop_processing = datetime.now()
        self.odooenv.cr.commit()
        return True

    #-------------------------------------------------------------------------------------
    def process_file(self, import_file, force = False):
        """
        Generic method to run all processing steps
        """
        if import_file:
            try:
                if import_file.does_file_need_processing(force):
                    self.create_dedicated_filelogger(path.basename(import_file.filename))
                    if self.start_processing(import_file):
                        result = self.process_data(import_file)
                        result = (result == None) or (result == True)
                        self.end_processing(import_file, result)
                    else:
                        self.logger.error("Issue when initiliazing processing")
                    self.close_and_reset_logger()
            except Exception as e:
                self.odooenv.cr.rollback()
                self.logger.exception("GOUFI: error while import file %s -> %s " % (toString(import_file.filename), str(e)))
                import_file.processing_status = 'failure'
                self.odooenv.cr.commit()
        else:
            self.logger.error("GOUFI: cannot import " + toString(import_file.filename))

