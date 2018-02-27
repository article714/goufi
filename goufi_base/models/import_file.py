# -*- coding: utf-8 -*-
'''
Created on 23 deb. 2018

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

    filesize = fields.Float(string = _(u"File size"))

    partner_id = fields.Many2one(string = _(u'Related Partner'), comodel_name = 'res.partner', track_visibility = 'onchange')

    date_addition = fields.Datetime(string = _(u"Addition date"), track_visibility = 'onchange', required = True)

    date_updated = fields.Datetime(string = _(u"Last updated on"), track_visibility = 'onchange', required = True)

    # parametrage du traitement

    import_config = fields.Many2one(string = _(u'Related import configuration'), comodel_name = 'goufi.import_configuration', track_visibility = 'onchange')

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
    # file detection
    def process_file(self):
        for aFile in self:
            if aFile.import_config:
                cls = None
                mod = None
                if aFile.import_config.processor:
                    # Resolve processor class
                    try:
                        processor = aFile.import_config.processor
                        mod = importlib.import_module(processor.processor_module)
                        if mod:
                            cls = getattr(mod, processor.processor_class)
                        if cls == None:
                            logging.error("Goufi: Cannot process file, no processor class found " + aFile.filename)
                            return None
                    except Exception as e:
                        logging.error("Goufi: Cannot process file, error when evaluating processor module" + aFile.filename + "(" + str(e) + "-" + str(e.message) + ")")

                    # Process File
                    # TODO: one day provide a way to re-user processor instances?
                    if mod and cls:
                        proc_inst = cls(aFile.import_config)
                        proc_inst.process_file(self)
                else:
                    logging.error("Goufi: Cannot process file, no processor given " + aFile.filename)

            else:
                logging.error("Goufi: Cannot process file, no import config given " + aFile.filename)

    #-------------------------------
    # automation of file processing

    @api.model
    def process_files(self, criteria = []):

        import_file_model = self.env['goufi.import_file']

        if import_file_model != None :
            records = import_file_model.search(criteria, limit = None)
            for rec in records:
                rec.process_file()
