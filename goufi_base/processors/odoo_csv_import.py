# -*- coding: utf-8 -*-
'''
Created on 3 mai 2018

@author: C. Guychard
@copyright: ©2018 Article 714
@license: AGPL v3
'''


from os import path
import re
import unicodecsv

from odoo import _
from odoo.tools.misc import ustr

from odoo.addons.goufi_base.utils.converters import toString

from .processor import AbstractProcessor


#-----------------------------------------------4--------------------------------------
# MAIN CLASS
class OdooCSVProcessor(AbstractProcessor):
    """
    A processor that import csv files that are Odoo compatible (same as in modules source code
    """

    def __init__(self, parent_config):

        super(OdooCSVProcessor, self).__init__(parent_config)
        self.target_model = None

    #-------------------------------------------------------------------------------------
    def process_file(self, import_file, force=False):
        ext = import_file.filename.split('.')[-1]
        if (ext == 'csv'):
            super(OdooCSVProcessor, self).process_file(import_file, force)
        else:
            self.logger.error("Cannot process file: Wrong extension -> %s" % ext)
            self.end_processing(import_file, False)

    #-------------------------------------------------------------------------------------
    def process_data(self, import_file):
        """
        Method that actually process data
        """

        self.logger.info("Odoo csv data import: " + toString(import_file.filename))

        if self.target_model == None:

            self.logger.warning("No target model set on configuration, attempt to find it from file name")

            bname = path.basename(import_file.filename)
            (modelname, ext) = bname.split('.')

            modelname = modelname.replace('_', '.')
            if re.match(r'[0-9]+\.', modelname):
                modelname = re.sub(r'[0-9]+\.', '', modelname)

            try:
                self.target_model = self.odooenv[modelname]
            except:
                self.target_model = None
                self.logger.exception("Not able to guess target model from filename: " + toString(import_file.filename))
                return False

        try:
            with open(import_file.filename, 'rb', encoding='utf-8') as csvfile:
                reader = unicodecsv.reader(csvfile, quotechar='"', delimiter=',')
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
                    self.logger.error('Processing of file %s failed: %s' % (import_file.filename,  warning_msg))
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
