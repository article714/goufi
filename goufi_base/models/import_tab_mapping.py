# -*- coding: utf-8 -*-
'''
Created on 23 feb. 2018

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
    _order = "sequence"

    # Tab Name
    name = fields.Char(string = _(u'Tab name'),
                       help = _(u"Name of the tab to process with this mapping"),
                       required = True, track_visibility = 'onchange')

    sequence = fields.Integer(string = _(u'Sequence'),
                              default = 1, help = _(u"Used to order mappings. Lower is better."))

    target_object = fields.Many2one(string = _(u"Target object"),
                                    help = _(u"Odoo object that will be targeted by import: create, update or delete instances"),
                                    comodel_name = "ir.model",
                                    required = True)

    default_header_line_index = fields.Integer(string = _(u"Default Header line"),
                                               help = _(u"Provides the index of the header line in import file. Header line contains name of columns to be mapped."),
                                               required = True, default = 0)

    parent_configuration = fields.Many2one(string = _(u"Parent configuration"),
                                      comodel_name = "goufi.import_configuration")

    column_mappings = fields.One2many(string = _(u"Column mappings"),
                                    help = _(u"Mapping configuration needed by this processor"),
                                      copy = True,
                                      comodel_name = "goufi.column_mapping",
                                      inverse_name = "parent_tab")

    # ******************************************************************************

    @api.onchange('target_object')
    def _reset_colmap_targets(self):
        for aTabMap in self:
            for colMap in  aTabMap.column_mappings:
                colMap.target_field = None
                colMap.target_object = None

    @api.multi
    def action_open_tabs_view(self):
        colmaps = self.mapped('self')
        action = self.env.ref('goufi_base.goufi_tab_mapping_show_action').read()[0]
        action['domain'] = [('parent_tab', 'in', colmaps.ids)]
        return action

