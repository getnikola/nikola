# This file is public domain according to its author, Brian Hsu

from docutils.parsers.rst import Directive, directives
from docutils import nodes

try:
    import requests
except ImportError:
    requests = None  # NOQA


class GitHubGist(Directive):
    """ Embed GitHub Gist.

        Usage:
          .. gist:: GIST_ID

    """

    required_arguments = 1
    optional_arguments = 1
    option_spec = {'file': directives.unchanged}
    final_argument_whitespace = True
    has_content = False

    def get_raw_gist_with_filename(self, gistID, filename):
        url = '/'.join(("https://raw.github.com/gist", gistID, filename))
        return requests.get(url).text

    def get_raw_gist(self, gistID):
        url = "https://raw.github.com/gist/{0}".format(gistID)
        return requests.get(url).text

    def run(self):
        if requests is None:
            print('To use the gist directive, you need to install the '
                  '"requests" package.')
            return []
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

        return [nodes.raw('', embedHTML, format='html'),
                nodes.raw('', '<noscript>', format='html'),
                nodes.literal_block('', rawGist),
                nodes.raw('', '</noscript>', format='html')]
