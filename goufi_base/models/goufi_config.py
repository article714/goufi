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

    group_config_needs_partner = fields.Selection(
        [(0, "No partner on import configurations"),
        (1, 'Partners on import files and configurations')],
        string = _(u'Provide partner to identify origin of imported data'),
        help = _(u'Provide partner to identify origin of imported data'),
        implied_group = 'goufi_base.group_config_needs_partner',
        default = 0)
