# -*- coding: utf-8 -*-
'''
Created on 23 feb. 2018

@author: C. Guychard
@copyright: ©2018 Article 714
@license: AGPL v3
'''


from odoo import models, fields, _, api


class TabMapping(models.Model):
    _name = 'goufi.tab_mapping'
    _description = _(u"Mappings configuration for a tab")
    _rec_name = "name"
    _order = "sequence"

    # Tab Name
    name = fields.Char(string=_(u'Tab name'),
                       help=_(u"Name of the tab to process with this mapping"),
                       required=True, track_visibility='onchange')

    sequence = fields.Integer(string=_(u'Sequence'),
                              default=1, help=_(u"Used to order mappings. Lower is better."))

    target_object = fields.Many2one(string=_(u"Target object"),
                                    help=_(u"Odoo object that will be targeted by import: create, update or delete instances"),
                                    comodel_name="ir.model",
                                    required=True)

    default_header_line_index = fields.Integer(string=_(u"Default Header line"),
                                               help=_(
                                                   u"Provides the index of the header line in import file. Header line contains name of columns to be mapped."),
                                               required=True, default=0)

    parent_configuration = fields.Many2one(string=_(u"Parent configuration"),
                                           comodel_name="goufi.import_configuration")

    # Does the tab should be ignored

    ignore_tab = fields.Boolean(string=_(u"Ignore"),
                                help=_(u"Does the processor should explicitely ignore this tab"),
                                default=False)

    # Does the tab processing needs tab col_mappings
    needs_col_mappings = fields.Boolean(string=_(u"Needs column mappings"),
                                        help=_(u"Does the processor needs column mappings for this Tab"),
                                        default=True)

    column_mappings = fields.One2many(string=_(u"Column mappings"),
                                      help=_(u"Mapping configuration needed by this processor"),
                                      copy=True,
                                      comodel_name="goufi.column_mapping",
                                      inverse_name="parent_tab")

    # ******************************************************************************

    @api.onchange('target_object')
    def _reset_colmap_targets(self):
        for aTabMap in self:
            for colMap in aTabMap.column_mappings:
                colMap.target_field = None
                colMap.target_object = None

    @api.model
    def create(self, values):
        if 'parent_configuration' in values:
            if values['parent_configuration'] != None:
                found = self.env['goufi.import_configuration'].search(
                    [('id', '=', values['parent_configuration'])], limit=1)
                if len(found) == 1:
                    config = found[0]
                    if not 'default_header_line_index' in values:
                        values['default_header_line_index'] = config.default_header_line_index
                    if config.target_object:
                        values['target_object'] = config.target_object.id
        return super(TabMapping, self).create(values)
