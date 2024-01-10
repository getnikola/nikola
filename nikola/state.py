# -*- coding: utf-8 -*-

# Copyright © 2012-2024 Roberto Alsina and others.

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

"""Persistent state implementation."""

import json
import os
import shutil
import tempfile
import threading

from . import utils


class Persistor():
    """Persist stuff in a place.

    This is an intentionally dumb implementation. It is *not* meant to be
    fast, or useful for arbitrarily large data. Use lightly.

    Intentionally it has no namespaces, sections, etc. Use as a
    responsible adult.
    """

    def __init__(self, path):
        """Where do you want it persisted."""
        self._path = path
        self._local = threading.local()
        self._local.data = {}

    def _set_site(self, site):
        """Set site and create path directory."""
        self._site = site
        utils.makedirs(os.path.dirname(self._path))

    def get(self, key):
        """Get data stored in key."""
        self._read()
        return self._local.data.get(key)

    def set(self, key, value):
        """Store value in key."""
        self._read()
        self._local.data[key] = value
        self._save()

    def delete(self, key):
        """Delete key and the value it contains."""
        self._read()
        if key in self._local.data:
            self._local.data.pop(key)
        self._save()

    def _read(self):
        if os.path.isfile(self._path):
            with open(self._path) as inf:
                self._local.data = json.load(inf)

    def _save(self):
        dname = os.path.dirname(self._path)
        with tempfile.NamedTemporaryFile(dir=dname, delete=False, mode='w+', encoding='utf-8') as outf:
            tname = outf.name
            json.dump(self._local.data, outf, sort_keys=True, indent=2)
        shutil.move(tname, self._path)
