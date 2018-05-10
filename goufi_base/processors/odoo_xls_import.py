# -*- coding: utf-8 -*-
'''
Created on 9 may. 2018

Mainly inspired by odoo => addons.base_import

@author: C. Guychard
@copyright: ©2018 Article 714
@license: AGPL v3
'''


import datetime
from os import path
import re

from odoo import _
from odoo.addons.goufi_base.utils.converters import toString
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.misc import ustr

from .processor import AbstractProcessor


try:
    import xlrd
    try:
        from xlrd import xlsx
    except ImportError:
        xlsx = None
except ImportError:
    xlrd = xlsx = None


#-----------------------------------------------4--------------------------------------
# Global private variables
_reHeader = re.compile(r'[0-9]+\_')

#-----------------------------------------------4--------------------------------------
# MAIN CLASS


class OdooXLSProcessor(AbstractProcessor):
    """
    A processor that import csv files that are Odoo compatible (same as in modules source code

    Can use the following parameters:
        * csv_separator => define the seperator between fields

    """

    def __init__(self, parent_config):

        super(OdooXLSProcessor, self).__init__(parent_config)
        self.target_model = None


       


    #-------------------------------------------------------------------------------------
    def process_file(self, import_file, force=False):
        ext = import_file.filename.split('.')[-1]
        if (ext == 'xls'):
            super(OdooXLSProcessor, self).process_file(import_file, force)
        else:
            self.logger.error("Cannot process file: Wrong extension -> %s" % ext)
            self.end_processing(import_file, False)

                    
                    
    #-------------------------------------------------------------------------------------
    def process_data(self, import_file):
        """
        Method that actually process data
        """

        self.logger.info("Odoo xls data import: " + toString(import_file.filename))

        if self.target_model == None:

            self.logger.warning("No target model set on configuration, attempt to find it from file name")

            bname = path.basename(import_file.filename)
            modelname = '.'.join(bname.split('.')[:-1])

            if _reHeader.match(modelname):
                modelname = re.sub(r'[0-9]+\_', '', modelname)

            try:
                self.target_model = self.odooenv[modelname]
            except:
                self.target_model = None
                self.logger.exception("Not able to guess target model from filename: " + toString(import_file.filename))
                return False
            
            self.logger.warning("Found target model from file name: %s" % str(self.target_model))

        try:
            datas = []
            fields = None
            with xlrd.open_workbook(import_file.filename) as book:
                sh = book.sheet_by_index(0)
                
                # header
                fields = sh.row_values(0)
                        
                if not ('id' in fields):
                    self.logger.error("Import specification does not contain 'id', Cannot continue.")
                    return False
    
                # datas
                for rownum in range(1, sh.nrows):
                    row = sh.row(rownum)
                    # copied from base_import odoo source code
                    values = []
                    for cell in row:
                        if cell.ctype is xlrd.XL_CELL_NUMBER:
                            is_float = cell.value % 1 != 0.0
                            values.append(
                                unicode(cell.value)
                                if is_float
                                else unicode(int(cell.value))
                            )
                        elif cell.ctype is xlrd.XL_CELL_DATE:
                            is_datetime = cell.value % 1 != 0.0
                            # emulate xldate_as_datetime for pre-0.9.3
                            dt = datetime.datetime(*xlrd.xldate.xldate_as_tuple(cell.value, sh.book.datemode))
                            values.append(
                                dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                                if is_datetime
                                else dt.strftime(DEFAULT_SERVER_DATE_FORMAT)
                            )
                        elif cell.ctype is xlrd.XL_CELL_BOOLEAN:
                            values.append(u'True' if cell.value else u'False')
                        elif cell.ctype is xlrd.XL_CELL_ERROR:
                            raise ValueError(
                                _("Error cell found while reading XLS/XLSX file: %s") % 
                                xlrd.error_text_from_code.get(
                                    cell.value, "unknown error code %s" % cell.value)
                            )
                        else:
                            values.append(cell.value)
                    if any(x for x in values if x.strip()):
                        datas.append(values)

            result = self.target_model.load(fields, datas)
            if any(msg['type'] == 'error' for msg in result['messages']):
                # Report failed import and abort module install
                warning_msg = "\n".join(msg['message'] for msg in result['messages'])
                self.logger.error('Processing of file %s failed: %s' % (import_file.filename, warning_msg))
                import_file.processing_status = 'failure'
                import_file.processing_result = warning_msg
                return False

            return True

        except Exception as e:
            self.logger.exception("Processing Failed: " + str(e))
            self.odooenv.cr.rollback()
            import_file.processing_status = 'failure'
            import_file.processing_result = str(e)
            self.odooenv.cr.commit()
            return False
