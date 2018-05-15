# -*- coding: utf-8 -*-
'''
Created on 23 feb. 2018

@author: C. Guychard
@copyright: ©2018 Article 714
@license: AGPL v3
'''

import logging

from odoo.addons.goufi_base.utils.converters import toString
from .expression_mappings import Processor

#-------------------------------------------------------------------------------------
# MAIN CLASS


class ColGroupProcessor(Processor):

    def __init__(self, parent_config):

        super(Processor, self).__init__(parent_config)

        self.column_groups = {}

    #-------------------------------------------------------------------------------------
    # Process mappings configuration for each tab

    def prepare_mappings(self, tab_name=None):

        super(ColGroupProcessor, self).prepare_mappings(tab_name=tab_name)

        # Column groups
        if val.member_of:
            if val.member_of.name not in self.column_groups:
                self.column_groups[val.member_of.name] = ()
            self.column_groups[val.member_of.name].append(val.name)

    #-------------------------------------------------------------------------------------
    # Process line values
    def process_values(self, filename, line_index, data_values):

        if len(self.column_groups) == 0:
            super(ColGroupProcessor, self).process_values(filename, line_index, data_values)
        else:
            # TODO ==> computation must be repeated for columns in column_groups

            for group in self.column_groups:
                print ("TODO")
