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
    _description = _(u"Mappings configuration for a tab")
    _rec_name = "name"

    # Tab Name
    name = fields.Char(string = _(u'Tab name'),
                       help = _(u"Name of the tab to process with this mapping"),
                       required = True, track_visibility = 'onchange')

    sequence = fields.Integer(string = _(u'Sequence'),
                              default = 1, help = _(u"Used to order mappings. Lower is better."))

    target_object = fields.Many2one(string = _(u"Target object"),
                                    help = _(u"Odoo object that will be targeted by import: create, update or delete instances"),
                                    comodel_name = "ir.model",
                                    required = False)

    default_header_line_index = fields.Integer(string = _(u"Default Header line"),
                                               help = _(u"Provides the index of the header line in import file. Header line contains name of columns to be mapped."),
                                               required = True, default = 0)

    parent_configuration = fields.Many2one(string = _(u"Parent configuration"),
                                      comodel_name = "goufi.import_configuration")

    column_mappings = fields.One2many(string = _(u"Column mappings"),
                                    help = _(u"Mapping configuration needed by this processor"),
                                      comodel_name = "goufi.column_mapping",
                                      inverse_name = "parent_tab")

