"""tzlocal for OS X."""

import os
import dateutil.tz
import subprocess

_cache_tz = None


def _get_localzone():
    tzname = subprocess.check_output(["systemsetup", "-gettimezone"]).decode('utf-8')
    tzname = tzname.replace("Time Zone: ", "")
    # OS X 10.9+, this command is root-only
    if 'exiting!' in tzname:
        tzname = ''

    if not tzname:
        # link will be something like /usr/share/zoneinfo/America/Los_Angeles.
        link = os.readlink("/etc/localtime")
        tzname = link.split('zoneinfo/')[-1]
    tzname = tzname.strip()
    try:
        # test the name
        assert tzname
        dateutil.tz.gettz(tzname)
        return tzname
    except:
        return None


def get_localzone():
    """Get the computers configured local timezone, if any."""
    global _cache_tz
    if _cache_tz is None:
        _cache_tz = _get_localzone()
    return _cache_tz


def reload_localzone():
    """Reload the cached localzone. You need to call this if the timezone has changed."""
    global _cache_tz
    _cache_tz = _get_localzone()
    return _cache_tz
