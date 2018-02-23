# -*- coding: utf-8 -*-
# ©2017 Openflexo, Certificare
# License: TBD


from odoo import models, fields, _

class ImportFile(models.Model):
    _inherit = ['mail.thread']
    _name = 'certificare.import_file'
    _description = u"Fichier d'import"
    _rec_name = "fichier"

    # identification du fichier
    fichier = fields.Char(string = _(u'Nom du fichier'), required = True, track_visibility = 'onchange')

    filesize = fields.Float(string = _(u"Taille du fichier"))

    partenaire = fields.Many2one(comodel_name = 'res.partner', track_visibility = 'onchange')

    date_ajout = fields.Datetime(string = _(u"Date d'ajout"))

    # parametrage du traitement

    to_process = fields.Boolean(string = _(u"Fichier à Traiter?"), default = True)

    num_ligne_entete = fields.Integer(string = _("Indice en-tête"), help = "Indique le numéro de la ligne d'en-tête")

    # etat du traitement
    date_traitement = fields.Datetime(string = _(u"Début du traitement"), track_visibility = 'onchange')
    date_fin_traitement = fields.Datetime(string = _(u"Fin du traitement"), track_visibility = 'onchange')

    etat_traitement = fields.Selection([('new', 'new'),
                                (u'en cours', u'en cours'),
                                (u'termine', u'terminé'),
                                (u'echec', u'échec')],
                                string = _(u"Etat du traitement"), default = 'new', track_visibility = 'onchange')

    resultat_traitement = fields.Text()

    log_traitement = fields.Binary(string = _(u'Logs des traitements'), prefetch = False, attachment = False)

