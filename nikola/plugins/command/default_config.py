# -*- coding: utf-8 -*-

# Copyright © 2012-2019 Roberto Alsina and others.

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

"""Show the default configuration."""

from nikola.plugin_categories import Command
from nikola.utils import get_logger
import nikola.plugins.command.init
import sys


LOGGER = get_logger('default_config')


class CommandShowConfig(Command):
    """Show the default configuration."""

    name = "default_config"

    doc_usage = ""
    needs_config = False
    doc_purpose = "Print the default Nikola configuration."
    cmd_options = []

    def _execute(self, options=None, args=None):
        """Show the default configuration."""
        try:
            print(nikola.plugins.command.init.CommandInit.create_configuration_to_string())
        except Exception:
            sys.stdout.buffer.write(nikola.plugins.command.init.CommandInit.create_configuration_to_string().encode('utf-8'))
