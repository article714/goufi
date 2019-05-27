# -*- coding: utf-8 -*-
"""
Created on februrary 23, 2018

@author: C. Guychard
@copyright: ©2018 Article 714
@license: AGPL v3
"""

import logging
import sys
import unittest

from odoo import exceptions


def log_handler_by_class(logger, handler_cls):
    for handler in logger.handlers:
        if isinstance(handler, handler_cls):
            yield handler


def remove_logging_handler(logger_name, handler_cls):
    """Removes handlers of specified classes from a :class:`logging.Logger`
    with a given name.

    :param string logger_name: name of the logger

    :param handler_cls: class of the handler to remove. You can pass a tuple of
        classes to catch several classes
    """
    logger = logging.getLogger(logger_name)
    for handler in log_handler_by_class(logger, handler_cls):
        logger.removeHandler(handler)
