# -*- coding: utf-8 -*-
# ©2017 - C. Guychard
# License: AGPL v3

from calendar import timegm
from datetime import date, datetime
from odoo import models, fields, _, api
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
import logging
import os
import re


#----
# utility functions
def toString(value):
    avalue = ""
    if isinstance(value, str):
        try:
            avalue = unicode(value)
        except UnicodeError:
            avalue = unicode(value.decode('iso-8859-1'))
    elif isinstance(value, unicode):
        avalue = value
    else:
        avalue = unicode("" + str(value))
    return avalue


def dateToOdooString(val):
    if isinstance(val, datetime):
        return val.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
    elif isinstance(val, date):
        return val.strftime(DEFAULT_SERVER_DATE_FORMAT)
    else:
        return toString(val)

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
                                 required = True
                                 )

    default_header_line_index = fields.Integer(string = _(u"Default Header line"), help = _(u"Fixes the index of the header line in import file"))

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
                                               'import_config': self.id
                                               })
                    else:
                        logging.error("Goufi: multiple import files found for :" + cur_path)

                    if iFile != None:
                        self.env.cr.commit()

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

