# -*- coding: utf-8 -*-
'''
Created on 03 may 2018

@author: C. Guychard
@copyright: ©2018 Article 714
@license: AGPL v3
'''

from odoo import models, fields, _


class ImportProcessorParameter(models.Model):
    _name = 'goufi.processor_parameter'
    _description = _(u"Import Processor Parameter")
    _rec_name = "name"

    # Processor identification
    name = fields.Char(string=_(u'Name'), required=True)

    value = fields.Char(string=_(u'Value'), required=True)

    # Info about parent configuration

    parent_configuration = fields.Many2one(string=_(u"Parent configuration"),
                                           comodel_name="goufi.import_configuration")
