# -*- coding: utf-8 -*-
'''
Created on 23 february 2017

@author: C. Guychard
@copyright: ©2018 Article 714
@license: AGPL v3
'''

import logging

from odoo import models, fields, _, api


class ColumnGroup(models.Model):
    """
    A Column group is a way to define a set of mapping rules that will apply
    to several columns at the same time.
    Processors can support iteration over column groups also, in order to
    provide users with a way to easily import several instances of the same kind of data
    related to the same 'line'
    """
    _name = 'goufi.column_mapping_group'
    _description = _(u"Group of columns, used to defined advanced mapping")
    _rec_name = "name"

    # Column Group
    name = fields.Char(string=_(u'Columns Group name'),
                       help=_(u"Name of the group to map"),
                       required=True, track_visibility='onchange')


class ColumnMapping(models.Model):
    _name = 'goufi.column_mapping'
    _description = _(u"Mappings configuration for a given column")
    _rec_name = "name"
    _order = "sequence"

    # Column mapping
    # name of the column
    name = fields.Char(string=_(u'Column name'),
                       help=_(u"Name of the column to map"),
                       required=True, track_visibility='onchange')

    sequence = fields.Integer(string=_(u'Sequence'),
                              default=1, help=_(u"Used to order mappings. Lower is better."))

    # expression
    mapping_expression = fields.Char(string=_(u'Mapping Expression'),
                                     help=_(u"Expression used to process column content, meaning depends on chosen processor."),
                                     required=False, track_visibility='onchange')

    # is column part of a group

    member_of = fields.Many2one(string=_(u"Group"),
                                help=_(u"Set of columns this one belongs to"),
                                comodel_name='goufi.column_mapping_group',
                                required=False)

    col_group_support = fields.Boolean(string=_(u"Supports column groups"),
                                       help=_(u"Does the processor can process (iterable) group of columns"),
                                       related="parent_configuration.col_group_support",
                                       default=False, store=False)

    # is column part of identifier
    is_identifier = fields.Boolean(string=_(u"Is column part of identifiers?"),
                                   help=_(u"""The value of the mapping is used to find existing records in Odoo database.
If a record is found with given value in 'key field' (i.e. field given in expression), the record is updated with data.
If no record is found, a new one is created.

There can be several columns used as criteria
"""),
                                   default=False)

    is_mandatory = fields.Boolean(string=_(u"Mandatory column"),
                                  help=_(u"""There must be a value for this column"""),
                                  default=False)

    # is column a deletion marker
    is_deletion_marker = fields.Boolean(string=_(u"Does column contain a deletion marker?"),
                                        help=_(u"If True, the selected record (if found) will be deleted"),
                                        default=False)

    delete_if_expression = fields.Char(string=_(u"Delete if value matches"),
                                       help=_(
                                           u"Must contain a regular expression that the column value must match to be evaluated as True and the record be deleted"),
                                       required=False, default=_(u"Yes"), size=64)

    archive_if_not_deleted = fields.Boolean(string=_(u"Archive if not deleted?"),
                                            help=_(u"Should we archive record if deletion fail?"),
                                            default=False)

    # is column an archival marker
    is_archival_marker = fields.Boolean(string=_(u"Does column contain an archival marker?"),
                                        help=_(u"If True, the selected record (if found) will be archived"),
                                        default=False)

    archive_if_expression = fields.Char(string=_(u"Archive if value matches"),
                                        help=_(
                                            u"Must contain a regular expression that the column value must match to be evaluated as True and the record be archived"),
                                        required=False, default=_(u"Yes"), size=64)

    # is a constant expression

    is_constant_expression = fields.Boolean(string=_(u"Expression is a constant"),
                                            help=_(u"""The mapping expression is a string constant"""),
                                            default=False)

    # is a function call => value is set from the result of a function execution
    # function with prototype:
    # Function must return the value to be assigned to mapping or None

    is_function_call = fields.Boolean(string=_(u"Expression is a function to call"),
                                      help=_(u"""The value assigned to target property is the result of a function call.
Expression is the name of the function to call (must be a processor's method)
The function must have prototype: def aFunction(self,value)
Function must return the value to be assigned to mapping or None"""),
                                      default=False)

    # is a contextual expression mapping
    # (that is computed from processor properties, not from import file)

    is_contextual_expression_mapping = fields.Boolean(string=_(u"Is a contextual expression mapping "),
                                                      help=_(
                                                          u"If this mapping is a contextual expression, then it  is computed from processor properties, not from import file"),
                                                      default=False)

    # target object and target field (when relevant)
    target_object = fields.Many2one(string=_(u"Target object"),
                                    help=_(u"Odoo object that will be targeted by import: create, update or delete instances"),
                                    comodel_name="ir.model",
                                    required=False,
                                    compute='_get_target_object')

    def _get_target_field_dom(self):
        model_id = self._context.get('target_object')
        self._get_target_object()
        if model_id:
            return [('model_id', '=', model_id)]
        if self.target_object:
            return [('model_id', '=', self.target_object.id)]
        return []

    target_field = fields.Many2one(string=_(u"Target field"),
                                   help=_(u"Odoo object's field that will be targeted by import: create, update or delete instances"),
                                   comodel_name="ir.model.fields",
                                   required=False,
                                   domain=_get_target_field_dom)

    # Info about parent configuration and parent tab (if relevant)

    parent_configuration = fields.Many2one(string=_(u"Parent configuration"),
                                           comodel_name="goufi.import_configuration")

    tab_support = fields.Boolean(string=_(u"Supports multi tabs"),
                                 help=_(u"Does the selected parent configuration's pocessor can process multiple tabs"),
                                 related="parent_configuration.tab_support",
                                 store=False)

    parent_tab = fields.Many2one(string=_(u"Parent Tab (when multi tabs)"),
                                 comodel_name="goufi.tab_mapping")

    # computed field

    display_target = fields.Char(string=_(u"Target Field"), help=_(u"Target field for target object"),
                                 required=False,
                                 store=False,
                                 compute='_compute_display_target')

    # ******************************************************************************

    @api.depends('parent_configuration', 'parent_tab')
    def _get_target_object(self):
        for colMap in self:
            # update parent config if needed
            if colMap.parent_tab:
                if colMap.parent_configuration and colMap.parent_configuration != colMap.parent_tab.parent_configuration:
                    colMap.parent_configuration = colMap.parent_tab.parent_configuration
                else:
                    colMap.parent_configuration = colMap.parent_tab.parent_configuration

            if colMap.tab_support:
                if colMap.parent_tab:
                    colMap.target_object = colMap.parent_tab.target_object
            elif colMap.parent_configuration:
                colMap.target_object = colMap.parent_configuration.target_object

    @api.depends('target_object', 'target_field')
    def _compute_display_target(self):
        for colMap in self:
            if len(colMap.target_object) > 0:
                if len(colMap.target_field) > 0:
                    colMap.display_target = colMap.target_object.model + "." + colMap.target_field.name
                else:
                    colMap.display_target = colMap.target_object.model + ".?"
            else:
                colMap.display_target = _('None')

    @api.onchange('target_object')
    def _reset_colmap_targets(self):
        for aColMap in self:
            aColMap.target_field = None

    def fix_consistency(self, values):
        if 'is_deletion_marker' in values:
            if values['is_deletion_marker']:
                values['is_archival_marker'] = False
                values['is_identifier'] = False
                values['is_constant_expression'] = True
        if 'is_archival_marker' in values:
            if values['is_archival_marker']:
                values['is_deletion_marker'] = False
                values['is_identifier'] = False
                values['is_constant_expression'] = True
        if 'is_identifier' in values:
            if values['is_identifier']:
                values['is_mandatory'] = True
                values['is_deletion_marker'] = False
                values['is_archival_marker'] = False
                values['is_constant_expression'] = False

    @api.model
    def create(self, values):
        try:
            self.fix_consistency(values)
            if 'parent_tab' in values:
                if values['parent_tab'] != None:
                    found = self.env['goufi.tab_mapping'].search([('id', '=', values['parent_tab'])], limit=1)
                    if len(found) == 1:
                        values['parent_configuration'] = found[0].parent_configuration.id
        except Exception as e:
            logging.exception("Not able to check values when creating column mapping %s : %s" %
                              (type(e), unicode(e.message or e.name)))
        return super(ColumnMapping, self).create(values)

    def write(self, values):
        self.fix_consistency(values)
        if 'parent_tab' in values:
            if values['parent_tab'] != None:
                found = self.env['goufi.tab_mapping'].search([('id', '=', values['parent_tab'])], limit=1)
                if len(found) == 1:
                    values['parent_configuration'] = found[0].parent_configuration.id
        if 'target_object' in values:
            if self.target_object:
                if self.target_object != values['target_object']:
                    self.target_field = None
        super(ColumnMapping, self).write(values)
