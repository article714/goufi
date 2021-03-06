# -*- coding: utf-8 -*-
'''
Created on 23 february 2018

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
    _description = _(u"Import Configuration")
    _rec_name = "name"

    active = fields.Boolean('Active', default=True,
                            help="If unchecked, it will allow you to hide the configuration without removing it.")

    # Configuration identification
    name = fields.Char(string=_(u'Configuration name'), required=True, track_visibility='onchange')

    description = fields.Char(string=_(u'Description'), required=False, size=256)

    filename_pattern = fields.Char(_(u'File name pattern'),
                                   help=_(
                                       u""" The pattern that a file should respect to be detected as being processed by the current configuration """),
                                   required=True)

    files_location = fields.Char(string=_(u'Files Location'),
                                 help=_(u""" The place where we should try to find files that will be processed according to the current config
                                 """),
                                 required=True, default="/odoo/file_imports"
                                 )

    recursive_search = fields.Boolean(string=_(u"Recursive search"),
                                      help=_(u"should we search for files in sub-directories"),
                                      default=False)

    working_dir = fields.Char(string=_(u'Working directory'),
                              help=_(u" Directory where temp and log files will be put"),
                              required=True, default="/odoo/file_imports/_work"
                              )

    default_header_line_index = fields.Integer(string=u"Default Header line",
                                               help=u"Provides the index of the header line in \
                                                       import file. Header line contains name of \
                                                           columns to be mapped.",
                                               required=True, default=1)

    default_partner_id = fields.Many2one(string=_(u'Related Partner'),
                                         help=_("The partner that provided the Data"),
                                         comodel_name='res.partner', track_visibility='onchange')

    needs_partner = fields.Boolean(string=_(u"Needs partner"),
                                   help=_(u"Does the selected configuration needs a partner reference"),
                                   compute="_get_param_needs_partner",
                                   read_only=True, store=False)

    processor = fields.Many2one(string=_(u"Import processor"),
                                comodel_name='goufi.import_processor',
                                required=True)

    needs_mappings = fields.Boolean(string=_(u"Needs mappings"),
                                    help=_(u"Does the selected processor need \
                                        column/tab mappings"),
                                    related="processor.needs_mappings")


    has_parameters = fields.Boolean(string=_(u"Has parameters"),
                                    help=_(u"Does the selected processor accept \
                                        parameters"),
                                    related="processor.has_parameters",
                                    read_only=True)

    # Languate configuration

    @api.multi
    def _get_default_language(self):
        lang_model = self.env['res.lang']
        strid = self.env['ir.config_parameter'].sudo().get_param('goufi.goufi_default_language')
        id = 0
        try:
            id = int(strid)
        except:
            return False
        language = lang_model.browse(id)
        if language:
            return language
        else:
            return False

    context_language = fields.Many2one(
        string=_(u'Language to use'),
        help=_(u'Language to be used for import'),
        comodel_name='res.lang',
        default=_get_default_language)

    # Parameters when needed

    processor_parameters = fields.One2many(string=_(u"Processor parameters"),
                                           help=_(u"Parameters that will be passed to processor"),
                                           comodel_name="goufi.processor_parameter",
                                           inverse_name="parent_configuration",
                                           required=False)

    # Single Tab configuration => a single mapping and target object needed for config.

    target_object = fields.Many2one(string=_(u"Target object"),
                                    help=_(u"Odoo object that will be targeted by import: create, update or delete instances"),
                                    comodel_name="ir.model",
                                    required=False)

    column_mappings = fields.One2many(string=_(u"Column mappings"),
                                      help=_(u"Mapping configuration needed by this processor"),
                                      comodel_name="goufi.column_mapping",
                                      inverse_name="parent_configuration",
                                      required=False)

    col_group_support = fields.Boolean(string=_(u"Supports column groups"),
                                       help=_(u"Does the processor can process (iterable) group of columns"),
                                       related="processor.col_group_support",
                                       read_only=True)

    # Multi-Tab configuration => several mappings and targets object needed for config.
    #   there will be a target object per tab-mapping

    tab_support = fields.Boolean(string=_(u"Supports multi tabs"),
                                 help=_(u"Does the selected processor can process multiple tabs"),
                                 related="processor.tab_support",
                                 read_only=True)

    single_mapping = fields.Boolean(string=_(u"Single mapping for all tabs"),
                                    help=_(u"Does the selected processor use \
                                        the same mappings for all tabs"),
                                    related="processor.needs_mappings")

    tab_mappings = fields.One2many(string=_(u"Tab mappings"),
                                   help=_(u"Mapping configuration needed by this processor"),
                                   comodel_name="goufi.tab_mapping",
                                   inverse_name="parent_configuration",
                                   required=False)

    #-------------------------------
    @api.multi
    @api.depends('processor', 'name', 'active', 'default_partner_id')
    def _get_param_needs_partner(self):
        needs_partner_val = self.env['ir.config_parameter'].get_param('goufi.config_needs_partner')
        needs_partner = True if needs_partner_val == 'True' else False
        for obj in self:
            obj.needs_partner = needs_partner

    @api.multi
    def action_open_tabs_view(self):
        action = self.env.ref('goufi_base.goufi_tab_mapping_show_action').read()[0]
        action['domain'] = [('parent_configuration', '=', self.id)]
        return action

    #-------------------------------
    # file detection

    def detect_files(self, cr=None, uid=None, context=None, cur_dir=None):
        self.ensure_one()

        file_model = self.env['goufi.import_file']
        delete_files_val = self.env['ir.config_parameter'].get_param('goufi.delete_obsolete_files')
        delete_files = True if delete_files_val == 'True' else False
        all_files = []

        # detection of obsolete files
        all_existing_files = file_model.search([('import_config', '=', self.id)])
        for aFile in all_existing_files:
            try:
                if not os.path.exists(aFile.filename):
                    if delete_files:
                        aFile.unlink()
                        self.env.cr.commit()
                    else:
                        aFile.active = False
                        self.env.cr.commit()
            except:
                logging.exception(u"Goufi failed to archive/delete import_file:%s" % aFile.filename)

        # detection of new or updated files
        if cur_dir != None:
            all_files = sorted(os.listdir(cur_dir))
        elif self.files_location and file_model != None:
            all_files = sorted(os.listdir(self.files_location))
        else:
            logging.error("GOUFI: No files location for configuration " + self.name)
            return None

        for aFile in all_files:
            if cur_dir != None:
                cur_path = cur_dir + os.path.sep + aFile
            else:
                cur_path = self.files_location + os.path.sep + aFile

            if os.path.isdir(cur_path):
                if self.recursive_search:
                    self.detect_files(cr, uid, context, cur_dir=cur_path)
            elif os.path.isfile(cur_path):
                if re.match(self.filename_pattern, aFile):
                    filesize = os.path.getsize(cur_path)
                    str_date = dateToOdooString(datetime.now())

                    existing_found = file_model.search([('filename', '=', cur_path), ('import_config', '=', self.id)])
                    nb_found = len(existing_found)

                    if nb_found == 1:
                        iFile = existing_found[0]
                        modtime = os.path.getmtime(cur_path)

                        if modtime > timegm(datetime.strptime(iFile.date_updated, DEFAULT_SERVER_DATETIME_FORMAT).timetuple()):
                            iFile.write({'date_updated': str_date,
                                         'filesize': filesize})

                    elif nb_found == 0:
                        iFile = file_model.create({'filename': cur_path,
                                                   'date_addition': str_date,
                                                   'date_updated': str_date,
                                                   'filesize': filesize,
                                                   'import_config': self.id,
                                                   'header_line_index': self.default_header_line_index
                                                   })
                    else:
                        logging.error("GOUFI: multiple import files found for :" + cur_path)

                    if iFile != None:
                        self.env.cr.commit()

    #-------------------------------
    # automation of file detection
    @api.model
    def detect(self, criteria=[]):
        """
        Detects files that can be processed using some import configuration

        criteria: can be used to define a domain for filtering configuration to use
        """
        config_model = self.env['goufi.import_configuration']

        if config_model != None:
            records = config_model.search(criteria, limit=None)
            for rec in records:
                rec.detect_files(cur_dir=None)
