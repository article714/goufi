# -*- coding: utf-8 -*-
'''
Created on 23 deb. 2018

@author: C. Guychard
@copyright: ©2018 Article 714
@license: AGPL v3
'''

from calendar import timegm
from datetime import datetime
import logging
import os
import re

from odoo import models, fields, _, api
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

from odoo.addons.goufi_base.utils.converters import dateToOdooString


#------------------------------------------------------------
# main class
class ImportConfiguration(models.Model):
    _inherit = ['mail.thread']
    _name = 'goufi.import_configuration'
    _description = u"Import Configuration"
    _rec_name = "name"

    # Configuration identification
    name = fields.Char(string = _(u'Configuration name'), required = True, track_visibility = 'onchange')

    filename_pattern = fields.Char(_(u'File name pattern'),
                                      help = _(u""" The pattern that a file should respect to be detected as being processed by the current configuration """),
                                     required = True)

    files_location = fields.Char(string = _(u'Files Location'),
                                 help = _(u""" The place where we should try to find files that will be processed according to the current config
                                 """),
                                 required = True, default = "/odoo/file_imports"
                                 )

    default_header_line_index = fields.Integer(string = _(u"Default Header line"),
                                               help = _(u"Provides the index of the header line in import file. Header line contains name of columns to be mapped."),
                                               required = True, default = 0)

    processor = fields.Many2one(string = _(u"Import processor"),
                                comodel_name = 'goufi.import_processor',
                                required = True)

    needs_mappings = fields.Boolean(string = _(u"Needs mappings"),
                                    help = _(u"Does the selected processor needs column mappings"),
                                    related = "processor.needs_mappings",
                                    required = True, default = False)

    # Single Tab configuration => a single mapping and target object needed for config.

    target_object = fields.Many2one(string = _(u"Target object"),
                                    help = _(u"Odoo object that will be targeted by import: create, update or delete instances"),
                                    comodel_name = "ir.model",
                                    required = False)

    column_mappings = fields.One2many(string = _(u"Column mappings"),
                                    help = _(u"Mapping configuration needed by this processor"),
                                      comodel_name = "goufi.column_mapping",
                                      inverse_name = "parent_configuration",
                                      required = False)

    # Multi-Tab configuration => several mappings and targets object needed for config.
    #   there will be a target object per tab-mapping

    tab_support = fields.Boolean(string = _(u"Supports multi tabs"),
                                    help = _(u"Does the selected processor can process multiple tabs"),
                                    related = "processor.tab_support",
                                    required = True, default = False)

    tab_mappings = fields.One2many(string = _(u"Tab mappings"),
                                    help = _(u"Mapping configuration needed by this processor"),
                                      comodel_name = "goufi.tab_mapping",
                                      inverse_name = "parent_configuration",
                                      required = False)

    #-------------------------------
    #-------------------------------
    # file detection
    def _detect_files(self):
        file_model = self.env['goufi.import_file']
        if self.files_location and file_model != None:
            all_files = sorted(os.listdir(self.files_location))
            for aFile in all_files:
                cur_path = self.files_location + os.path.sep + aFile

                if re.match(self.filename_pattern, aFile):
                    filesize = os.path.getsize(cur_path)
                    str_date = dateToOdooString(datetime.now())

                    existing_found = file_model.search([('filename', '=', cur_path)])
                    nb_found = len(existing_found)

                    if nb_found == 1:
                        iFile = existing_found[0]
                        modtime = os.path.getmtime(cur_path)

                        if modtime > timegm(datetime.strptime(iFile.date_updated, DEFAULT_SERVER_DATETIME_FORMAT).timetuple()):
                            iFile.write({'date_updated':str_date})

                    elif nb_found == 0:
                        iFile = file_model.create({'filename':cur_path,
                                               'date_addition':str_date,
                                               'date_updated':str_date,
                                               'filesize':filesize,
                                               'import_config': self.id,
                                               'header_line_index':self.default_header_line_index
                                               })
                    else:
                        logging.error("Goufi: multiple import files found for :" + cur_path)

                    if iFile != None:
                        self.env.cr.commit()
        else:
            logging.error ("GOUFI: No files location for configuration " + self.name)

    #-------------------------------
    # automation of file detection
    @api.model
    def detect(self, criteria = []):
        """
        Detects files that can be processed using some import configuration

        criteria: can be used to define a domain for filtering configuration to use
        """
        config_model = self.env['goufi.import_configuration']

        if config_model != None :
            records = config_model.search(criteria, limit = None)
            for rec in records:
                rec._detect_files()

