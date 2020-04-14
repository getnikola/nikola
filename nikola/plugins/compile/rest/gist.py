# -*- coding: utf-8 -*-
# This file is public domain according to its author, Brian Hsu

"""Gist directive for reStructuredText."""

import requests
from docutils.parsers.rst import Directive, directives
from docutils import nodes

from nikola.plugin_categories import RestExtension


class Plugin(RestExtension):
    """Plugin for gist directive."""

    name = "rest_gist"

    def set_site(self, site):
        """Set Nikola site."""
        self.site = site
        directives.register_directive('gist', GitHubGist)
        return super().set_site(site)


class GitHubGist(Directive):
    """Embed GitHub Gist.

    Usage:

      .. gist:: GIST_ID

    or

      .. gist:: GIST_URL
    """

    required_arguments = 1
    optional_arguments = 1
    option_spec = {'file': directives.unchanged}
    final_argument_whitespace = True
    has_content = False

    def get_raw_gist_with_filename(self, gistID, filename):
        """Get raw gist text for a filename."""
        url = '/'.join(("https://gist.github.com/raw", gistID, filename))
        return requests.get(url).text

    def get_raw_gist(self, gistID):
        """Get raw gist text."""
        url = "https://gist.github.com/raw/{0}".format(gistID)
        try:
            return requests.get(url).text
        except requests.exceptions.RequestException:
            raise self.error('Cannot get gist for url={0}'.format(url))

    def run(self):
        """Run the gist directive."""
        if 'https://' in self.arguments[0]:
            gistID = self.arguments[0].split('/')[-1].strip()
        else:
            gistID = self.arguments[0].strip()
        embedHTML = ""
        rawGist = ""

        if 'file' in self.options:
            filename = self.options['file']
            rawGist = (self.get_raw_gist_with_filename(gistID, filename))
            embedHTML = ('<script src="https://gist.github.com/{0}.js'
                         '?file={1}"></script>').format(gistID, filename)
        else:
            rawGist = (self.get_raw_gist(gistID))
            embedHTML = ('<script src="https://gist.github.com/{0}.js">'
                         '</script>').format(gistID)

        reqnode = nodes.literal_block('', rawGist)

        return [nodes.raw('', embedHTML, format='html'),
                nodes.raw('', '<noscript>', format='html'),
                reqnode,
                nodes.raw('', '</noscript>', format='html')]
