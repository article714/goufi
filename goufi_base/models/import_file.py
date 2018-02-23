# -*- coding: utf-8 -*-
# ©2017 - C. Guychard
# License: AGPL v3

from odoo import models, fields, _, api


class ImportFile(models.Model):
    _inherit = ['mail.thread']
    _name = 'goufi.import_file'
    _description = u"Import File"
    _rec_name = "filename"

    # File identification
    filename = fields.Char(string = _(u'File name'), required = True, track_visibility = 'onchange')

    filesize = fields.Float(string = _(u"File size"))

    partner_id = fields.Many2one(comodel_name = 'res.partner', track_visibility = 'onchange')

    date_addition = fields.Datetime(string = _(u"Date d'ajout"))

    # parametrage du traitement

    to_process = fields.Boolean(string = _(u"File is to be processed"), default = True)

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
    # automation of file detection

    @api.model
    def detect(self):
        print("TODO")
