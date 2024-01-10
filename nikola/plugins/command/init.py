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

"""Create a new site."""

import datetime
import io
import json
import os
import shutil
import textwrap
import unidecode
from urllib.parse import urlsplit, urlunsplit

import dateutil.tz
import dateutil.zoneinfo
from mako.template import Template
from pkg_resources import resource_filename

import nikola
from nikola.nikola import DEFAULT_INDEX_READ_MORE_LINK, DEFAULT_FEED_READ_MORE_LINK, LEGAL_VALUES
from nikola.plugin_categories import Command
from nikola.utils import ask, ask_yesno, get_logger, makedirs, load_messages
from nikola.packages.tzlocal import get_localzone


LOGGER = get_logger('init')

SAMPLE_CONF = {
    'BLOG_AUTHOR': "Your Name",
    'BLOG_TITLE': "Demo Site",
    'SITE_URL': "https://example.com/",
    'BLOG_EMAIL': "joe@demo.site",
    'BLOG_DESCRIPTION': "This is a demo site for Nikola.",
    'PRETTY_URLS': True,
    'STRIP_INDEXES': True,
    'DEFAULT_LANG': "en",
    'TRANSLATIONS': """{
    DEFAULT_LANG: "",
    # Example for another language:
    # "es": "./es",
}""",
    'THEME': LEGAL_VALUES['DEFAULT_THEME'],
    'TIMEZONE': 'UTC',
    'COMMENT_SYSTEM': 'disqus',
    'COMMENT_SYSTEM_ID': 'nikolademo',
    'CATEGORY_ALLOW_HIERARCHIES': False,
    'CATEGORY_OUTPUT_FLAT_HIERARCHY': False,
    'INDEX_READ_MORE_LINK': DEFAULT_INDEX_READ_MORE_LINK,
    'FEED_READ_MORE_LINK': DEFAULT_FEED_READ_MORE_LINK,
    'POSTS': """(
    ("posts/*.rst", "posts", "post.tmpl"),
    ("posts/*.md", "posts", "post.tmpl"),
    ("posts/*.txt", "posts", "post.tmpl"),
    ("posts/*.html", "posts", "post.tmpl"),
)""",
    'PAGES': """(
    ("pages/*.rst", "pages", "page.tmpl"),
    ("pages/*.md", "pages", "page.tmpl"),
    ("pages/*.txt", "pages", "page.tmpl"),
    ("pages/*.html", "pages", "page.tmpl"),
)""",
    'COMPILERS': """{
    "rest": ['.rst', '.txt'],
    "markdown": ['.md', '.mdown', '.markdown'],
    "textile": ['.textile'],
    "txt2tags": ['.t2t'],
    "bbcode": ['.bb'],
    "wiki": ['.wiki'],
    "ipynb": ['.ipynb'],
    "html": ['.html', '.htm'],
    # PHP files are rendered the usual way (i.e. with the full templates).
    # The resulting files have .php extensions, making it possible to run
    # them without reconfiguring your server to recognize them.
    "php": ['.php'],
    # Pandoc detects the input from the source filename
    # but is disabled by default as it would conflict
    # with many of the others.
    # "pandoc": ['.rst', '.md', '.txt'],
}""",
    'NAVIGATION_LINKS': """{
    DEFAULT_LANG: (
        ("/archive.html", "Archives"),
        ("/categories/index.html", "Tags"),
        ("/rss.xml", "RSS feed"),
    ),
}""",
    'REDIRECTIONS': [],
    '_METADATA_MAPPING_FORMATS': ', '.join(LEGAL_VALUES['METADATA_MAPPING'])
}


# Generate a list of supported languages here.
# Ugly code follows.
_suplang = {}
_sllength = 0

for k, v in LEGAL_VALUES['TRANSLATIONS'].items():
    if not isinstance(k, tuple):
        main = k
        _suplang[main] = v
    else:
        main = k[0]
        k = k[1:]
        bad = []
        good = []
        for i in k:
            if i.startswith('!'):
                bad.append(i[1:])
            else:
                good.append(i)
        different = ''
        if good or bad:
            different += ' ['
        if good:
            different += 'ALTERNATIVELY ' + ', '.join(good)
        if bad:
            if good:
                different += '; '
            different += 'NOT ' + ', '.join(bad)
        if good or bad:
            different += ']'
        _suplang[main] = v + different

    if len(main) > _sllength:
        _sllength = len(main)

_sllength = str(_sllength)
suplang = (u'# {0:<' + _sllength + u'}  {1}\n').format('en', 'English')
del _suplang['en']
for k, v in sorted(_suplang.items()):
    suplang += (u'# {0:<' + _sllength + u'}  {1}\n').format(k, v)

SAMPLE_CONF['_SUPPORTED_LANGUAGES'] = suplang.strip()

# Generate a list of supported comment systems here.

SAMPLE_CONF['_SUPPORTED_COMMENT_SYSTEMS'] = '\n'.join(textwrap.wrap(
    u', '.join(LEGAL_VALUES['COMMENT_SYSTEM']),
    initial_indent=u'#   ', subsequent_indent=u'#   ', width=79))


def format_default_translations_config(additional_languages):
    """Adapt TRANSLATIONS setting for all additional languages."""
    if not additional_languages:
        return SAMPLE_CONF["TRANSLATIONS"]
    lang_paths = ['    DEFAULT_LANG: "",']
    for lang in sorted(additional_languages):
        lang_paths.append('    "{0}": "./{0}",'.format(lang))
    return "{{\n{0}\n}}".format("\n".join(lang_paths))


def get_default_translations_dict(default_lang, additional_languages):
    """Generate a TRANSLATIONS dict matching the config from 'format_default_translations_config'."""
    tr = {default_lang: ''}
    for l in additional_languages:
        tr[l] = './' + l
    return tr


def format_navigation_links(additional_languages, default_lang, messages, strip_indexes=False):
    """Return the string to configure NAVIGATION_LINKS."""
    f = u"""\
    {0}: (
        ("{1}/archive.html", "{2[Archive]}"),
        ("{1}/categories/{3}", "{2[Tags]}"),
        ("{1}/rss.xml", "{2[RSS feed]}"),
    ),"""

    pairs = []

    def get_msg(lang):
        """Generate a smaller messages dict with fallback."""
        fmsg = {}
        for i in (u'Archive', u'Tags', u'RSS feed'):
            if messages[lang][i]:
                fmsg[i] = messages[lang][i]
            else:
                fmsg[i] = i
        return fmsg

    if strip_indexes:
        index_html = ''
    else:
        index_html = 'index.html'

    # handle the default language
    pairs.append(f.format('DEFAULT_LANG', '', get_msg(default_lang), index_html))

    for l in additional_languages:
        pairs.append(f.format(json.dumps(l, ensure_ascii=False), '/' + l, get_msg(l), index_html))

    return u'{{\n{0}\n}}'.format('\n\n'.join(pairs))


# In order to ensure proper escaping, all variables but the pre-formatted ones
# are handled by json.dumps().
def prepare_config(config):
    """Parse sample config with JSON."""
    p = config.copy()
    p.update({k: json.dumps(v, ensure_ascii=False) for k, v in p.items()
             if k not in ('POSTS', 'PAGES', 'COMPILERS', 'TRANSLATIONS', 'NAVIGATION_LINKS', '_SUPPORTED_LANGUAGES', '_SUPPORTED_COMMENT_SYSTEMS', 'INDEX_READ_MORE_LINK', 'FEED_READ_MORE_LINK', '_METADATA_MAPPING_FORMATS')})
    # READ_MORE_LINKs require some special treatment.
    p['INDEX_READ_MORE_LINK'] = "'" + p['INDEX_READ_MORE_LINK'].replace("'", "\\'") + "'"
    p['FEED_READ_MORE_LINK'] = "'" + p['FEED_READ_MORE_LINK'].replace("'", "\\'") + "'"
    # fix booleans and None
    p.update({k: str(v) for k, v in config.items() if isinstance(v, bool) or v is None})
    return p


def test_destination(destination, demo=False):
    """Check if the destination already exists, which can break demo site creation."""
    # Issue #2214
    if demo and os.path.exists(destination):
        LOGGER.warning("The directory {0} already exists, and a new demo site cannot be initialized in an existing directory.".format(destination))
        LOGGER.warning("Please remove the directory and try again, or use another directory.")
        LOGGER.info("Hint: If you want to initialize a git repository in this directory, run `git init` in the directory after creating a Nikola site.")
        return False
    else:
        return True


class CommandInit(Command):
    """Create a new site."""

    name = "init"

    doc_usage = "[--demo] [--quiet] folder"
    needs_config = False
    doc_purpose = "create a Nikola site in the specified folder"
    cmd_options = [
        {
            'name': 'quiet',
            'long': 'quiet',
            'short': 'q',
            'default': False,
            'type': bool,
            'help': "Do not ask questions about config.",
        },
        {
            'name': 'demo',
            'long': 'demo',
            'short': 'd',
            'default': False,
            'type': bool,
            'help': "Create a site filled with example data.",
        }
    ]

    @classmethod
    def copy_sample_site(cls, target):
        """Copy sample site data to target directory."""
        src = resource_filename('nikola', os.path.join('data', 'samplesite'))
        shutil.copytree(src, target)

    @staticmethod
    def create_configuration(target):
        """Create configuration file."""
        template_path = resource_filename('nikola', 'conf.py.in')
        conf_template = Template(filename=template_path)
        conf_path = os.path.join(target, 'conf.py')
        with io.open(conf_path, 'w+', encoding='utf8') as fd:
            fd.write(conf_template.render(**prepare_config(SAMPLE_CONF)))

    @staticmethod
    def create_configuration_to_string():
        """Return configuration file as a string."""
        template_path = resource_filename('nikola', 'conf.py.in')
        conf_template = Template(filename=template_path)
        return conf_template.render(**prepare_config(SAMPLE_CONF))

    @classmethod
    def create_empty_site(cls, target):
        """Create an empty site with directories only."""
        for folder in ('files', 'galleries', 'images', 'listings', 'posts', 'pages'):
            makedirs(os.path.join(target, folder))

    @staticmethod
    def ask_questions(target, demo=False):
        """Ask some questions about Nikola."""
        def urlhandler(default, toconf):
            answer = ask('Site URL', 'https://example.com/')
            try:
                answer = answer.decode('utf-8')
            except (AttributeError, UnicodeDecodeError):
                pass
            if not answer.startswith(u'http'):
                print("    ERROR: You must specify a protocol (http or https).")
                urlhandler(default, toconf)
                return
            if not answer.endswith('/'):
                print("    The URL does not end in '/' -- adding it.")
                answer += '/'

            dst_url = urlsplit(answer)
            try:
                dst_url.netloc.encode('ascii')
            except (UnicodeEncodeError, UnicodeDecodeError):
                # The IDN contains characters beyond ASCII.  We must convert it
                # to Punycode. (Issue #1644)
                nl = dst_url.netloc.encode('idna')
                answer = urlunsplit((dst_url.scheme,
                                     nl,
                                     dst_url.path,
                                     dst_url.query,
                                     dst_url.fragment))
                print("    Converting to Punycode:", answer)

            SAMPLE_CONF['SITE_URL'] = answer

        def prettyhandler(default, toconf):
            SAMPLE_CONF['PRETTY_URLS'] = ask_yesno('Enable pretty URLs (/page/ instead of /page.html) that don\'t need web server configuration?', default=True)

        def lhandler(default, toconf, show_header=True):
            if show_header:
                print("We will now ask you to provide the list of languages you want to use.")
                print("Please list all the desired languages, comma-separated, using ISO 639-1 codes.  The first language will be used as the default.")
                print("Type '?' (a question mark, sans quotes) to list available languages.")
            answer = ask('Language(s) to use', 'en')
            while answer.strip() == '?':
                print('\n# Available languages:')
                try:
                    print(SAMPLE_CONF['_SUPPORTED_LANGUAGES'] + '\n')
                except UnicodeEncodeError:
                    # avoid Unicode characters in supported language names
                    print(unidecode.unidecode(SAMPLE_CONF['_SUPPORTED_LANGUAGES']) + '\n')
                answer = ask('Language(s) to use', 'en')

            langs = [i.strip().lower().replace('-', '_') for i in answer.split(',')]
            for partial, full in LEGAL_VALUES['_TRANSLATIONS_WITH_COUNTRY_SPECIFIERS'].items():
                if partial in langs:
                    langs[langs.index(partial)] = full
                    print("NOTICE: Assuming '{0}' instead of '{1}'.".format(full, partial))

            default = langs.pop(0)
            SAMPLE_CONF['DEFAULT_LANG'] = default
            # format_default_translations_config() is intelligent enough to
            # return the current value if there are no additional languages.
            SAMPLE_CONF['TRANSLATIONS'] = format_default_translations_config(langs)

            # Get messages for navigation_links.  In order to do this, we need
            # to generate a throwaway TRANSLATIONS dict.
            tr = get_default_translations_dict(default, langs)

            # Assuming that base contains all the locales, and that base does
            # not inherit from anywhere.
            try:
                messages = load_messages(['base'], tr, default, themes_dirs=['themes'])
                SAMPLE_CONF['NAVIGATION_LINKS'] = format_navigation_links(langs, default, messages, SAMPLE_CONF['STRIP_INDEXES'])
            except nikola.utils.LanguageNotFoundError as e:
                print("    ERROR: the language '{0}' is not supported.".format(e.lang))
                print("    Are you sure you spelled the name correctly?  Names are case-sensitive and need to be reproduced as-is (complete with the country specifier, if any).")
                print("\nType '?' (a question mark, sans quotes) to list available languages.")
                lhandler(default, toconf, show_header=False)

        def tzhandler(default, toconf):
            print("\nPlease choose the correct time zone for your blog. Nikola uses the tz database.")
            print("You can find your time zone here:")
            print("https://en.wikipedia.org/wiki/List_of_tz_database_time_zones")
            print("")
            answered = False
            while not answered:
                try:
                    lz = get_localzone()
                except Exception:
                    lz = None
                answer = ask('Time zone', lz if lz else "UTC")
                tz = dateutil.tz.gettz(answer)

                if tz is None:
                    print("    WARNING: Time zone not found.  Searching list of time zones for a match.")
                    all_zones = dateutil.zoneinfo.get_zonefile_instance().zones
                    matching_zones = [zone for zone in all_zones if answer.lower() in zone.lower()]
                    if len(matching_zones) == 1:
                        tz = dateutil.tz.gettz(matching_zones[0])
                        answer = matching_zones[0]
                        print("    Picking '{0}'.".format(answer))
                    elif len(matching_zones) > 1:
                        print("    The following time zones match your query:")
                        print('        ' + '\n        '.join(matching_zones))
                        continue

                if tz is not None:
                    time = datetime.datetime.now(tz).strftime('%H:%M:%S')
                    print("    Current time in {0}: {1}".format(answer, time))
                    answered = ask_yesno("Use this time zone?", True)
                else:
                    print("    ERROR: No matches found.  Please try again.")

            SAMPLE_CONF['TIMEZONE'] = answer

        def chandler(default, toconf):
            print("You can configure comments now.  Type '?' (a question mark, sans quotes) to list available comment systems.  If you do not want any comments, just leave the field blank.")
            answer = ask('Comment system', '')
            while answer.strip() == '?':
                print('\n# Available comment systems:')
                print(SAMPLE_CONF['_SUPPORTED_COMMENT_SYSTEMS'])
                print('')
                answer = ask('Comment system', '')

            while answer and answer not in LEGAL_VALUES['COMMENT_SYSTEM']:
                if answer != '?':
                    print('    ERROR: Nikola does not know this comment system.')
                print('\n# Available comment systems:')
                print(SAMPLE_CONF['_SUPPORTED_COMMENT_SYSTEMS'])
                print('')
                answer = ask('Comment system', '')

            SAMPLE_CONF['COMMENT_SYSTEM'] = answer
            SAMPLE_CONF['COMMENT_SYSTEM_ID'] = ''

            if answer:
                print("You need to provide the site identifier for your comment system.  Consult the Nikola manual for details on what the value should be.  (you can leave it empty and come back later)")
                answer = ask('Comment system site identifier', '')
                SAMPLE_CONF['COMMENT_SYSTEM_ID'] = answer

        STORAGE = {'target': target}

        questions = [
            ('Questions about the site', None, None, None),
            # query, default, toconf, destination
            ('Destination', None, False, '!target'),
            ('Site title', 'My Nikola Site', True, 'BLOG_TITLE'),
            ('Site author', 'Nikola Tesla', True, 'BLOG_AUTHOR'),
            ('Site author\'s e-mail', 'n.tesla@example.com', True, 'BLOG_EMAIL'),
            ('Site description', 'This is a demo site for Nikola.', True, 'BLOG_DESCRIPTION'),
            (urlhandler, None, True, True),
            (prettyhandler, None, True, True),
            ('Questions about languages and locales', None, None, None),
            (lhandler, None, True, True),
            (tzhandler, None, True, True),
            ('Questions about comments', None, None, None),
            (chandler, None, True, True),
        ]

        print("Creating Nikola Site")
        print("====================\n")
        print("This is Nikola v{0}.  We will now ask you a few easy questions about your new site.".format(nikola.__version__))
        print("If you do not want to answer and want to go with the defaults instead, simply restart with the `-q` parameter.")

        for query, default, toconf, destination in questions:
            if target and destination == '!target' and test_destination(target, demo):
                # Skip the destination question if we know it already
                pass
            else:
                if default is toconf is destination is None:
                    print('--- {0} ---'.format(query))
                elif destination is True:
                    query(default, toconf)
                else:
                    answer = ask(query, default)
                    try:
                        answer = answer.decode('utf-8')
                    except (AttributeError, UnicodeDecodeError):
                        pass
                    if toconf:
                        SAMPLE_CONF[destination] = answer
                    if destination == '!target':
                        while not answer or not test_destination(answer, demo):
                            if not answer:
                                print('    ERROR: you need to specify a target directory.\n')
                            answer = ask(query, default)
                        STORAGE['target'] = answer

        print("\nThat's it, Nikola is now configured.  Make sure to edit conf.py to your liking.")
        print("If you are looking for themes and addons, check out https://themes.getnikola.com/ and https://plugins.getnikola.com/.")
        print("Have fun!")
        return STORAGE

    def _execute(self, options={}, args=None):
        """Create a new site."""
        try:
            target = args[0]
        except IndexError:
            target = None
        if not options.get('quiet'):
            st = self.ask_questions(target=target, demo=options.get('demo'))
            try:
                if not target:
                    target = st['target']
            except KeyError:
                pass

        if not target:
            print("Usage: nikola init [--demo] [--quiet] folder")
            print("""
Options:
  -q, --quiet               Do not ask questions about config.
  -d, --demo                Create a site filled with example data.""")
            return 1
        if not options.get('demo'):
            self.create_empty_site(target)
            LOGGER.info('Created empty site at {0}.'.format(target))
        else:
            if not test_destination(target, True):
                return 2
            self.copy_sample_site(target)
            LOGGER.info("A new site with example data has been created at "
                        "{0}.".format(target))
            LOGGER.info("See README.txt in that folder for more information.")

        self.create_configuration(target)
