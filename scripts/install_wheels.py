#!/usr/bin/env python
"""Install wheels from Python."""
import wheel.install
import glob
import sys

wheels = glob.glob(sys.argv[1] + '/*.whl')
for i in wheels:
    w = wheel.install.WheelFile(i)
    w.install()
