#!/usr/bin/env python
# For internal use only.
"""Return the Python version in a sane format (vX.Y).

Also available a less sane format (X.Y) if `short` is provided
as an argument.

Or ([v]X.Y.Z) if `long` is provided.

$ getpyver.py
v2.7
$ getpyver.py short
2.7
$ getpyver.py long
v2.7.6
$ getpyver.py long short
2.7.6

"""
import sys
limit = 3 if 'long' in sys.argv else 2
if 'short' in sys.argv:
    print(".".join([str(i) for i in sys.version_info[0:limit]]))
else:
    print("v" + (".".join([str(i) for i in sys.version_info[0:limit]])))
