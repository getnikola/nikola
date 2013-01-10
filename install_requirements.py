#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Helper tool to install the right requirements using pip based on the
running Python version. It requires ``pip`` to be installed and found
in the $PATH.

:author: Niko Wenselowski
"""
from __future__ import unicode_literals, print_function

import sys
import os


def get_requirements_file_path():
    """Returns the absolute path to the correct requirements file."""
    directory = os.path.dirname(__file__)

    if sys.version_info[0] == 3:
        requirements_file = 'requirements-3.txt'
    else:
        requirements_file = 'requirements.txt'

    return os.path.join(directory, requirements_file)


def main():
    requirements_file = get_requirements_file_path()
    print('Installing requirements from %s' % requirements_file)
    os.system('pip install -r %s --use-mirrors' % requirements_file)


if __name__ == '__main__':
    main()
