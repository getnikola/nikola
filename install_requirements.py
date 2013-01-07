#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function

import sys
import os

if sys.version_info[0] == 3:
    requirements_file = 'requirements-3.txt'
else:
    requirements_file = 'requirements.txt'


print('Installing requirements from %s' % requirements_file)
os.system('pip install -r %s --use-mirrors' % requirements_file)