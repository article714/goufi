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
import re

from odoo.exceptions import ValidationError

from odoo.addons.goufi_base.models.import_configuration import ImportConfiguration
from odoo.addons.goufi_base.models.import_file import ImportFile
from odoo.addons.goufi_base.utils.converters import toString


#-------------------------------------------------------------------------------------
# STATIC GLOBAL Properties
procLogFmt = logging.Formatter('%(asctime)s -(%(filename)s,%(lineno)d) - [%(levelname)s] - %(message)s')
procLogDefaultLogger = logging.Logger("GoufiImportProcessor", logging.INFO)

_reHeader = re.compile(r'[0-9]+[\_\.]')

#-------------------------------------------------------------------------------------
# MAIN CLASS


class AbstractProcessor(object):
    """
    A base class to provide standard utilities an default implementation of any Processor method

    Initialize logger specific of the current instance of processor
    """

    # TODO => document the API
    # TODO => document hooks
    # self.hooks['_prepare_mapping_hook']  => prepare_mapping_hook(self,
    # importtab=None, tabtuple=None, colmappings=None):

    #-------------------------------------------------------------------------------------
    def __init__(self, parent_config):
        """
        Constructor
        parent_config should be an instance of ImportConfiguration
        """

        # default logging
        procLogDefaultLogger.setLevel(logging.INFO)
        self.logger = procLogDefaultLogger
        self.logger_fh = None

        # error reporting mechanism
        self.errorCount = 0

        # hooks
        self.hooks = {}

        # default target model
        self.target_model = None

        # current header index
        self.header_line_idx = parent_config.default_header_line_index

        # set language in context
        lang = parent_config.context_language
        if lang == False:
            lang = parent_config._get_default_language()

        # setup links with odoo environment
        self.odooenv = None
        if isinstance(parent_config, ImportConfiguration):
            self.parent_config = parent_config
            if lang:
                self.odooenv = self.parent_config.env(context={'lang': lang.code})
            else:
                self.odooenv = self.parent_config.env
        else:
            self.parent_config = None
            self.logger.error("GOUFI: error- invalid configuration")

    #-------------------------------------------------------------------------------------
    def create_dedicated_filelogger(self, name_complement="hello"):
        """
        Creates a instance of a dedicated logger that will log to a file the current processing results

        """

        # fichier de log
        if self.parent_config.working_dir and path.exists(self.parent_config.working_dir) and path.isdir(self.parent_config.working_dir):

            logpath = self.parent_config.working_dir + path.sep
            filename_TS = datetime.now().strftime("%Y-%m-%d")
            fh = logging.FileHandler(filename=logpath + "goufi" + name_complement +
                                     '_' + filename_TS + '.log', mode='w')
            fh.setFormatter(procLogFmt)
            fh.setLevel(level=logging.INFO)
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
    def search_target_model_from_filename(self, import_file):

        if self.target_model == None:
            try:
                self.target_model = self.odooenv[self.parent_config.target_object.model]
            except:
                self.target_model = None

        if self.target_model == None:

            self.logger.warning("No target model set on configuration, attempt to find it from file name")

            bname = path.basename(import_file.filename)
            modelname = '.'.join(bname.split('.')[:-1])

            if _reHeader.match(modelname):
                modelname = _reHeader.sub('', modelname)

            try:
                self.target_model = self.odooenv[modelname]
            except:
                modelname = modelname.replace('_', '.')
            if self.target_model == None:
                try:
                    self.target_model = self.odooenv[modelname]
                except:
                    self.target_model = None
                    self.end_processing(import_file, success=False, status='failure',
                                        any_message=u"Model Not found: %s" % modelname)

    #-------------------------------------------------------------------------------------
    def start_processing(self, import_file):
        """
        Method that prepares the processing
        """
        # init
        self.logger.info("Start processing of file " + toString(import_file.filename))
        self.errorCount = 0

        # update import_file data
        import_file.processing_status = 'running'
        import_file.date_start_processing = datetime.now()
        import_file.date_stop_processing = False
        import_file.processing_logs = False
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
    def end_processing(self, import_file, success=True, status='ended', any_message='Done'):
        """
        Method that closes-up the processing
        """
        self.logger.info("End processing of aFile " + toString(import_file.filename))

        if not success:
            self.odooenv.cr.rollback()
            import_file.processing_status = 'failure'
        elif self.errorCount > 0:
            import_file.processing_status = 'error'
            if any_message == 'Done':
                any_message = 'Ended with %d Errors' % self.errorCount
        else:
            import_file.processing_status = status
        import_file.processing_result = any_message

        # unset the processing marker

        import_file.to_process = import_file.process_when_updated

        # uploads log aFile
        # TODO: deal with big log files
        if self.logger_fh:
            self.logger_fh.close()
            file_base64 = ''
            with open(self.logger_fh.baseFilename, "rb") as aFile:
                file_base64 = base64.b64encode(aFile.read())
            import_file.processing_logs = file_base64
            self.close_and_reset_logger()

        import_file.date_stop_processing = datetime.now()
        self.odooenv.cr.commit()
        return True

    #-------------------------------------------------------------------------------------
    def process_file(self, import_file, force=False):
        """
        Generic method to run all processing steps
        """
        if import_file:
            try:
                if import_file.does_file_need_processing(force):
                    self.create_dedicated_filelogger(path.basename(import_file.filename))
                    if self.start_processing(import_file):
                        try:
                            result = self.process_data(import_file)
                            result = (result == None) or (result == True)
                            # reports result
                            if self.errorCount == 0:
                                self.end_processing(import_file, success=result, status='ended')
                            else:
                                self.end_processing(import_file, success=result, status='error',
                                                    any_message="%d errors raised during data processing" % self.errorCount)

                        except Exception as e:
                            self.odooenv.cr.rollback()
                            self.logger.exception("GOUFI: error while processing data (file %s) -> %s " %
                                                  (toString(import_file.filename), str(e)))
                            self.end_processing(import_file, success=False, status='failure',
                                                any_message="Error: Generic Exception (%s)" % str(e))
                            self.odooenv.cr.commit()

                    else:
                        self.logger.error("Issue when initiliazing processing")
                        self.end_processing(import_file, success=False, status='error',
                                            any_message="Failed when initializing processing")

            except Exception as e:
                self.odooenv.cr.rollback()
                self.logger.exception("GOUFI: error while import file %s -> %s " %
                                      (toString(import_file.filename), str(e)))
                self.end_processing(import_file, success=False, status='failure',
                                    any_message="Error: Generic Exception (%s)" % str(e))
                self.odooenv.cr.commit()
        else:
            self.logger.error("GOUFI: cannot import : no import_file provided !")
            logging.exception("GOUFI: cannot import : no import_file provided !")

#-------------------------------------------------------------------------------------
# LineIterator CLASS


class LineIteratorProcessor(AbstractProcessor):
    """
    A processor that must provide a generator to iterate on each line of the  file
    """

    #-------------------------------------------------------------------------------------
    # Process line values
    def process_values(self, line_index=-1, data_values=()):

        raise ValidationError("GOUFI: un-implemented generator method")

    #-------------------------------------------------------------------------------------
    # line generator
    def get_rows(self, import_file=None):

        raise ValidationError("GOUFI: un-implemented process_data method")

    #-------------------------------------------------------------------------------------
    # line generator
    def prepare_mappings(self, import_file=None):
        if import_file and import_file.import_config:
            if "_prepare_mapping_hook" in self.hooks:
                result = self.hooks['_prepare_mapping_hook'](
                    self, colmappings=import_file.import_config.column_mappings)
            else:
                self.logger.info("Default method does nothing: %s", import_file.filename)
                result = -1
        else:
            result = -1
        return result

    #-------------------------------------------------------------------------------------
    def process_data(self, import_file):
        """
        Method that actually process data
        Should return True on success and False on failure
        """

        idx = 0
        nb_mappings = self.prepare_mappings(import_file)
        if nb_mappings > 0:
            # TODO: document this
            if ('import_processed' in self.target_model.fields_get_keys()):
                            # hook for objects needing to be set as processed through import
                self.odooenv.cr.execute(
                    'update %s set import_processed = False' % toString(self.target_model._table))
                self.odooenv.cr.commit()
            for row in self.get_rows(import_file):
                idx += 1
                try:
                    self.process_values(idx, row)
                except Exception as e:
                    self.logger.exception(u"Error when processing line N° %d", idx)
                    self.errorCount += 1
                    self.odooenv.cr.rollback()
                    return -1
        elif nb_mappings < 0:
            self.logger.error("Could not prepare mapping configuration for file: %s", import_file.filename)
            self.errorCount += 1

        return nb_mappings

#-------------------------------------------------------------------------------------
# MultiSheetLineIterator CLASS


class MultiSheetLineIterator(AbstractProcessor):
    """
    A processor that must provide a generator to iterate on each line of the  file
    """

    #-------------------------------------------------------------------------------------
    # tab generator
    # must return a tuple (tabname, Object)
    def get_tabs(self, import_file=None):

        raise ValidationError("GOUFI: un-implemented process_data method")

    #-------------------------------------------------------------------------------------
    # line generator
    # must return a tuble(index, Object)
    def get_rows(self, tab=None):

        raise ValidationError("GOUFI: un-implemented process_data method")

    #-------------------------------------------------------------------------------------
    # Process tab header, in order to provide a list of columns to process
    # must return a list of column titles in header
    def process_tab_header(self, tab=None,  headerrow=None):

        raise ValidationError("GOUFI: un-implemented generator method")

    #-------------------------------------------------------------------------------------
    # Provides a dictionary of values in a row
    def get_row_values_as_dict(self, tab=None, row=None, tabheader=None):

        raise ValidationError("GOUFI: un-implemented generator method")

    #-------------------------------------------------------------------------------------
    # Process line values
    def process_values(self, line_index=-1, data_values=()):

        raise ValidationError("GOUFI: un-implemented generator method")

    #-------------------------------------------------------------------------------------
    # prepare mappins configuration for tab processing,
    # must return an integer > 0 if successful and something to process
    #                         0 if nothing to do or ignore
    #                         -1 if failure
    def prepare_mappings_for_tab(self, import_file=None, tab=None):

        if import_file and tab:
            tab_name = tab[0]
            tabmap_model = self.odooenv['goufi.tab_mapping']
            # Look for target Model in parent config
            parent_config = import_file.import_config
            if parent_config:
                if tab_name != None:
                    found = tabmap_model.search(
                        [('parent_configuration', '=', parent_config.id), ('name', '=', tab_name)], limit=1)
                    if len(found) == 1:
                        current_tab = found[0]
                        try:
                            # Explicitly ignore
                            if found[0].ignore_tab:
                                self.logger.info("Tab ignored by configuration: " + toString(tab_name))
                                return 0
                            self.target_model = self.odooenv[current_tab.target_object.model]
                            self.header_line_idx = current_tab.default_header_line_index
                            if "_prepare_mapping_hook" in self.hooks:
                                result = self.hooks['_prepare_mapping_hook'](self, importtab=current_tab, tabtuple=tab)
                            else:
                                result = len(current_tab.column_mappings)

                        except:
                            self.logger.exception("Target model not found for " + toString(tab_name))
                            return -1
                    else:
                        self.logger.error("Tab configuration not found: " + toString(tab_name))
                        return -1
                else:
                    self.logger.error("No tab name given")
                    return -1
            else:
                self.logger.error("No configuration found for tab %s", tab_name)
                return -1
        else:
            self.logger.error("No import_file or no Tab %s, %s", str(import_file), str(tab))
            return -1

        return result

    #-------------------------------------------------------------------------------------
    def process_data(self, import_file):
        """
        Method that actually process data
        Should return True on success and False on failure
        """
        for tab in self.get_tabs(import_file):
            try:
                nb_mappings = self.prepare_mappings_for_tab(import_file, tab)
                if nb_mappings > 0:
                    idx = 0
                    header = None
                    # TODO Document this
                    if ('import_processed' in self.target_model.fields_get_keys()):
                            # hook for objects needing to be set as processed through import
                        self.odooenv.cr.execute(
                            'update %s set import_processed = False' % toString(self.target_model._table))
                        self.odooenv.cr.commit()
                    for row in self.get_rows(tab):
                        try:
                            if idx == self.header_line_idx:
                                # process header for tab
                                header = self.process_tab_header(tab, row)
                            elif idx > self.header_line_idx:
                                # process data for tab
                                if header != None and len(header) > 0:
                                    values = self.get_row_values_as_dict(tab, row, header)
                                else:
                                    self.logger.error(u"Header line is empty")
                                    self.errorCount += 1
                                    break
                                try:
                                    self.process_values(idx, values)
                                except Exception as e:
                                    self.logger.exception(u"Error when processing line N°%d in %s", idx + 1, tab[0])
                            idx += 1
                        except Exception as e:
                            self.logger.exception(u"Error when processing line N° %d of tab %s", idx + 1, tab[0])
                            self.errorCount += 1
                            self.odooenv.cr.rollback()
                            return False
                elif nb_mappings < 0:
                    self.logger.error("Could not prepare mapping configuration for Tab: %s", tab[0])
                    self.errorCount += 1
            except Exception as e:
                self.logger.exception(u"Error when processing a Tab:  %s", tab[0])
                self.errorCount += 1
                self.odooenv.cr.rollback()

        return self.errorCount == 0
