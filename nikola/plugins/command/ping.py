# -*- coding: utf-8 -*-

# Copyright © 2012-2013 Roberto Alsina and others.

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
import sys

from nikola.plugin_categories import Command
from nikola.utils import remove_file, get_logger

class Ping(Command):
    """Ping site updates.  """
    name = "ping"

    doc_usage = ""
    doc_purpose = "ping services with updates to the live site"

    logger = None

    def _execute(self, command, args):
        self.logger = get_logger('ping', self.site.loghandlers)

        blog_title = self.site.config['BLOG_TITLE']
        site_url = self.site.config['SITE_URL']

        if sys.version_info[0] == 2:
            import xmlrpclib as ping_xmlclient
            import urllib2 as ping_browser
        elif sys.version_info[0] >= 3:
            import xmlrpc.client as ping_xmlclient
            import urllib.request as ping_browser

        for xmlrpc_service in self.site.config['PING_XMLRPC_SERVICES']:
            self.logger.notice("==> XML-RPC service: {0}".format(xmlrpc_service))

            try:
                ping_xmlclient.ServerProxy(xmlrpc_service).weblogUpdates.ping(blog_title, site_url)
            except ping_xmlclient.ProtocolError as e:
                self.logger.warn("Unsuccessfully pinged service {0}: [{1}] {2}".format(xmlrpc_service, e.errcode, e.errmsg))
            except Exception as e:
                self.logger.warn("Unknown problem while pinging service {0}: {1}".format(xmlrpc_service, e))

        for web_service in self.site.config['PING_GET_SERVICES']:
            self.logger.notice("==> HTTP GET service: {0}".format(web_service))

            try:
                ping_browser.urlopen(web_service).read()
            except Exception as e:
                self.logger.warn("Unknown problem while pinging service {0}: {1}".format(web_service, e))

        self.logger.notice("Pinged all services")

