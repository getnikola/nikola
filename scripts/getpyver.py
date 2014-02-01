#!/usr/bin/env python
# For internal use only.
"""Return the Python version in a sane format (vX.Y.Z).

Also available a less sane format (X.Y.Z) if `short` is provided
as an argument.

"""
import sys
if 'short' in sys.argv:
    print(".".join([str(i) for i in sys.version_info[0:3]]))
else:
    print("v" + (".".join([str(i) for i in sys.version_info[0:3]])))
