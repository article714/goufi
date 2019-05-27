# -*- coding: utf-8 -*-
"""
Created on 25 July 2018

@author: C. Guychard
@copyright: ©2018 Article 714
@license: AGPL v3
"""

from odoo import models

from odoo.addons.queue_job.job import job


class ImportFile(models.Model):
    _inherit = "goufi.import_file"

    @job
    def enqueue_file_processing(self):
        """

        enqueue processing for file in a configured queue

        """
        self.with_delay().process_file()
