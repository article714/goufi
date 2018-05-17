# -*- coding: utf-8 -*-
'''
Created on 23 feb. 2018

@author: C. Guychard
@copyright: ©2018 Article 714
@license: AGPL v3
'''

from calendar import timegm
from datetime import datetime
from os import path
import importlib
import logging

from odoo import models, fields, _, api
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class ImportFile(models.Model):
    _inherit = ['mail.thread']
    _name = 'goufi.import_file'
    _description = _(u"Import File")
    _rec_name = "filename"
    _order = "filename"

    active = fields.Boolean('Active', default=True,
                            help="If unchecked, it will allow you to hide the file without removing it.")

    # File identification
    filename = fields.Char(string=_(u'File name'), required=True, track_visibility='onchange')

    filesize = fields.Float(string=_(u"File size"), default=0.0)

    partner_id = fields.Many2one(string=_(u'Related Partner'),
                                 help=_("The partner that provided the Data"),
                                 comodel_name='res.partner', track_visibility='onchange')

    needs_partner = fields.Boolean(string=_(u"Needs partner"),
                                   help=_(u"Does the selected configuration needs a partner reference"),
                                   related="import_config.needs_partner",
                                   read_only=True, store=False)

    date_addition = fields.Datetime(string=_(u"Addition date"), track_visibility='onchange', required=True)

    date_updated = fields.Datetime(string=_(u"Last updated on"), track_visibility='onchange', required=True)

    # parametrage du traitement

    import_config = fields.Many2one(string=_(u'Related import configuration'), comodel_name='goufi.import_configuration',
                                    track_visibility='onchange', required=True)

    to_process = fields.Boolean(string=_(u"File is to be processed"), default=True, track_visibility='onchange')

    needs_to_be_processed = fields.Boolean(string=_(u"File needs to be processed"),
                                           compute='_file_needs_processing', store=True)

    process_when_updated = fields.Boolean(
        string=_(u"File is to be re-processed when updated"), default=True, track_visibility='onchange')

    header_line_index = fields.Integer(string=_(u"Header line"), help=_(
        u"Fixes the index of the header line in import file"))

    # etat du traitement
    date_start_processing = fields.Datetime(string=_(u"Processing started on"), track_visibility='onchange')
    date_stop_processing = fields.Datetime(string=_(u"Processing ended on"), track_visibility='onchange')

    processing_status = fields.Selection([('new', 'new'),
                                          (u'running', u'running'),
                                          (u'ended', u'ended'),
                                          (u'error', u'ended with errors'),
                                          (u'pending', u'pending'),
                                          (u'failure', u'failure')],
                                         string=_(u"Processing status"), default='new', track_visibility='onchange')

    processing_result = fields.Text()

    processing_logs = fields.Binary(string=_(u'Processing logs'), prefetch=False, attachment=False)

    #-------------------------------
    # file processing
    @api.depends('active', 'to_process', 'processing_status', 'date_start_processing', 'date_stop_processing', 'process_when_updated', 'date_updated', 'date_addition')
    def _file_needs_processing(self):
        for record in self:
            result = False
            # File has been updated and to be processed when update
            if record.process_when_updated:
                upd_time = timegm(datetime.strptime(record.date_updated, DEFAULT_SERVER_DATETIME_FORMAT).timetuple())
                if record.date_stop_processing:
                    lastproc_time = timegm(datetime.strptime(record.date_stop_processing,
                                                             DEFAULT_SERVER_DATETIME_FORMAT).timetuple())
                else:
                    lastproc_time = 0

                result = (lastproc_time > 0) and (upd_time > lastproc_time) and (record.processing_status != 'running')

            # File is New or process is waiting for processing
            result = result or (record.processing_status == 'pending') or (record.processing_status == 'new')

            # file is to be processed not already being processed
            result = result and (record.to_process) and (record.processing_status != 'running')

            # File is active and config also
            if len(record.import_config) > 0:
                result = result and (record.active) and (record.import_config.active)
            else:
                result = False

            # Partner Needed?
            needs_partner_val = self.env['ir.config_parameter'].get_param('goufi.config_needs_partner')
            config_needs_partner = True if needs_partner_val == 'True' else False
            if config_needs_partner:
                if len(record.import_config) > 0:
                    result = result and ((len(record.partner_id) > 0) or (
                        len(record.import_config.default_partner_id) > 0))
                else:
                    result = result and (len(record.partner_id) > 0)

            record.needs_to_be_processed = result

    #-------------------------------------------------------------------------------------
    @api.one
    def does_file_need_processing(self, force=False):
        """
        Returns true if the given ImportFile is to be processed
        """
        if isinstance(self, ImportFile):

            result = self.needs_to_be_processed

            # file is to be processed or process is forced and not already being processed
            result = result or (force and self.processing_status != 'running')

            return result
        else:
            return False

    def reset_processing_status(self):
        for aFile in self:
            aFile.processing_status = 'pending'
            aFile.date_start_processing = False
            aFile.date_stop_processing = False

    def force_process_file(self):
        for aFile in self:
            aFile._process_a_file(force=True)

    def process_file(self):
        for aFile in self:
            if aFile.needs_to_be_processed:
                lang = aFile.import_config.context_language
                if lang == False:
                    lang = aFile.import_config._get_default_language()
                if lang:
                    aFile.with_context({'lang': lang.code})._process_a_file(force=False)
                else:
                    aFile.with_context({'lang': lang.code})._process_a_file(force=False)

    def _process_a_file(self, force=False):
        """
        Process the file
        if it has been updated or are in status new or pending
        """
        if self.import_config:
            cls = None
            mod = None

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
                logging.error("GOUFI: Cannot process file, error when evaluating processor module" +
                              self.filename + "(" + str(e) + ")")

            # Process File
            # TODO: one day provide a way to re-use processor instances?
            if mod and cls:
                proc_inst = cls(self.import_config)
                try:
                    proc_inst.process_file(self, force)
                except Exception as e:
                    logging.exception("Not Able to Process import File %s" % self.filename)

    #-------------------------------
    # automation of file processing

    @api.model
    def process_files(self, criteria=[], maxFiles=10, anOrder=None):

        import_file_model = self.env['goufi.import_file']

        if import_file_model != None:
            records = ()
            if anOrder == None:
                records = import_file_model.search(criteria, limit=maxFiles)
            else:
                records = import_file_model.search(criteria, order=anOrder, limit=maxFiles)
            for rec in records:
                rec.process_file()

    #-------------------------------
    # standard model method override

    @api.depends(lambda self: (self._rec_name,) if self._rec_name else ())
    def _compute_display_name(self):
        for record in self:
            if record.filename and record.import_config:
                record.display_name = '[' + record.import_config.name + '] ' + path.basename(record.filename)
            else:
                models.Model._compute_display_name(record)

    def create(self, values):
        if 'import_config' in values:
            config = self.env['goufi.import_configuration'].browse((values['import_config'],))
            if len(config) > 0:
                config = config[0]
                if config.default_partner_id:
                    values['partner_id'] = config.default_partner_id.id
                values['header_line_index'] = config.default_header_line_index

        return super(ImportFile, self).create(values)

    def write(self, values):
        if 'import_config' in values:
            config = self.env['goufi.import_configuration'].browse((values['import_config'],))
            if len(config) > 0:
                config = config[0]
                if config.default_partner_id:
                    values['partner_id'] = config.default_partner_id.id
        return super(ImportFile, self).write(values)
