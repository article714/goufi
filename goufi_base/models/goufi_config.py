# -*- coding: utf-8 -*-
'''
Created on march 2018

@author: C. Guychard
@copyright: ©2018 Article 714
@license: AGPL v3
'''

from odoo import api, fields, models, _

PARAMS = [
    ("group_config_needs_partner", "goufi.group_config_needs_partner"),
    ("delete_obsolete_files", "goufi.delete_obsolete_files"),
]


class GoufiConfigSettings(models.TransientModel):
    _name = 'goufi.config.settings'
    _inherit = 'res.config.settings'

    group_config_needs_partner = fields.Boolean(
        string=_(u'Provide partner to identify origin of imported data'),
        help=_(u'Do we need to provide partner to identify origin of imported data'),
        default=0)


    delete_obsolete_files = fields.Boolean(
        string=_(u'Are obsolete (non-existant) files deleted?'),
        help=_(u'When this parameter is True, import_files are deleted, else, they are archived'),
        default=False)


    @api.one
    def set_params(self):
        for field_name, key_name in PARAMS:
            obj = getattr(self, field_name, '')
            value = None
            if isinstance(self[field_name], models.Model):
                value = obj.id
            elif isinstance(self[field_name], fields.Selection):
                if obj:
                    value = obj
                else:
                    value = 0 
            elif isinstance(obj, str):
                value = obj.strip()
            elif isinstance(obj, unicode):
                value = obj.strip()
            else:
                value = str(obj).strip()

            self.env['ir.config_parameter'].set_param(key_name, value)

    def get_default_params(self, context=None):
        res = {}
        for field_name, key_name in PARAMS:
            param_value = self.env['ir.config_parameter'].get_param(key_name, '')
            if isinstance(self[field_name], models.Model):
                if param_value != None and param_value != '':
                    val = self[field_name].search([('id', '=', param_value)])
                    res[field_name] = val.id
            elif isinstance(self[field_name], fields.Selection):
                    if param_value:
                        res[field_name] = int(param_value)
                    else:
                        res[field_name] = 0
            elif isinstance(self[field_name], fields.Boolean):
                    res[field_name] = True if param_value == 'True' else False
            else:
                res[field_name] = param_value.strip()
        return res

