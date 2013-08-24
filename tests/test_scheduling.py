# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from base import BaseTestCase
import datetime
from nose.plugins.skip import SkipTest
try:
    from freezegun import freeze_time
    _freeze_time = True
except ImportError:
    _freeze_time = False
    freeze_time = lambda x: lambda y: y

FMT = '%Y/%m/%d %H:%M:%S'
NOW = '2013/08/22 10:00:00'  # Thursday
TODAY = datetime.datetime.strptime(NOW, FMT)
RULE_TH = 'RRULE:FREQ=WEEKLY;BYDAY=TH'
RULE_FR = 'RRULE:FREQ=WEEKLY;BYDAY=FR'


class TestScheduling(BaseTestCase):

    @classmethod
    def setUp(self):
        if not _freeze_time:
            raise SkipTest('freezegun not installed')

    @freeze_time(NOW)
    def test_get_date(self):
        from nikola.plugins.command.new_post import get_date

        #### NOW does not match rule #########################################
        ## No last date
        expected = TODAY.replace(day=23).strftime(FMT)
        self.assertEqual(expected, get_date(True, RULE_FR))
        self.assertEqual(expected, get_date(True, RULE_FR, force_today=True))

        ## Last date in the past; doesn't match rule
        date = TODAY.replace(hour=7)
        expected = TODAY.replace(day=23, hour=7).strftime(FMT)
        self.assertEqual(expected, get_date(True, RULE_FR, date))
        self.assertEqual(expected, get_date(True, RULE_FR, date, True))

        ## Last date in the future; doesn't match rule
        date = TODAY.replace(day=24, hour=7)
        expected = TODAY.replace(day=30, hour=7).strftime(FMT)
        self.assertEqual(expected, get_date(True, RULE_FR, date))
        self.assertEqual(expected, get_date(True, RULE_FR, date, True))

        ## Last date in the past; matches rule
        date = TODAY.replace(day=16, hour=8)
        expected = TODAY.replace(day=23, hour=8).strftime(FMT)
        self.assertEqual(expected, get_date(True, RULE_FR, date))
        self.assertEqual(expected, get_date(True, RULE_FR, date, True))

        ## Last date in the future; matches rule
        date = TODAY.replace(day=23, hour=18)
        expected = TODAY.replace(day=30, hour=18).strftime(FMT)
        self.assertEqual(expected, get_date(True, RULE_FR, date))
        self.assertEqual(expected, get_date(True, RULE_FR, date, True))

        #### NOW matches rule ################################################
        ## Not scheduling should return NOW
        self.assertEqual(NOW, get_date(False, RULE_TH))
        ## No last date
        self.assertEqual(NOW, get_date(True, RULE_TH))
        self.assertEqual(NOW, get_date(True, RULE_TH, force_today=True))

        ## Last date in the past; doesn't match rule
        ### Corresponding time has already passed, today
        date = TODAY.replace(day=21, hour=7)
        expected = TODAY.replace(day=29, hour=7).strftime(FMT)
        self.assertEqual(expected, get_date(True, RULE_TH, date))
        expected = TODAY.replace(day=22, hour=7).strftime(FMT)
        self.assertEqual(expected, get_date(True, RULE_TH, date, True))
        ### Corresponding time has not passed today
        date = TODAY.replace(day=21, hour=18)
        expected = TODAY.replace(day=22, hour=18).strftime(FMT)
        self.assertEqual(expected, get_date(True, RULE_TH, date))
        self.assertEqual(expected, get_date(True, RULE_TH, date, True))

        ## Last date in the future; doesn't match rule
        ### Corresponding time has already passed, today
        date = TODAY.replace(day=24, hour=7)
        expected = TODAY.replace(day=29, hour=7).strftime(FMT)
        self.assertEqual(expected, get_date(True, RULE_TH, date))
        self.assertEqual(expected, get_date(True, RULE_TH, date, True))
        ### Corresponding time has not passed today
        date = TODAY.replace(day=24, hour=18)
        expected = TODAY.replace(day=29, hour=18).strftime(FMT)
        self.assertEqual(expected, get_date(True, RULE_TH, date))
        self.assertEqual(expected, get_date(True, RULE_TH, date, True))

        ## Last date in the past; matches rule
        ### Corresponding time has already passed, today
        date = TODAY.replace(day=15, hour=7)
        expected = TODAY.replace(day=29, hour=7).strftime(FMT)
        self.assertEqual(expected, get_date(True, RULE_TH, date))
        expected = TODAY.replace(day=22, hour=7).strftime(FMT)
        self.assertEqual(expected, get_date(True, RULE_TH, date, True))
        ### Corresponding time has already passed, today; rule specifies HOUR
        date = TODAY.replace(day=15, hour=7)
        expected = TODAY.replace(day=29, hour=9).strftime(FMT)
        self.assertEqual(expected, get_date(True, RULE_TH + ';BYHOUR=9', date))
        expected = TODAY.replace(day=22, hour=9).strftime(FMT)
        self.assertEqual(expected,
                         get_date(True, RULE_TH + ';BYHOUR=9', date, True))
        ### Corresponding time has not passed today
        date = TODAY.replace(day=15, hour=18)
        expected = TODAY.replace(day=22, hour=18).strftime(FMT)
        self.assertEqual(expected, get_date(True, RULE_TH, date))
        self.assertEqual(expected, get_date(True, RULE_TH, date, True))

        ## Last date in the future; matches rule
        ### Corresponding time has already passed, today
        date = TODAY.replace(day=29, hour=7)
        expected = TODAY.replace(day=5, month=9, hour=7).strftime(FMT)
        self.assertEqual(expected, get_date(True, RULE_TH, date))
        ### Corresponding time has not passed today
        date = TODAY.replace(day=22, hour=18)
        expected = TODAY.replace(day=29, hour=18).strftime(FMT)
        self.assertEqual(expected, get_date(True, RULE_TH, date))
        self.assertEqual(expected, get_date(True, RULE_TH, date, True))

if __name__ == '__main__':
    import unittest
    unittest.main()
