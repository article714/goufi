# -*- coding: utf-8 -*-

'''
Created on 23 deb. 2018

Utility functions to manipulate recordsets

@author: C. Guychard
@copyright: ©2018 Article 714
@license: AGPL v3
'''


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
            # Value to compare depends on field type
            val = None
            if field['type'] == 'many2one':
                result = result or not (rec_val.id == values[key])
            elif field['type'] == 'boolean':
                result = result or not (str(rec_val) == values[key])
            elif field['type'] == 'date':
                try:
                    val = dateToOdooString(toDate(values[key]), force_date=True)
                    result = result or not (val == rec_val)
                except:
                    result = True
                    break
            elif field['type'] == 'datetime':
                try:
                    val = dateToOdooString(toDate(values[key]))
                    result = result or not (val == rec_val)
                except:
                    result = True
                    break
            elif field['type'] in('many2many', 'one2many'):
                # no way to check => true
                result = True
                break
            elif field['type'] == 'char':

                val = values[key]

                if not isinstance(val, unicode):
                    try:
                        result = result or not (rec_val == unicode(val))
                    except:
                        result = True
                else:
                    result = result or not (rec_val == val)

            else:
                result = result or not (rec_val == values[key])
            # Comparing
            if result:
                break
    return result
