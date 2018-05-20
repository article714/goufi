# -*- coding: utf-8 -*-
'''
Created on 23 feb. 2018

@author: C. Guychard
@copyright: ©2018 Article 714
@license: AGPL v3
'''


#-------------------------------------------------------------------------------------
# MAIN CLASS


class ColGroupMixin(object):

    def __init__(self, parent_config):
        self.register_hook('_prepare_mapping_hook', ColGroupMixin.prepare_mapping_hook)
        self.register_hook('_process_values_hook', ColGroupMixin.process_values_hook)
        self.column_groups = {}

    #-------------------------------------------------------------------------------------
    # Process mappings configuration for each tab

    def prepare_mapping_hook(self, tab_name="Unknown", colmappings=None):

        for val in colmappings:
            # Column groups
            if val.member_of:
                if val.member_of.name not in self.column_groups:
                    self.column_groups[val.member_of.name] = []
                self.column_groups[val.member_of.name].append(val.name)

        return 1

    #-------------------------------------------------------------------------------------
    # Process mappings configuration for each tab

    def process_values_hook(self):
        print ("TODO TODO")
