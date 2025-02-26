# -*- coding: utf-8 -*-

# Copyright © 2012-2025 Roberto Alsina and others.

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

"""Nikola -- a modular, fast, simple, static website generator."""

import os

# The current Nikola version:
__version__ = '8.3.1'

# A flag whether logging should emit debug information:
DEBUG = bool(os.getenv('NIKOLA_DEBUG'))

# A flag whether special templates trace logging should be generated:
TEMPLATES_TRACE = bool(os.getenv('NIKOLA_TEMPLATES_TRACE'))

# A flag to show tracebacks of unhandled exceptions.
# This is a less noisy alternative to the NIKOLA_DEBUG flag.
SHOW_TRACEBACKS = bool(os.getenv('NIKOLA_SHOW_TRACEBACKS'))

from .nikola import Nikola  # NOQA
from . import plugins  # NOQA
