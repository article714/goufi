# -*- coding: utf-8 -*-
'''
Created on march 2018

@author: C. Guychard
@copyright: ©2018 Article 714
@license: AGPL v3
'''

from odoo import api, fields, models, _


class GoufiConfigSettings(models.TransientModel):
    _name = 'goufi.config.settings'
    _inherit = 'res.config.settings'

    config_needs_partner = fields.Boolean(
        string=_(u'Provide partner to identify origin of imported data'),
        help=_(u'Do we need to provide partner to identify origin of imported data'))

    delete_obsolete_files = fields.Boolean(
        string=_(u'Are obsolete (non-existant) files deleted?'),
        help=_(u'When this parameter is True, import_files are deleted, else, they are archived'))

    goufi_default_language = fields.Many2one(
        string=_(u'Default language'),
        help=_(u'Default language to be used for import'),
        comodel_name='res.lang')

    @api.multi
    def set_config_needs_partner(self):
        return self.env['ir.config_parameter'].sudo().set_param(
            'goufi.config_needs_partner', self.config_needs_partner)

    @api.multi
    def set_delete_obsolete_files(self):
        return self.env['ir.config_parameter'].sudo().set_param(
            'goufi.delete_obsolete_files', self.delete_obsolete_files)

    @api.multi
    def set_goufi_default_language(self):
        return self.env['ir.config_parameter'].sudo().set_param(
            'goufi.goufi_default_language', self.goufi_default_language.id)

    @api.model
    def get_default_config_needs_partner(self, fields):
        return {'config_needs_partner': True if self.env['ir.config_parameter'].sudo().get_param('goufi.config_needs_partner') == 'True' else False}

    @api.model
    def get_default_obsolete_files(self, fields):
        return {'delete_obsolete_files': True if self.env['ir.config_parameter'].sudo().get_param('goufi.delete_obsolete_files') == 'True' else False}

    @api.multi
    def get_default_goufi_default_language(self, fields):
        lang_model = self.env['res.lang']
        strid = self.env['ir.config_parameter'].sudo().get_param('goufi.goufi_default_language')
        id = 0
        try:
            id = int(strid)
        except:
            return {'goufi_default_language': False}
        language = lang_model.browse(id)
        if language:
            return {'goufi_default_language': language.id}
        else:
            return {'goufi_default_language': False}
