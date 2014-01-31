#!/usr/bin/env python
# For internal use only.
"""Return the Python version in a sane format (vX.Y.Z)."""
import sys
print("v" + (".".join([str(i) for i in sys.version_info[0:3]])))
