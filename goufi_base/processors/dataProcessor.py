# -*- coding: utf-8 -*-
'''
Created on 23 feb. 2018

@author: C. Guychard
@copyright: ©2018 Article 714
@license: AGPL v3
'''

from openpyxl.cell.read_only import EmptyCell
from openpyxl.reader.excel import load_workbook
import configparser
import os
import re
import unicodecsv
import xlrd

from odoo.addons.goufi_base.utils.converters  import toString

#-------------------------------------------------------------------------------------
# CONSTANTS
AUTHORIZED_EXTS = ('xlsx', 'xls', 'csv')

#-------------------------------------------------------------------------------------
# MAIN CLASS


class DataProcessor():

    #-------------------------------------------------------------------------------------
    # process a linee of data

    def map_values(self, row):
        for f in row:
            if row[f] == "False" or row[f] == "True":
                row[f] = eval(row[f])
            elif row[f] == None:
                del(row[f])
        return row

