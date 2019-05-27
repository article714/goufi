# -*- coding: utf-8 -*-
"""
Created on 26 feb. 2018

@author: C. Guychard
@copyright: ©2018 Article 714
@license: AGPL v3
"""

import logging
import sys
import unittest

from odoo import exceptions
from odoo.tests.common import TransactionCase


class TestImportConfiguration(TransactionCase):
    def test_it(self):
        return True

    def setUp(self):
        super(TestImportConfiguration, self).setUp()

        self.config = self.env["goufi.import_configuration"].new()
