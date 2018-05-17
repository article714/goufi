# -*- coding: utf-8 -*-
'''
Created on 17 may 2018

@author: C. Guychard
@copyright: ©2018 Article 714
@license: AGPL v3
'''

"""
a set of classes to be used in mixins for processor that provide support for importing XLS* files
"""

from odoo.addons.goufi_base.utils.converters import toString

from .processor import AbstractProcessor


#-------------------------------------------------------------------------------------
# CONSTANTS
XL_AUTHORIZED_EXTS = ('xlsx', 'xls')


class XLImporterMixin(AbstractProcessor):

    #-------------------------------------------------------------------------------------
    def process_file(self, import_file, force=False):
        ext = import_file.filename.split('.')[-1]
        if (ext in XL_AUTHORIZED_EXTS):
            super(XLImporterMixin, self).process_file(import_file, force)
        else:
            self.logger.error("Cannot process file: Wrong extension -> %s", ext)

    #-------------------------------------------------------------------------------------
    def process_data(self, import_file):
        """
        Method that actually process data
        """

        self.logger.info(" process XLS* file: " + toString(import_file.filename))
        try:

            if import_file.filename.endswith('.xls'):
                result = self.process_xls(import_file)
            elif import_file.filename.endswith('.xlsx'):
                result = self.process_xlsx(import_file)

            return result

        except Exception as e:
            self.logger.exception("Processing Failed: " + str(e))
            self.odooenv.cr.rollback()
            import_file.processing_status = 'failure'
            import_file.processing_result = str(e)
            self.odooenv.cr.commit()
            return False
