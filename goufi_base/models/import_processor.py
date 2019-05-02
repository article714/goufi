# -*- coding: utf-8 -*-
"""
Created on 23 feb. 2018

@author: C. Guychard
@copyright: ©2018 Article 714
@license: AGPL v3
"""

from odoo import models, fields, _


class ImportProcessor(models.Model):
    _name = "goufi.import_processor"
    _description = _(u"Import Processor")
    _rec_name = "name"

    # Processor identification
    name = fields.Char(string=_(u"Name"), required=True)

    has_parameters = fields.Boolean(
        string=_(u"Has parameters"),
        help=_(u"Does this processor accepts parameters"),
        default=False,
    )

    needs_mappings = fields.Boolean(
        string=_(u"Needs mappings"),
        help=_(u"Does this processor needs column mappings"),
        default=False,
    )

    tab_support = fields.Boolean(
        string=_(u"Supports multi tabs"),
        help=_(u"Does the processor can process multiple tabs"),
        default=False,
    )

    col_group_support = fields.Boolean(
        string=_(u"Supports column groups"),
        help=_(u"Does the processor can process (iterable) group of columns"),
        default=False,
    )

    processor_module = fields.Char(
        string=_(u"Module containing Processor Class"), required=True
    )

    processor_class = fields.Char(string=_(u"Name of Processor Class"), required=True)
