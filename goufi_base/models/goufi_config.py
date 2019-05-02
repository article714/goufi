# -*- coding: utf-8 -*-
"""
Created on march 2018

@author: C. Guychard
@copyright: ©2018 Article 714
@license: AGPL v3
"""

from odoo import api, fields, models, _


class GoufiConfigSettings(models.TransientModel):
    _name = "goufi.config.settings"
    _inherit = "res.config.settings"

    config_needs_partner = fields.Boolean(
        string=_(u"Provide partner to identify origin of imported data"),
        help=_(u"Do we need to provide partner to identify origin of imported data"),
        default=0,
    )

    delete_obsolete_files = fields.Boolean(
        string=_(u"Are obsolete (non-existant) files deleted?"),
        help=_(
            u"When this parameter is True, import_files are deleted, else, they are archived"
        ),
        default=False,
    )

    goufi_default_language = fields.Many2one(
        string=_(u"Default language"),
        help=_(u"Default language to be used for import"),
        comodel_name="res.lang",
    )

    @api.model
    def get_values(self):
        lang_model = self.env["res.lang"]
        res = super(GoufiConfigSettings, self).get_values()
        ICPSudo = self.env["ir.config_parameter"].sudo()
        strid = ICPSudo.get_param("goufi.goufi_default_language")
        id = 0
        value = False
        try:
            id = int(strid)
        except:
            value = False
        language = lang_model.browse(id)
        if language:
            value = language.id
        else:
            value = False
        res.update(
            config_needs_partner=ICPSudo.get_param("goufi.config_needs_partner"),
            delete_obsolete_files=ICPSudo.get_param("goufi.delete_obsolete_files"),
            goufi_default_language=value,
        )
        return res

    @api.multi
    def set_values(self):
        super(GoufiConfigSettings, self).set_values()
        ICPSudo = self.env["ir.config_parameter"].sudo()
        ICPSudo.set_param("goufi.config_needs_partner", self.config_needs_partner)
        ICPSudo.set_param("goufi.delete_obsolete_files", self.delete_obsolete_files)
        ICPSudo.set_param(
            "goufi.goufi_default_language", self.goufi_default_language.id
        )
