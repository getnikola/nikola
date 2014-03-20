# -*- coding: utf-8 -*-

# Copyright © 2012-2014 Roberto Alsina and others.

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
import os
import sys
import shutil
import codecs
import json

from mako.template import Template

import nikola
from nikola.nikola import DEFAULT_TRANSLATIONS_PATTERN
from nikola.plugin_categories import Command
from nikola.utils import get_logger, makedirs, STDERR_HANDLER, load_messages
from nikola.winutils import fix_git_symlinked

LOGGER = get_logger('init', STDERR_HANDLER)

SAMPLE_CONF = {
    'BLOG_AUTHOR': "Your Name",
    'BLOG_TITLE': "Demo Site",
    'SITE_URL': "http://getnikola.com/",
    'BLOG_EMAIL': "joe@demo.site",
    'BLOG_DESCRIPTION': "This is a demo site for Nikola.",
    'DEFAULT_LANG': "en",
    'TRANSLATIONS': """{
    DEFAULT_LANG: "",
    # Example for another language:
    # "es": "./es",
}""",
    'THEME': 'bootstrap3',
    'COMMENT_SYSTEM': 'disqus',
    'COMMENT_SYSTEM_ID': 'nikolademo',
    'TRANSLATIONS_PATTERN': DEFAULT_TRANSLATIONS_PATTERN,
    'POSTS': """(
    ("posts/*.rst", "posts", "post.tmpl"),
    ("posts/*.txt", "posts", "post.tmpl"),
)""",
    'PAGES': """(
    ("stories/*.rst", "stories", "story.tmpl"),
    ("stories/*.txt", "stories", "story.tmpl"),
)""",
    'COMPILERS': """{
    "rest": ('.rst', '.txt'),
    "markdown": ('.md', '.mdown', '.markdown'),
    "textile": ('.textile',),
    "txt2tags": ('.t2t',),
    "bbcode": ('.bb',),
    "wiki": ('.wiki',),
    "ipynb": ('.ipynb',),
    "html": ('.html', '.htm'),
    # PHP files are rendered the usual way (i.e. with the full templates).
    # The resulting files have .php extensions, making it possible to run
    # them without reconfiguring your server to recognize them.
    "php": ('.php',),
    # Pandoc detects the input from the source filename
    # but is disabled by default as it would conflict
    # with many of the others.
    # "pandoc": ('.rst', '.md', '.txt'),
}""",
    'NAVIGATION_LINKS': """{
    DEFAULT_LANG: (
        ("/archive.html", "Archives"),
        ("/categories/index.html", "Tags"),
        ("/rss.xml", "RSS feed"),
    ),
}""",
    'REDIRECTIONS': [],
}


def format_default_translations_config(additional_languages):
    """Return the string to configure the TRANSLATIONS config variable to
    make each additional language visible on the generated site."""
    if not additional_languages:
        return SAMPLE_CONF["TRANSLATIONS"]
    lang_paths = ['    DEFAULT_LANG: "",']
    for lang in sorted(additional_languages):
        lang_paths.append('    "{0}": "./{0}",'.format(lang))
    return "{{\n{0}\n}}".format("\n".join(lang_paths))


def format_navigation_links(additional_languages, default_lang, messages):
    """Return the string to configure NAVIGATION_LINKS."""
    f = u"""\
    {0}: (
        ("{1}/archive.html", "{2[Archive]}"),
        ("{1}/categories/index.html", "{2[Tags]}"),
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

    # handle the default language
    pairs.append(f.format('DEFAULT_LANG', '', get_msg(default_lang)))

    for l in additional_languages:
        pairs.append(f.format(json.dumps(l), '/' + l, get_msg(l)))

    return u'{{\n{0}\n}}'.format('\n\n'.join(pairs))


# In order to ensure proper escaping, all variables but the three
# pre-formatted ones are handled by json.dumps().
def prepare_config(config):
    """Parse sample config with JSON."""
    p = config.copy()
    p.update(dict((k, json.dumps(v)) for k, v in p.items()
             if k not in ('POSTS', 'PAGES', 'COMPILERS', 'TRANSLATIONS', 'NAVIGATION_LINKS')))
    return p


class CommandInit(Command):

    """Create a new site."""

    name = "init"

    doc_usage = "[--demo] folder"
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
        lib_path = cls.get_path_to_nikola_modules()
        src = os.path.join(lib_path, 'data', 'samplesite')
        shutil.copytree(src, target)
        fix_git_symlinked(src, target)

    @classmethod
    def create_configuration(cls, target):
        lib_path = cls.get_path_to_nikola_modules()
        template_path = os.path.join(lib_path, 'conf.py.in')
        conf_template = Template(filename=template_path)
        conf_path = os.path.join(target, 'conf.py')
        with codecs.open(conf_path, 'w+', 'utf8') as fd:
            fd.write(conf_template.render(**prepare_config(SAMPLE_CONF)))

    @classmethod
    def create_empty_site(cls, target):
        for folder in ('files', 'galleries', 'listings', 'posts', 'stories'):
            makedirs(os.path.join(target, folder))

    @staticmethod
    def get_path_to_nikola_modules():
        return os.path.dirname(nikola.__file__)

    @staticmethod
    def ask_questions(target):
        """Ask some questions about Nikola."""
        def ask(query, default):
            """Ask a question."""
            if default:
                default_q = ' [{0}]'.format(default)
            else:
                default_q = ''
            # Stolen from new_post.
            print("{query}{default_q}: ".format(query=query, default_q=default_q), end='')
            # WHY, PYTHON3???? WHY?
            sys.stdout.flush()
            inp = sys.stdin.readline().strip()
            return inp if inp else default

        def lhandler(default, toconf):
            print("We will now ask you to provide the list of languages you want to use.")
            print("Please list all the desired languages, comma-separated.  The first language will be used as the default.")
            answer = ask('Language(s) to use', 'en')
            langs = answer.split(',')
            default = langs.pop(0)
            SAMPLE_CONF['DEFAULT_LANG'] = default
            # format_default_translations_config() is intelligent enough to
            # return the current value if there are no additional languages.
            SAMPLE_CONF['TRANSLATIONS'] = format_default_translations_config(langs)

            # Get messages for navigation_links.  In order to do this, we need
            # to generate a throwaway TRANSLATIONS dict.
            tr = {default: ''}
            for l in langs:
                tr[l] = './' + l
            # Assuming that base contains all the locales, and that base does
            # not inherit from anywhere.
            messages = nikola.utils.load_messages(['base'], tr, default)
            SAMPLE_CONF['NAVIGATION_LINKS'] = format_navigation_links(langs, default, messages)

        def chandler(default, toconf):
            print("You can configure comments now.  Consult the manual if you want to know what is available.  If you do not want any comments, just leave the fields blank.")

        STORAGE = {'target': target}

        questions = [
            ('Questions about the site', None, None, None),
            # query, default, toconf, destination
            ('Destination', None, False, '!target'),
            ('Site title', 'My Nikola Site', True, 'BLOG_TITLE'),
            ('Site author', 'Nikola Tesla', True, 'BLOG_AUTHOR'),
            ('Site author’s e-mail', 'n.tesla@example.com', True, 'BLOG_EMAIL'),
            ('Site description', 'This is a demo site for Nikola.', True, 'BLOG_DESCRIPTION'),
            ('Site URL', 'http://getnikola.com/', True, 'SITE_URL'),
            ('Questions about languages and locales', None, None, None),
            (lhandler, None, True, True),
            ('Questions about comments', None, None, None),
            (chandler, None, True, True),
            ('Comment system', '', True, 'COMMENT_SYSTEM'),
            ('Comment system site identifier', '', True, 'COMMENT_SYSTEM_ID'),
        ]

        print("Creating Nikola Site")
        print("====================\n")
        print("This is Nikola v{0}.  We will now ask you a few easy questions about your new site.".format(nikola.__version__))
        print("If you do not want to answer and want to go with the defaults instead, simply restart with the `-q` parameter.")


        for query, default, toconf, destination in questions:
            if target and destination == '!target':
                # Skip the destination question if we know it already
                pass
            else:
                if default is toconf is destination is None:
                    print('--- {0} ---'.format(query))
                elif destination is True:
                    query(default, toconf)
                else:
                    answer = ask(query, default)
                    if toconf:
                        SAMPLE_CONF[destination] = answer
                    if destination == '!target':
                        while not answer:
                            print('ERROR: directory missing.')
                            answer = ask(query, default)
                        STORAGE['target'] = answer

        print("That's it, Nikola is now configured.")
        print("Make sure to edit conf.py to your liking.")
        return STORAGE

    def _execute(self, options={}, args=None):
        """Create a new site."""
        try:
            target = args[0]
        except IndexError:
            target = None
        if not options.get('quiet'):
            st = self.ask_questions(target=target)
            try:
                target = st['target']
            except KeyError:
                pass

        if not target:
            print("Usage: nikola init [options] folder")
            return False
        if not options.get('demo'):
            self.create_empty_site(target)
            LOGGER.info('Created empty site at {0}.'.format(target))
        else:
            self.copy_sample_site(target)
            LOGGER.info("A new site with example data has been created at "
                        "{0}.".format(target))
            LOGGER.info("See README.txt in that folder for more information.")

        self.create_configuration(target)
