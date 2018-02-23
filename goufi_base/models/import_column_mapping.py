# -*- coding: utf-8 -*-
'''
Created on 23 deb. 2018

@author: C. Guychard
@copyright: ©2018 Article 714
@license: AGPL v3
'''

from odoo import models, fields, _, api

import logging


class ColumnMapping(models.Model):
    _name = 'goufi.column_mapping'
    _description = u"Import File"
    _rec_name = "name"

    # Processor identification
    name = fields.Char(string = _(u'Name'), required = True, track_visibility = 'onchange')

    targe_object = fields.Many2one(comodel_name = 'ir.model')
