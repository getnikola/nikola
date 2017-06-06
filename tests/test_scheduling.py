# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

import datetime
import sys

import dateutil.parser
import dateutil.tz
import pytest

from .base import BaseTestCase

try:
    from freezegun import freeze_time
    _freeze_time = True
except ImportError:
    _freeze_time = False

    def freeze_time(x):
        return lambda y: y

_NOW = datetime.datetime(  # Thursday
    2013, 8, 22, 10, 0, 0, tzinfo=dateutil.tz.tzutc())


@pytest.mark.skipif(not _freeze_time, reason="freezegun not installed.")
class TestScheduling(BaseTestCase):

    @classmethod
    def setUp(cls):
        d = [name for name in sys.modules if name.startswith("six.moves.")]
        cls.deleted = {}
        for name in d:
            cls.deleted[name] = sys.modules[name]
            del sys.modules[name]

    @classmethod
    def tearDown(cls):
        for name, mod in cls.deleted.items():
            sys.modules[name] = mod

    @freeze_time(_NOW)
    def test_get_date(self):
        from nikola.plugins.command.new_post import get_date

        FMT = '%Y-%m-%d %H:%M:%S %Z'
        NOW = _NOW.strftime(FMT)
        TODAY = dateutil.parser.parse(NOW)
        RULE_TH = 'RRULE:FREQ=WEEKLY;BYDAY=TH'
        RULE_FR = 'RRULE:FREQ=WEEKLY;BYDAY=FR'
        UTC = dateutil.tz.tzutc()

        # NOW does not match rule #########################################
        # No last date
        expected = TODAY.replace(day=23)
        self.assertEqual(expected, get_date(True, RULE_FR, tz=UTC)[1])
        self.assertEqual(expected, get_date(True, RULE_FR, tz=UTC)[1])

        # Last date in the past; doesn't match rule
        date = TODAY.replace(hour=7)
        expected = TODAY.replace(day=23, hour=7)
        self.assertEqual(expected, get_date(True, RULE_FR, date, tz=UTC)[1])

        # Last date in the future; doesn't match rule
        date = TODAY.replace(day=24, hour=7)
        expected = TODAY.replace(day=30, hour=7)
        self.assertEqual(expected, get_date(True, RULE_FR, date, tz=UTC)[1])

        # Last date in the past; matches rule
        date = TODAY.replace(day=16, hour=8)
        expected = TODAY.replace(day=23, hour=8)
        self.assertEqual(expected, get_date(True, RULE_FR, date, tz=UTC)[1])

        # Last date in the future; matches rule
        date = TODAY.replace(day=23, hour=18)
        expected = TODAY.replace(day=30, hour=18)
        self.assertEqual(expected, get_date(True, RULE_FR, date, tz=UTC)[1])

        # NOW matches rule ################################################
        # Not scheduling should return NOW
        self.assertEqual(_NOW, get_date(False, RULE_TH, tz=UTC)[1])
        # No last date
        self.assertEqual(_NOW, get_date(True, RULE_TH, tz=UTC)[1])
        self.assertEqual(_NOW, get_date(True, RULE_TH, tz=UTC)[1])

        # Last date in the past; doesn't match rule
        # Corresponding time has already passed, today
        date = TODAY.replace(day=21, hour=7)
        expected = TODAY.replace(day=29, hour=7)
        self.assertEqual(expected, get_date(True, RULE_TH, date, tz=UTC)[1])
        # Corresponding time has not passed today
        date = TODAY.replace(day=21, hour=18)
        expected = TODAY.replace(day=22, hour=18)
        self.assertEqual(expected, get_date(True, RULE_TH, date, tz=UTC)[1])

        # Last date in the future; doesn't match rule
        # Corresponding time has already passed, today
        date = TODAY.replace(day=24, hour=7)
        expected = TODAY.replace(day=29, hour=7)
        self.assertEqual(expected, get_date(True, RULE_TH, date, tz=UTC)[1])
        # Corresponding time has not passed today
        date = TODAY.replace(day=24, hour=18)
        expected = TODAY.replace(day=29, hour=18)
        self.assertEqual(expected, get_date(True, RULE_TH, date, tz=UTC)[1])

        # Last date in the past; matches rule
        # Corresponding time has already passed, today
        date = TODAY.replace(day=15, hour=7)
        expected = TODAY.replace(day=29, hour=7)
        self.assertEqual(expected, get_date(True, RULE_TH, date, tz=UTC)[1])
        # Corresponding time has already passed, today; rule specifies HOUR
        date = TODAY.replace(day=15, hour=7)
        expected = TODAY.replace(day=29, hour=9)
        self.assertEqual(expected, get_date(
            True, RULE_TH + ';BYHOUR=9', date, tz=UTC)[1])
        # Corresponding time has not passed today
        date = TODAY.replace(day=15, hour=18)
        expected = TODAY.replace(day=22, hour=18)
        self.assertEqual(expected, get_date(True, RULE_TH, date, tz=UTC)[1])

        # Last date in the future; matches rule
        # Corresponding time has already passed, today
        date = TODAY.replace(day=29, hour=7)
        expected = TODAY.replace(day=5, month=9, hour=7)
        self.assertEqual(expected, get_date(True, RULE_TH, date, tz=UTC)[1])
        # Corresponding time has not passed today
        date = TODAY.replace(day=22, hour=18)
        expected = TODAY.replace(day=29, hour=18)
        self.assertEqual(expected, get_date(True, RULE_TH, date, tz=UTC)[1])


if __name__ == '__main__':
    import unittest
    unittest.main()
