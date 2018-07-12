# -*- coding: utf-8 -*-

'''
Created on 23 deb. 2018

Utility functions to manipulate recordsets

@author: C. Guychard
@copyright: ©2018 Article 714
@license: AGPL v3
'''

#-------------------------------------------------------------------------------------
# compare a recordset with a dictionary of values to tell if record needs to be updated
# from dictionary


def does_need_update(values, recordset):
    result = False
    for record in recordset:
        for key in values:
            rec_val = getattr(record, key, None)
            result = result or (rec_val != values[key])
    return result
