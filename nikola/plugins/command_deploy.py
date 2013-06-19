# Copyright (c) 2012 Roberto Alsina y otros.

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

from __future__ import print_function
from ast import literal_eval
import codecs
from datetime import datetime
import os
import subprocess
import time


from nikola.plugin_categories import Command


class Deploy(Command):
    """Deploy site.  """
    name = "deploy"

    doc_usage = ""
    doc_purpose = "Deploy the site."

    def _execute(self, command, args):
        # Get last succesful deploy date
        timestamp_path = os.path.join(self.site.config['CACHE_FOLDER'], 'lastdeploy')
        if self.site.config['DISQUS_FORUM'] == 'nikolademo':
            print("\nWARNING WARNING WARNING WARNING\n"
                  "You are deploying using the nikolademo Disqus account.\n"
                  "That means you will not be able to moderate the comments in your own site.\n"
                  "And is probably not what you want to do.\n"
                  "Think about it for 5 seconds, I'll wait :-)\n\n")
            time.sleep(5)
        for command in self.site.config['DEPLOY_COMMANDS']:
            try:
                with open(timestamp_path, 'rb') as inf:
                    last_deploy = literal_eval(inf.read().strip())
            except Exception:
                last_deploy = datetime(1970, 1, 1)  # NOQA

            print("==>", command)
            ret = subprocess.check_call(command, shell=True)
            if ret != 0:  # failed deployment
                raise Exception("Failed deployment")
        print("Successful deployment")
        new_deploy = datetime.now()
        # Store timestamp of successful deployment
        with codecs.open(timestamp_path, 'wb+', 'utf8') as outf:
            outf.write(repr(new_deploy))
        # Here is where we would do things with whatever is
        # on self.site.timeline and is newer than
        # last_deploy
