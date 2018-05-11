# -*- coding: utf-8 -*-
'''
Created on march 2018

@author: C. Guychard
@copyright: ©2018 Article 714
@license: AGPL v3
'''

from odoo import api, fields, models, _

PARAMS = [
    ("config_needs_partner", "goufi.config_needs_partner"),
    ("delete_obsolete_files", "goufi.delete_obsolete_files"),
]


class GoufiConfigSettings(models.TransientModel):
    _name = 'goufi.config.settings'
    _inherit = 'res.config.settings'

    config_needs_partner = fields.Boolean(
        string=_(u'Provide partner to identify origin of imported data'),
        help=_(u'Do we need to provide partner to identify origin of imported data'),
        default=0)

    delete_obsolete_files = fields.Boolean(
        string=_(u'Are obsolete (non-existant) files deleted?'),
        help=_(u'When this parameter is True, import_files are deleted, else, they are archived'),
        default=False)

    @api.multi
    def set_config_needs_partner(self):
        return self.env['ir.values'].sudo().set_default(
            'goufi.config.settings', 'config_needs_partner', self.config_needs_partner)

    @api.multi
    def set_delete_obsolete_files(self):
        return self.env['ir.values'].sudo().set_default(
            'goufi.config.settings', 'delete_obsolete_files', self.delete_obsolete_files)

    @api.model
    def get_default_config_needs_partner(self, fields):
        default_val = self.env['ir.values'].get_default('goufi.config.settings', 'config_needs_partner')
        return {
            'config_needs_partner': 1 if default_val == 'True' else False,
        }

    @api.model
    def get_default_delete_obsolete_files(self, fields):
        default_val = self.env['ir.values'].get_default('goufi.config.settings', 'delete_obsolete_files')
        return {
            'delete_obsolete_files': 1 if default_val == 'True' else False,
        }
