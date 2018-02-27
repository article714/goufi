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
    def process_data(self, import_file):
        """
        Method that actually process data
        """
        self.logger.info("DO NOTHING IMPORT; process DATA: " + toString(import_file.filename))
