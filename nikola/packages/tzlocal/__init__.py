"""Try to figure out what your local timezone is."""
import sys
__version__ = "2.0.0-nikola"

if sys.platform == "win32":
    from .win32 import get_localzone, reload_localzone  # NOQA
else:
    from .unix import get_localzone, reload_localzone  # NOQA
