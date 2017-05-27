# -*- coding: utf-8 -*-

# Copyright © 2012-2017 Roberto Alsina and others.

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

"""Beg the user to switch to python 3."""

import datetime
import os
import random
import sys

import doit.tools

from nikola.utils import get_logger, STDERR_HANDLER
from nikola.plugin_categories import LateTask

PY2_AND_NO_PY3_WARNING = """Nikola is going to deprecate Python 2 support in 2017. Your current
version will continue to work, but please consider upgrading to Python 3.

Please check http://bit.ly/1FKEsiX for details.
"""
PY2_WARNING = """Nikola is going to deprecate Python 2 support in 2017. You already have Python 3
available in your system. Why not switch?

Please check http://bit.ly/1FKEsiX for details.
"""
PY2_BARBS = [
    "Python 2 has been deprecated for years. Stop clinging to your long gone youth and switch to Python3.",
    "Python 2 is the safety blanket of languages. Be a big kid and switch to Python 3",
    "Python 2 is old and busted. Python 3 is the new hotness.",
    "Nice unicode you have there, would be a shame something happened to it.. switch to python 3!.",
    "Don't get in the way of progress! Upgrade to Python 3 and save a developer's mind today!",
    "Winners don't use Python 2 -- Signed: The FBI",
    "Python 2? What year is it?",
    "I just wanna tell you how I'm feeling\n"
    "Gotta make you understand\n"
    "Never gonna give you up [But Python 2 has to go]",
    "The year 2009 called, and they want their Python 2.7 back.",
]


LOGGER = get_logger('Nikola', STDERR_HANDLER)


def has_python_3():
    """Check if python 3 is available."""
    if 'win' in sys.platform:
        py_bin = 'py.exe'
    else:
        py_bin = 'python3'
    for path in os.environ["PATH"].split(os.pathsep):
        if os.access(os.path.join(path, py_bin), os.X_OK):
            return True
    return False


class Py3Switch(LateTask):
    """Beg the user to switch to python 3."""

    name = "_switch to py3"

    def gen_tasks(self):
        """Beg the user to switch to python 3."""
        def give_warning():
            if sys.version_info[0] == 3:
                return
            if has_python_3():
                LOGGER.warn(random.choice(PY2_BARBS))
                LOGGER.warn(PY2_WARNING)
            else:
                LOGGER.warn(PY2_AND_NO_PY3_WARNING)

        task = {
            'basename': self.name,
            'name': 'please!',
            'actions': [give_warning],
            'clean': True,
            'uptodate': [doit.tools.timeout(datetime.timedelta(days=3))]
        }

        return task
