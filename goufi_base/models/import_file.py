# -*- coding: utf-8 -*-
'''
Created on 23 feb. 2018

@author: C. Guychard
@copyright: ©2018 Article 714
@license: AGPL v3
'''

import importlib
import logging

from odoo import models, fields, _, api


class ImportFile(models.Model):
    _inherit = ['mail.thread']
    _name = 'goufi.import_file'
    _description = _(u"Import File")
    _rec_name = "filename"

    # File identification
    filename = fields.Char(string = _(u'File name'), required = True, track_visibility = 'onchange')

    filesize = fields.Float(string = _(u"File size"), default = 0.0)

    needs_partner = fields.Boolean (string = _(u"Does Goufi config needs partner"),
                                    help = _(u"This is configured for the whole goufi instance"),
                                    related = 'import_config.needs_partner',
                                    store = False,
                                    default = False)

    partner_id = fields.Many2one(string = _(u'Related Partner'),
                                         help = _("The partner that provided the Data"),
                                         comodel_name = 'res.partner', track_visibility = 'onchange')

    date_addition = fields.Datetime(string = _(u"Addition date"), track_visibility = 'onchange', required = True)

    date_updated = fields.Datetime(string = _(u"Last updated on"), track_visibility = 'onchange', required = True)

    # parametrage du traitement

    import_config = fields.Many2one(string = _(u'Related import configuration'), comodel_name = 'goufi.import_configuration',
                                     track_visibility = 'onchange', required = True)

    to_process = fields.Boolean(string = _(u"File is to be processed"), default = True, track_visibility = 'onchange')

    process_when_updated = fields.Boolean(string = _(u"File is to be re-processed when updated"), default = True, track_visibility = 'onchange')

    header_line_index = fields.Integer(string = _(u"Header line"), help = _(u"Fixes the index of the header line in import file"))

    # etat du traitement
    date_start_processing = fields.Datetime(string = _(u"Processing started on"), track_visibility = 'onchange')
    date_stop_processing = fields.Datetime(string = _(u"Processing ended on"), track_visibility = 'onchange')

    processing_status = fields.Selection([('new', 'new'),
                                (u'running', u'running'),
                                (u'ended', u'ended'),
                                (u'failure', u'failure')],
                                string = _(u"Processing status"), default = 'new', track_visibility = 'onchange')

    processing_result = fields.Text()

    processing_logs = fields.Binary(string = _(u'Processing logs'), prefetch = False, attachment = False)

    #-------------------------------
    # file processing

    def force_process_file(self):
        for aFile in self:
            aFile._process_a_file(force = True)

    def process_file(self):
        for aFile in self:
            aFile._process_a_file(force = False)

    def _process_a_file(self, force = False):
        if self.import_config:
            cls = None
            mod = None
            if self.import_config.processor:
                # Resolve processor class
                try:
                    processor = self.import_config.processor
                    mod = importlib.import_module(processor.processor_module)
                    if mod:
                        cls = getattr(mod, processor.processor_class)
                    if cls == None:
                        logging.error("GOUFI: Cannot process file, no processor class found " + self.filename)
                        return None
                except Exception as e:
                    logging.error("GOUFI: Cannot process file, error when evaluating processor module" + self.filename + "(" + str(e) + ")")

                # Process File
                # TODO: one day provide a way to re-use processor instances?
                if mod and cls:
                    proc_inst = cls(self.import_config)
                    proc_inst.process_file(self, force)
            else:
                logging.error("GOUFI: Cannot process file, no processor given " + self.filename)

        else:
            logging.error("GOUFI: Cannot process file, no import config given " + self.filename)

    #-------------------------------
    # automation of file processing

    @api.model
    def process_files(self, criteria = []):

        import_file_model = self.env['goufi.import_file']

        if import_file_model != None :
            records = import_file_model.search(criteria, limit = None)
            for rec in records:
                rec.process_file()

    #-------------------------------
    # standard model method override

    def create(self, values):
        if 'import_config' in values:
            config = self.env['goufi.import_configuration'].browse((values['import_config'],))
            if len(config) > 0:
                config = config[0]
                if config.partner_id:
                    values['default_partner_id'] = config.default_partner_id.id
                values['header_line_index'] = config.default_header_line_index

        return super(ImportFile, self).create(values)

    def write(self, values):
        if 'import_config' in values:
            config = self.env['goufi.import_configuration'].browse((values['import_config'],))
            if len(config) > 0:
                config = config[0]
                if config.partner_id:
                    values['default_partner_id'] = config.default_partner_id.id
        super(ImportFile, self).write(values)

