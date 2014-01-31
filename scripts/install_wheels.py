#!/usr/bin/env python
"""Install wheels from Python."""
import wheel.install
import glob
import sys

wheels = glob.glob(sys.argv[1] + '/*.whl')
print('Installing wheels...')
for i in wheels:
    print(i)
    w = wheel.install.WheelFile(i)
    w.install()
