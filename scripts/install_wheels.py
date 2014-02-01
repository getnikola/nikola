#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Nikola Wheel Installer
# ...because outsourcing never works.

# Copyright © 2014 Chris Warrick and others.

# Permission is hereby granted, free of charge, to any
# person obtaining a copy of this software and associated
# documentation files (the "Software"), to deal in the
# Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the
# Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice
# shall be included in all copies or substantial portions of
# the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY
# KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
# PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS
# OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""Install wheels for Nikola.  Sans outsourcing."""

from pip._vendor import requests  # THANK YOU PIP!
import wheel.install
import glob
import sys

pyver = '.'.join([str(i) for i in sys.version_info[0:3]])

wheels = glob.glob('/home/travis/build/getnikola/nikola/wheelhouse-v{pyver}/*.whl'.format(pyver=pyver))
print('Installing wheels...')
for i in wheels:
    print(i)
    w = wheel.install.WheelFile(i)
    w.install()
