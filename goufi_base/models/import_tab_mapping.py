# -*- coding: utf-8 -*-
'''
Created on 23 deb. 2018

@author: C. Guychard
@copyright: ©2018 Article 714
@license: AGPL v3
'''

import logging

from odoo import models, fields, _, api


class TabMapping(models.Model):
    _name = 'goufi.tab_mapping'
    _description = u"Import File"
    _rec_name = "name"

    # Processor identification
    name = fields.Char(string = _(u'Name'), required = True, track_visibility = 'onchange')

    target_object = fields.Many2one(comodel_name = 'ir.model')

    parent_configuration = fields.Many2one(string = _(u"Parent configuration"),
                                      comodel_name = "goufi.import_configuration")

    column_mappings = fields.One2many(string = _(u"Column mappings"),
                                    help = _(u"Mapping configuration needed by this processor"),
                                      comodel_name = "goufi.column_mapping",
                                      inverse_name = "parent_tab")
