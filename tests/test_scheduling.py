import datetime
import sys

import dateutil.parser
import dateutil.tz
import pytest

from nikola.plugins.command.new_post import get_date

freezegun = pytest.importorskip('freezegun')
freeze_time = freezegun.freeze_time

UTC = dateutil.tz.tzutc()
_NOW = datetime.datetime(  # Thursday
    2013, 8, 22, 10, 0, 0, tzinfo=UTC)
RULE_TH = 'RRULE:FREQ=WEEKLY;BYDAY=TH'
RULE_FR = 'RRULE:FREQ=WEEKLY;BYDAY=FR'


@pytest.fixture(autouse=True)
def disable_six_modules():
    deleted = {
        name: sys.modules.pop(name)
        for name in sys.modules
        if name.startswith("six.moves.")
    }
    try:
        yield
    finally:
        for name, mod in deleted.items():
            sys.modules[name] = mod


@freeze_time(_NOW)
def test_get_date(today):
    # NOW does not match rule #########################################
    # No last date
    expected = today.replace(day=23)
    assert expected == get_date(True, RULE_FR, tz=UTC)[1]
    assert expected == get_date(True, RULE_FR, tz=UTC)[1]

    # Last date in the past; doesn't match rule
    date = today.replace(hour=7)
    expected = today.replace(day=23, hour=7)
    assert expected == get_date(True, RULE_FR, date, tz=UTC)[1]

    # Last date in the future; doesn't match rule
    date = today.replace(day=24, hour=7)
    expected = today.replace(day=30, hour=7)
    assert expected == get_date(True, RULE_FR, date, tz=UTC)[1]

    # Last date in the past; matches rule
    date = today.replace(day=16, hour=8)
    expected = today.replace(day=23, hour=8)
    assert expected == get_date(True, RULE_FR, date, tz=UTC)[1]

    # Last date in the future; matches rule
    date = today.replace(day=23, hour=18)
    expected = today.replace(day=30, hour=18)
    assert expected == get_date(True, RULE_FR, date, tz=UTC)[1]

    # NOW matches rule ################################################
    # Not scheduling should return NOW
    assert _NOW == get_date(False, RULE_TH, tz=UTC)[1]

    # No last date
    assert _NOW == get_date(True, RULE_TH, tz=UTC)[1]
    assert _NOW == get_date(True, RULE_TH, tz=UTC)[1]

    # Last date in the past; doesn't match rule
    # Corresponding time has already passed, today
    date = today.replace(day=21, hour=7)
    expected = today.replace(day=29, hour=7)
    assert expected == get_date(True, RULE_TH, date, tz=UTC)[1]
    # Corresponding time has not passed today
    date = today.replace(day=21, hour=18)
    expected = today.replace(day=22, hour=18)
    assert expected == get_date(True, RULE_TH, date, tz=UTC)[1]

    # Last date in the future; doesn't match rule
    # Corresponding time has already passed, today
    date = today.replace(day=24, hour=7)
    expected = today.replace(day=29, hour=7)
    assert expected == get_date(True, RULE_TH, date, tz=UTC)[1]
    # Corresponding time has not passed today
    date = today.replace(day=24, hour=18)
    expected = today.replace(day=29, hour=18)
    assert expected == get_date(True, RULE_TH, date, tz=UTC)[1]

    # Last date in the past; matches rule
    # Corresponding time has already passed, today
    date = today.replace(day=15, hour=7)
    expected = today.replace(day=29, hour=7)
    assert expected == get_date(True, RULE_TH, date, tz=UTC)[1]
    # Corresponding time has already passed, today; rule specifies HOUR
    date = today.replace(day=15, hour=7)
    expected = today.replace(day=29, hour=9)
    assert expected == get_date(True, RULE_TH + ';BYHOUR=9', date, tz=UTC)[1]
    # Corresponding time has not passed today
    date = today.replace(day=15, hour=18)
    expected = today.replace(day=22, hour=18)
    assert expected == get_date(True, RULE_TH, date, tz=UTC)[1]

    # Last date in the future; matches rule
    # Corresponding time has already passed, today
    date = today.replace(day=29, hour=7)
    expected = today.replace(day=5, month=9, hour=7)
    assert expected == get_date(True, RULE_TH, date, tz=UTC)[1]
    # Corresponding time has not passed today
    date = today.replace(day=22, hour=18)
    expected = today.replace(day=29, hour=18)
    assert expected == get_date(True, RULE_TH, date, tz=UTC)[1]


@pytest.fixture
def today():
    NOW = _NOW.strftime('%Y-%m-%d %H:%M:%S %Z')
    return dateutil.parser.parse(NOW)
