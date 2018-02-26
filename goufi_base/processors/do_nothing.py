# -*- coding: utf-8 -*-
'''
Created on 23 feb. 2018

@author: C. Guychard
@copyright: ©2018 Article 714
@license: AGPL v3
'''

import logging

from odoo.addons.goufi_base.utils.converters  import toString
from .processor import AbstractProcessor

#-------------------------------------------------------------------------------------
# MAIN CLASS


class Processor(AbstractProcessor):

    #-------------------------------------------------------------------------------------
    def process_file(self, import_file):
        self.create_dedicated_filelogger(import_file.filename)
        self.logger.info("GOUFI ==> DO NOTHING IMPORT; process: " + toString(import_file.filename))
        self.close_and_reset_logger()
        return True

