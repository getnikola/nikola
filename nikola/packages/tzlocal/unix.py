"""tzlocal for UNIX."""

from __future__ import with_statement
import os
import re
import dateutil.tz

_cache_tz = None


def _get_localzone():
    """Try to find the local timezone configuration.

    This method prefers finding the timezone name and passing that to pytz,
    over passing in the localtime file, as in the later case the zoneinfo
    name is unknown.

    The parameter _root makes the function look for files like /etc/localtime
    beneath the _root directory. This is primarily used by the tests.
    In normal usage you call the function without parameters.
    """
    tz = os.environ.get('TZ')
    if tz and tz[0] == ':':
        tz = tz[1:]
    try:
        if tz:
            dateutil.tz.gettz(tz)
            return tz
    except:
        pass

    try:
        # link will be something like /usr/share/zoneinfo/America/Los_Angeles.
        link = os.readlink('/etc/localtime')
        tz = link.split('zoneinfo/')[-1]

        if tz:
            dateutil.tz.gettz(tz)
            return tz
    except:
        return None

    # Now look for distribution specific configuration files
    # that contain the timezone name.
    tzpath = os.path.join('/etc/timezone')
    if os.path.exists(tzpath):
        with open(tzpath, 'rb') as tzfile:
            data = tzfile.read()

            # Issue #3 was that /etc/timezone was a zoneinfo file.
            # That's a misconfiguration, but we need to handle it gracefully:
            if data[:5] != 'TZif2':
                etctz = data.strip().decode()
                # Get rid of host definitions and comments:
                if ' ' in etctz:
                    etctz, dummy = etctz.split(' ', 1)
                if '#' in etctz:
                    etctz, dummy = etctz.split('#', 1)
                tz = etctz.replace(' ', '_')
                try:
                    if tz:
                        dateutil.tz.gettz(tz)
                        return tz
                except:
                    pass

    # CentOS has a ZONE setting in /etc/sysconfig/clock,
    # OpenSUSE has a TIMEZONE setting in /etc/sysconfig/clock and
    # Gentoo has a TIMEZONE setting in /etc/conf.d/clock
    # We look through these files for a timezone:

    zone_re = re.compile('\s*ZONE\s*=\s*\"')
    timezone_re = re.compile('\s*TIMEZONE\s*=\s*\"')
    end_re = re.compile('\"')

    for tzpath in ('/etc/sysconfig/clock', '/etc/conf.d/clock'):
        if not os.path.exists(tzpath):
            continue
        with open(tzpath, 'rt') as tzfile:
            data = tzfile.readlines()

        for line in data:
            # Look for the ZONE= setting.
            match = zone_re.match(line)
            if match is None:
                # No ZONE= setting. Look for the TIMEZONE= setting.
                match = timezone_re.match(line)
            if match is not None:
                # Some setting existed
                line = line[match.end():]
                etctz = line[:end_re.search(line).start()]

                # We found a timezone
                tz = etctz.replace(' ', '_')
                try:
                    if tz:
                        dateutil.tz.gettz(tz)
                        return tz
                except:
                    pass

    # Nikola cannot use this thing below...

    # No explicit setting existed. Use localtime
    # for filename in ('etc/localtime', 'usr/local/etc/localtime'):
        # tzpath = os.path.join(_root, filename)

        # if not os.path.exists(tzpath):
            # continue
        # with open(tzpath, 'rb') as tzfile:
            # return pytz.tzfile.build_tzinfo('local', tzfile)

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
