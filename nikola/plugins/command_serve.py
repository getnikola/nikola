from optparse import OptionParser
import os
from BaseHTTPServer import HTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler

from nikola.plugin_categories import Command


class CommandBuild(Command):
    """Start test server."""

    name = "serve"

    def run(self, *args):
        """Start test server."""

        parser = OptionParser()
        parser.add_option("-p", "--port", dest="port",
            help="Port numer (default: 8000)", default=8000,
            type="int")
        parser.add_option("-a", "--address", dest="address",
            help="Address to bind (default: 127.0.0.1)",
            default='127.0.0.1')
        (options, args) = parser.parse_args(list(args))

        out_dir = self.site.config['OUTPUT_FOLDER']
        if not os.path.isdir(out_dir):
            print "Error: Missing '%s' folder?" % out_dir
        else:
            os.chdir(out_dir)
            httpd = HTTPServer((options.address, options.port),
                OurHTTPRequestHandler)
            sa = httpd.socket.getsockname()
            print "Serving HTTP on", sa[0], "port", sa[1], "..."
            httpd.serve_forever()


class OurHTTPRequestHandler(SimpleHTTPRequestHandler):
    extensions_map = dict(SimpleHTTPRequestHandler.extensions_map)
    extensions_map[""] = "text/plain"
