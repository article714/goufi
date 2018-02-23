# -*- coding: utf-8 -*-
# ©2017 - C. Guychard
# License: AGPL v3

from odoo import models, fields, _, api
import logging
import os
import re
import sys


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
                                 required = True
                                 )

    default_header_line_index = fields.Integer(string = _(u"Default Header line"), help = _(u"Fixes the index of the header line in import file"))

    #-------------------------------
    # file detection
    def _detect_files(self):
        if self.files_location:
            all_files = sorted(os.listdir(self.files_location))
            for aFile in all_files:
                cur_path = self.files_location + os.path.sep + aFile
                if re.match(self.filename_pattern, aFile):
                    logging.warning("Goufi: Would process " + cur_path)
                else:
                    logging.warning("Goufi: Would not process :" + cur_path)

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

