#!/usr/bin/env python
"""Install wheels from Python."""
import wheel.install
import glob
import sys

pyver = '.'.join([str(i) for i in sys.version_info[0:3]])

wheels = glob.glob('wheelhouse-v{pyver}/*.whl'.format(pyver=pyver))
print('Installing wheels...')
for i in wheels:
    print(i)
    w = wheel.install.WheelFile(i)
    w.install()
