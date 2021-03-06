# -*- coding: utf-8 -*-
"""
Created on 26 feb. 2018

@author: C. Guychard
@copyright: ©2018 Article 714
@license: AGPL v3
"""

from datetime import datetime
from os import path, remove
import base64
import logging
import re

from odoo.exceptions import ValidationError

from odoo.addons.goufi_base.models.import_configuration import ImportConfiguration
from odoo.addons.goufi_base.models.import_file import ImportFile
from odoo.addons.goufi_base.utils.converters import toString


# -------------------------------------------------------------------------------------
# STATIC GLOBAL Properties
procLogFmt = logging.Formatter(
    "%(asctime)s -(%(filename)s,%(lineno)d) - [%(levelname)s] - %(message)s"
)

_reHeader = re.compile(r"[0-9]+[\_\.]")

# -------------------------------------------------------------------------------------
# list of hooks and consolidation functions

# TODO TODO TODO

# -------------------------------------------------------------------------------------
# MAIN CLASS


class AbstractProcessor(object):
    """
    A base class to provide standard utilities an default implementation of any Processor method

    Initialize logger specific of the current instance of processor
    """

    # TODO => document the API
    # TODO => document hooks
    # self.hooks '_prepare_mapping_hook'=> prepare_mapping_hook(self,tab_name="Unknown",, colmappings=None):

    # -------------------------------------------------------------------------------------
    # Some utility function that we might use in data transformations

    def remove_all_spaces(self, value):
        try:
            return value.strip().replace(u" ", "")
        except:
            return value

    # -------------------------------------------------------------------------------------
    def __init__(self, parent_config):
        """
        Constructor
        parent_config should be an instance of ImportConfiguration
        """

        # prevent multiple run of init in multi-inheritance mixins
        if not hasattr(self, "already_up"):

            # default logging
            self.logger = None
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
                    self.odooenv = self.parent_config.env(context={"lang": lang.code})
                else:
                    self.odooenv = self.parent_config.env
            else:
                self.parent_config = None
                self.logger.error("GOUFI: error- invalid configuration")

            # prevent re_run of __init__
            self.already_up = True

    # -------------------------------------------------------------------------------------
    def register_hook(self, hook_name="never_called", func=None):
        if func != None and callable(func):
            if hook_name not in self.hooks:
                self.hooks[hook_name] = []
            if func not in self.hooks[hook_name]:
                # prevent double insertion of the same hook
                self.hooks[hook_name].append(func)

    # -------------------------------------------------------------------------------------
    def run_hooks(self, hook_name, *args, **kwargs):
        result = None
        if hook_name in self.hooks:
            for hook in self.hooks[hook_name]:
                result = hook(self, *args, **kwargs)
        else:
            return True
        return result

    # -------------------------------------------------------------------------------------
    def create_dedicated_filelogger(self, name_complement="hello"):
        """
        Creates a instance of a dedicated logger that will log to a file the current processing results

        """

        if self.logger != None:
            logging.warning("GOUFI: logger for current instance is not new")
        else:
            self.logger = logging.getLogger("GoufiIP.%s" % name_complement)
        # reset handlers
        for h in list(self.logger.handlers):
            self.logger.removeHandler(h)
        self.logger.propagate = 0
        self.logger.setLevel(logging.INFO)

        # fichier de log
        if self.parent_config.working_dir:

            work_dir = self.parent_config.working_dir
            if "~" in work_dir:
                work_dir = path.expanduser(work_dir)
            if "$" in work_dir:
                work_dir = path.expandvars(work_dir)

            if path.exists(work_dir) and path.isdir(work_dir):

                logpath = work_dir + path.sep
                filename_TS = datetime.now().strftime("%Y-%m-%d")
                fh = logging.FileHandler(
                    filename="%sgoufi_%s_%s%s"
                    % (logpath, name_complement, filename_TS, ".log"),
                    mode="w",
                )
                fh.setFormatter(procLogFmt)
                fh.setLevel(logging.INFO)
                self.logger.addHandler(fh)
                self.logger_fh = fh
                self.logger.info("Started the new file handler: %s", str(fh))
            else:
                logging.error(
                    "GOUFI: error- wrong working dir, fall back to default logger"
                )
                self.logger = logging

    # -------------------------------------------------------------------------------------
    def close_and_reset_logger(self):
        """
        close existing logger and reset self.logger to default one
        """
        if self.logger_fh != None:
            self.logger.warning("Will flush and close log file %s", str(self.logger))
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
        if self.logger != None:
            self.logger = None

    # -------------------------------------------------------------------------------------

    def search_target_model_from_filename(self, import_file):

        if self.target_model == None:
            try:
                self.target_model = self.odooenv[self.parent_config.target_object.model]
            except:
                self.target_model = None

        if self.target_model == None and not self.parent_config.tab_support:

            self.logger.warning(
                "No target model set on configuration, attempt to find it from file name"
            )

            bname = path.basename(import_file.filename)
            modelname = ".".join(bname.split(".")[:-1])

            if _reHeader.match(modelname):
                modelname = _reHeader.sub("", modelname)

            try:
                self.target_model = self.odooenv[modelname]
            except:
                modelname = modelname.replace("_", ".")
            if self.target_model == None:
                try:
                    self.target_model = self.odooenv[modelname]
                except:
                    self.target_model = None
                    self.errorCount += 1
                    self.logger.error("Model Not found: %s", modelname)

    # -------------------------------------------------------------------------------------
    def start_processing(self, import_file):
        """
        Method that prepares the processing
        """
        # init
        self.logger.info("Start processing of file " + toString(import_file.filename))
        self.errorCount = 0

        # update import_file data
        import_file.processing_status = "running"
        import_file.date_start_processing = datetime.now()
        import_file.date_stop_processing = False
        import_file.processing_logs = False
        import_file.processing_result = False
        self.odooenv.cr.commit()
        return True

    # -------------------------------------------------------------------------------------
    def process_data(self, import_file):
        """
        Method that actually process data
        Should return True on success and False on failure
        """
        raise ValidationError("GOUFI: un-implemented process_data method")

    # -------------------------------------------------------------------------------------
    def end_processing(
        self, import_file, success=True, status="ended", any_message="Done"
    ):
        """
        Method that closes-up the processing
        """
        if self.logger:
            self.logger.info(
                "End processing of aFile " + toString(import_file.filename)
            )

        if not success:
            self.odooenv.cr.rollback()
            import_file.processing_status = "failure"
        elif self.errorCount > 0:
            import_file.processing_status = "error"
            if any_message == "Done":
                any_message = "Ended with %d Errors" % self.errorCount
        else:
            import_file.processing_status = status
        import_file.processing_result = any_message

        # unset the processing marker

        import_file.to_process = import_file.process_when_updated

        # uploads log aFile
        # TODO: deal with big log files
        if self.logger_fh:
            self.logger_fh.flush()
            file_base64 = ""
            with open(self.logger_fh.baseFilename, "rb") as aFile:
                file_base64 = base64.b64encode(aFile.read())
            import_file.processing_logs = file_base64
            self.close_and_reset_logger()

        import_file.date_stop_processing = datetime.now()
        self.odooenv.cr.commit()
        return True

    # -------------------------------------------------------------------------------------
    def process_file(self, import_file, force=False):
        """
        Generic method to run all processing steps
        """
        if import_file:
            try:
                if import_file.does_file_need_processing(force):
                    self.create_dedicated_filelogger(
                        path.basename(import_file.filename)
                    )
                    if self.start_processing(import_file):
                        try:
                            result = self.process_data(import_file)
                            result = (result == None) or (result == True)
                            # reports result
                            if result:
                                if self.errorCount == 0:
                                    self.end_processing(
                                        import_file, success=result, status="ended"
                                    )
                                else:
                                    self.end_processing(
                                        import_file,
                                        success=result,
                                        status="error",
                                        any_message="%d error(s) raised during data processing"
                                        % self.errorCount,
                                    )
                            else:
                                self.end_processing(
                                    import_file,
                                    success=result,
                                    status="failure",
                                    any_message="Import Failed and %d error(s) raised during data processing"
                                    % self.errorCount,
                                )

                        except Exception as e:
                            self.odooenv.cr.rollback()
                            self.logger.exception(
                                "GOUFI: error while processing data (file %s) -> %s ",
                                toString(import_file.filename),
                                str(e),
                            )
                            self.end_processing(
                                import_file,
                                success=False,
                                status="failure",
                                any_message="Error: Generic Exception (%s)" % str(e),
                            )
                            self.odooenv.cr.commit()

                    else:
                        self.logger.error("Issue when initiliazing processing")
                        self.end_processing(
                            import_file,
                            success=False,
                            status="error",
                            any_message="Failed when initializing processing",
                        )
                        self.odooenv.cr.commit()
                    self.close_and_reset_logger()

            except Exception as e:
                self.odooenv.cr.rollback()
                if self.logger:
                    self.logger.exception(
                        "GOUFI: error while import file %s -> %s ",
                        toString(import_file.filename),
                        str(e),
                    )
                else:
                    logging.error(
                        "GOUFI: no logger set for processor: %s - (%s)",
                        str(self),
                        toString(import_file.filename),
                    )
                self.end_processing(
                    import_file,
                    success=False,
                    status="failure",
                    any_message="Error: Generic Exception (%s)" % str(e),
                )
                self.odooenv.cr.commit()
        else:
            self.logger.error("GOUFI: cannot import : no import_file provided !")
            logging.exception("GOUFI: cannot import : no import_file provided !")


# -------------------------------------------------------------------------------------
# LineIterator CLASS


class LineIteratorProcessor(AbstractProcessor):
    """
    A processor that must provide a generator to iterate on each line of the  file
    """

    def __init__(self, parent_config):
        AbstractProcessor.__init__(self, parent_config)

    # -------------------------------------------------------------------------------------
    # Process line values
    def process_values(self, line_index=-1, data_values=()):

        raise ValidationError("GOUFI: un-implemented generator method")

    # -------------------------------------------------------------------------------------
    # line generator
    def get_rows(self, import_file=None):

        raise ValidationError("GOUFI: un-implemented process_data method")

    # -------------------------------------------------------------------------------------
    # line generator
    def prepare_mappings(self, import_file=None):
        if import_file and import_file.import_config:
            if "_prepare_mapping_hook" in self.hooks:
                result = self.run_hooks(
                    "_prepare_mapping_hook",
                    colmappings=import_file.import_config.column_mappings,
                )
            else:
                self.logger.info(
                    "Default method does nothing: %s", import_file.filename
                )
                result = -1
        else:
            result = -1
        return result

    # -------------------------------------------------------------------------------------
    def process_data(self, import_file):
        """
        Method that actually process data
        Should return True on success and False on failure
        """

        if self.parent_config:
            if self.parent_config.target_object:
                self.target_model = self.odooenv[self.parent_config.target_object.model]
        if self.target_model == None:
            # Search for target model
            self.search_target_model_from_filename(import_file)
        if self.target_model == None:
            self.logger.exception(
                "Not able to guess target model: " + toString(import_file.filename)
            )
            return False

        idx = 0
        nb_mappings = self.prepare_mappings(import_file)
        if nb_mappings > 0:
            # Pre-process Rows Hook
            try:
                if "_pre_process_rows_hook" in self.hooks:
                    result = self.run_hooks("_pre_process_rows_hook", import_file)
                    if not result:
                        self.logger.error(
                            u"Failure during processing of _pre_process_rows_hook"
                        )
                        self.errorCount += 1
                        return False
            except Exception as e:
                self.odooenv.cr.rollback()
                self.logger.exception(
                    u" Error raised during _pre_process_rows_hook processing"
                )
                self.errorCount += 1
                return False

            # process Rows
            for row in self.get_rows(import_file):
                try:
                    result = self.run_hooks("_pre_conditions_hook", import_file, row[1])
                    if result:
                        self.process_values(row[0], row[1])
                except Exception as e:
                    self.logger.exception(u"Error when processing line N° %d", row[0])
                    self.errorCount += 1
                    self.odooenv.cr.rollback()
                    return -1
        elif nb_mappings < 0:
            self.logger.error(
                "Could not prepare mapping configuration for file: %s",
                import_file.filename,
            )
            self.errorCount += 1

        return self.errorCount == 0


# -------------------------------------------------------------------------------------
# MultiSheetLineIterator CLASS


class MultiSheetLineIterator(AbstractProcessor):
    """
    A processor that must provide a generator to iterate on each line of the  file
    """

    def __init__(self, parent_config):
        AbstractProcessor.__init__(self, parent_config)

    # -------------------------------------------------------------------------------------
    # tab generator
    # must return a tuple (tabname, Object)
    def get_tabs(self, import_file=None):

        raise ValidationError("GOUFI: un-implemented get_tabs method")

    # -------------------------------------------------------------------------------------
    # line generator
    # must return a tuble(index, Object)
    def get_rows(self, tab=None):

        raise ValidationError("GOUFI: un-implemented get_rows method")

    # -------------------------------------------------------------------------------------
    # Process tab header, in order to provide a list of columns to process
    # must return a list of column titles in header
    def process_tab_header(self, tab=None, headerrow=None):

        raise ValidationError("GOUFI: un-implemented generator method")

    # -------------------------------------------------------------------------------------
    # Provides a dictionary of values in a row
    def get_row_values_as_dict(self, tab=None, row=None, tabheader=None):

        raise ValidationError("GOUFI: un-implemented generator method")

    # -------------------------------------------------------------------------------------
    # Process line values
    def process_values(self, line_index=-1, data_values=()):

        raise ValidationError("GOUFI: un-implemented generator method")

    # -------------------------------------------------------------------------------------
    # prepare mappings configuration for tab processing,
    # must return an integer > 0 if successful and something to process
    #                         0 if nothing to do or ignore
    #                         -1 if failure
    def prepare_mappings_for_tab(self, import_file=None, tab=None):

        if import_file and tab:
            tab_name = tab[0]
            tabmap_model = self.odooenv["goufi.tab_mapping"]
            # Look for target Model in parent config
            parent_config = import_file.import_config
            if parent_config:
                if not parent_config.tab_support:
                    result = 1
                    if "_prepare_mapping_hook" in self.hooks:
                        result = self.run_hooks(
                            "_prepare_mapping_hook",
                            tab_name=tab_name,
                            colmappings=self.parent_config.column_mappings,
                        )
                    # OK: no tab support => i.e. single tab sometime
                    return result
                elif tab_name != None:
                    if parent_config.single_mapping:
                        found = tabmap_model.search(
                            [("parent_configuration", "=", parent_config.id)], limit=1
                        )
                    else:
                        found = tabmap_model.search(
                            [
                                ("parent_configuration", "=", parent_config.id),
                                ("name", "=", tab_name),
                            ],
                            limit=1,
                        )
                    if len(found) == 1:
                        current_tab = found[0]
                        try:
                            # Explicitly ignore
                            if found[0].ignore_tab:
                                self.logger.info(
                                    "Tab ignored by configuration: "
                                    + toString(tab_name)
                                )
                                return 0
                            self.target_model = self.odooenv[
                                current_tab.target_object.model
                            ]
                            self.header_line_idx = current_tab.default_header_line_index
                            if "_prepare_mapping_hook" in self.hooks:
                                result = self.run_hooks(
                                    "_prepare_mapping_hook",
                                    tab_name=current_tab.name,
                                    colmappings=current_tab.column_mappings,
                                )
                            else:
                                result = len(current_tab.column_mappings)

                        except:
                            self.logger.exception(
                                "Target model not found for " + toString(tab_name)
                            )
                            return -1
                    else:
                        self.logger.error(
                            "Tab configuration not found: " + toString(tab_name)
                        )
                        return -1
                else:
                    self.logger.error("No tab name given")
                    return -1
            else:
                self.logger.error("No configuration found for tab %s", tab_name)
                return -1
        else:
            self.logger.error(
                "No import_file or no Tab %s, %s", str(import_file), str(tab)
            )
            return -1

        return result

    # -------------------------------------------------------------------------------------
    def process_data(self, import_file):
        """
        Method that actually process data
        Should return True on success and False on failure
        """

        if self.parent_config:
            if self.parent_config.target_object:
                self.target_model = self.odooenv[self.parent_config.target_object.model]
        if self.target_model == None:
            # Search for target model
            self.search_target_model_from_filename(import_file)

        for tab in self.get_tabs(import_file):
            try:
                nb_mappings = self.prepare_mappings_for_tab(import_file, tab)
                if nb_mappings is not None and nb_mappings > 0:
                    idx = 0
                    header = None

                    # Pre-process Rows Hook
                    try:
                        if "_pre_process_rows_hook" in self.hooks:
                            result = self.run_hooks(
                                "_pre_process_rows_hook", import_file
                            )
                            if not result:
                                self.logger.error(
                                    u"Failure during processing of _pre_process_rows_hook"
                                )
                                self.errorCount += 1
                                return False
                    except Exception as e:
                        self.odooenv.cr.rollback()
                        self.logger.exception(
                            u" Error raised during _pre_process_rows_hook processing"
                        )
                        self.errorCount += 1
                        return False

                    # Process Rows
                    for row in self.get_rows(tab):

                        try:
                            if idx == self.header_line_idx:
                                # process header for tab
                                header = self.process_tab_header(tab, row)
                            elif idx > self.header_line_idx:
                                # process data for tab
                                if header != None and len(header) > 0:
                                    values = self.get_row_values_as_dict(
                                        tab=tab, row=row, tabheader=header
                                    )
                                else:
                                    self.logger.error(u"Header line is empty")
                                    self.errorCount += 1
                                    break
                                try:
                                    result = self.run_hooks(
                                        "_pre_conditions_hook", import_file, values
                                    )
                                    if result:
                                        self.process_values(idx, values)
                                except Exception as e:
                                    self.errorCount += 1
                                    self.logger.exception(
                                        u"Error when processing line N°%d in %s",
                                        idx + 1,
                                        tab[0],
                                    )
                            idx += 1
                        except Exception as e:
                            self.logger.exception(
                                u"Error when processing line N° %d of tab %s",
                                idx + 1,
                                tab[0],
                            )
                            self.errorCount += 1
                            self.odooenv.cr.rollback()
                            return False
                elif nb_mappings < 0:
                    self.logger.error(
                        "Could not prepare mapping configuration for Tab: %s", tab[0]
                    )
                    self.errorCount += 1
            except Exception as e:
                self.logger.exception(u"Error when processing a Tab:  %s", tab[0])
                self.errorCount += 1
                self.odooenv.cr.rollback()

        return self.errorCount == 0
