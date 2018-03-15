# -*- coding: utf-8 -*-
'''
Created on march 2018

@author: C. Guychard
@copyright: ©2018 Article 714
@license: AGPL v3
'''

from odoo import api, fields, models, _


class GoufiConfig(models.TransientModel):
    _name = 'goufi.config.settings'
    _inherit = 'res.config.settings'

    config_needs_partner = fields.Boolean(
        _(u'Provide partner to identify origin of imported data'),
        help = _(u'Provide partner to identify origin of imported data'))

