# -*- coding: utf-8 -*-

'''
Created on 23 deb. 2018

Utility functions to manipulate recordsets

@author: C. Guychard
@copyright: ©2018 Article 714
@license: AGPL v3
'''

import logging

from odoo import models, fields
from odoo.addons.goufi_base.utils.converters import toDate, dateToOdooString


#-------------------------------------------------------------------------------------
# compare a recordset with a dictionary of values to tell if record needs to be updated
# from dictionary
def does_need_update(values, recordset):
    result = False   
    target_fields = recordset.fields_get()
    for record in recordset:
        for key in values:
            field = target_fields[key]
            rec_val = getattr(record, key, None)
            logging.warning("COMPARING: %s ==  %s / %s", str(rec_val), str(values[key]), str(field['type']))
            # Value to compare depends on field type
            val = None
            if field['type'] == 'many2one':
                logging.warning("COMPARING Many2ONE: %s ==  %s / %s", str(rec_val.id), str(values[key]), str(field['type']))

                result = result or not (rec_val.id == values[key])
            elif  field['type'] == 'boolean':
                result = result or not (str(rec_val) == values[key])
            elif  field['type'] == 'date':
                try:
                    val = dateToOdooString(toDate(values[key]), force_date=True)
                    result = result or not (val == values[key])
                except:
                    result = True
                    break
            elif field['type'] == 'datetime':
                try:
                    val = dateToOdooString(toDate(values[key]))
                    result = result or not (val == values[key])
                except:
                    result = True
                    break
            elif field['type'] in('many2many', 'one2many'):
                # no way to check => true
                result = True
                break
            else:
                result = result or not (rec_val == values[key])
            # Comparing
            logging.warning("COMPARED: %s %s => %s", str(rec_val), str(values[key]), str(result))
            if result:
                break
    return result
