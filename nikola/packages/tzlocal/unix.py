"""Unix support for tzlocal."""
import os
import re

import dateutil.tz

_cache_tz = None


def _try_tz_from_env():
    tzenv = os.environ.get("TZ")
    if tzenv and tzenv[0] == ":":
        tzenv = tzenv[1:]
    try:
        if tzenv:
            dateutil.tz.gettz(tzenv)
            return tzenv
    except Exception:
        pass


def _get_localzone(_root="/"):
    """Try to find the local timezone configuration.

    The parameter _root makes the function look for files like /etc/localtime
    beneath the _root directory. This is primarily used by the tests.
    In normal usage you call the function without parameters.
    """
    tzenv = _try_tz_from_env()
    if tzenv:
        return tzenv

    # Are we under Termux on Android?
    if os.path.exists("/system/bin/getprop"):
        import subprocess

        androidtz = (
            subprocess.check_output(["getprop", "persist.sys.timezone"])
            .strip()
            .decode()
        )
        return androidtz

    # Now look for distribution specific configuration files
    # that contain the timezone name.
    for configfile in ("etc/timezone", "var/db/zoneinfo"):
        tzpath = os.path.join(_root, configfile)
        try:
            with open(tzpath, "rb") as tzfile:
                data = tzfile.read()

                # Issue #3 was that /etc/timezone was a zoneinfo file.
                # That's a misconfiguration, but we need to handle it gracefully:
                if data[:5] == b"TZif2":
                    continue

                etctz = data.strip().decode()
                if not etctz:
                    # Empty file, skip
                    continue
                for etctz in data.decode().splitlines():
                    # Get rid of host definitions and comments:
                    if " " in etctz:
                        etctz, dummy = etctz.split(" ", 1)
                    if "#" in etctz:
                        etctz, dummy = etctz.split("#", 1)
                    if not etctz:
                        continue
                    tz = etctz.replace(" ", "_")
                    return tz

        except IOError:
            # File doesn't exist or is a directory
            continue

    # CentOS has a ZONE setting in /etc/sysconfig/clock,
    # OpenSUSE has a TIMEZONE setting in /etc/sysconfig/clock and
    # Gentoo has a TIMEZONE setting in /etc/conf.d/clock
    # We look through these files for a timezone:

    zone_re = re.compile(r"\s*ZONE\s*=\s*\"")
    timezone_re = re.compile(r"\s*TIMEZONE\s*=\s*\"")
    end_re = re.compile('"')

    for filename in ("etc/sysconfig/clock", "etc/conf.d/clock"):
        tzpath = os.path.join(_root, filename)
        try:
            with open(tzpath, "rt") as tzfile:
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
                    etctz = line[: end_re.search(line).start()]

                    # We found a timezone
                    tz = etctz.replace(" ", "_")
                    return tz

        except IOError:
            # File doesn't exist or is a directory
            continue

    # systemd distributions use symlinks that include the zone name,
    # see manpage of localtime(5) and timedatectl(1)
    tzpath = os.path.join(_root, "etc/localtime")
    if os.path.exists(tzpath) and os.path.islink(tzpath):
        tzpath = os.path.realpath(tzpath)
        start = tzpath.find("/") + 1
        while start != 0:
            tzpath = tzpath[start:]
            try:
                tested_tz = dateutil.tz.gettz(tzpath)
                if tested_tz:
                    return tzpath
            except Exception:
                pass
            start = tzpath.find("/") + 1

    # Nothing found, return UTC
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
