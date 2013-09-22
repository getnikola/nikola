# coding: utf8
# Author: Rodrigo Bistolfi
# Date: 03/2013


""" Base class for Nikola test cases """


__all__ = ["BaseTestCase", "cd"]

from contextlib import contextmanager
import os
import sys
import unittest

import logbook

# Make logbook shutup
from nikola.utils import LOGGER

LOGGER.handlers.append(logbook.TestHandler())


if sys.version_info < (2, 7):

    try:
        import unittest2
        _unittest2 = True
    except ImportError:
        _unittest2 = False

    if _unittest2:
        BaseTestCase = unittest2.TestCase

    else:

        class BaseTestCase(unittest.TestCase):
            """ Base class for providing 2.6 compatibility """

            def assertIs(self, first, second, msg=None):
                self.assertTrue(first is second)

            def assertIsNot(self, first, second, msg=None):
                self.assertTrue(first is not second)

            def assertIsNone(self, expr, msg=None):
                self.assertTrue(expr is None)

            def assertIsNotNone(self, expr, msg=None):
                self.assertTrue(expr is not None)

            def assertIn(self, first, second, msg=None):
                self.assertTrue(first in second)

            def assertNotIn(self, first, second, msg=None):
                self.assertTrue(first not in second)

            def assertIsInstance(self, obj, cls, msg=None):
                self.assertTrue(isinstance(obj, cls))

            def assertNotIsInstance(self, obj, cls, msg=None):
                self.assertFalse(isinstance(obj, cls))


else:
    BaseTestCase = unittest.TestCase


@contextmanager
def cd(path):
    old_dir = os.getcwd()
    os.chdir(path)
    yield
    os.chdir(old_dir)
