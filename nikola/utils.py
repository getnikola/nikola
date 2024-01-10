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

"""Utility functions."""

import configparser
import datetime
import hashlib
import io
import lxml.html
import operator
import os
import re
import json
import shutil
import socket
import subprocess
import sys
import threading
import typing
from collections import defaultdict, OrderedDict
from collections.abc import Callable, Iterable
from html import unescape as html_unescape
from importlib import reload as _reload
from unicodedata import normalize as unicodenormalize
from urllib.parse import quote as urlquote
from urllib.parse import unquote as urlunquote
from urllib.parse import urlparse, urlunparse
from zipfile import ZipFile as zipf

import babel.dates
import dateutil.parser
import dateutil.tz
import pygments.formatters
import pygments.formatters._mapping
import PyRSS2Gen as rss
from blinker import signal
from doit import tools
from doit.cmdparse import CmdParse
from pkg_resources import resource_filename
from nikola.packages.pygments_better_html import BetterHtmlFormatter
from typing import List
from unidecode import unidecode

# Renames
from nikola import DEBUG  # NOQA
from .log import LOGGER, get_logger  # NOQA
from .hierarchy_utils import TreeNode, clone_treenode, flatten_tree_structure, sort_classifications
from .hierarchy_utils import join_hierarchical_category_path, parse_escaped_hierarchical_category_name

try:
    import toml
except ImportError:
    toml = None

try:
    from ruamel.yaml import YAML
except ImportError:
    YAML = None

try:
    import hsluv
except ImportError:
    hsluv = None

__all__ = ('CustomEncoder', 'get_theme_path', 'get_theme_path_real',
           'get_theme_chain', 'load_messages', 'copy_tree', 'copy_file',
           'slugify', 'unslugify', 'to_datetime', 'apply_filters',
           'config_changed', 'get_crumbs', 'get_tzname', 'get_asset_path',
           '_reload', 'Functionary', 'TranslatableSetting',
           'TemplateHookRegistry', 'LocaleBorg',
           'sys_encode', 'sys_decode', 'makedirs', 'get_parent_theme_name',
           'demote_headers', 'get_translation_candidate', 'write_metadata',
           'ask', 'ask_yesno', 'options2docstring', 'os_path_split',
           'get_displayed_page_number', 'adjust_name_for_index_path_list',
           'adjust_name_for_index_path', 'adjust_name_for_index_link',
           'NikolaPygmentsHTML', 'create_redirect', 'clean_before_deployment',
           'sort_posts', 'smartjoin', 'indent', 'load_data', 'html_unescape',
           'rss_writer', 'map_metadata', 'req_missing', 'bool_from_meta',
           # Deprecated, moved to hierarchy_utils:
           'TreeNode', 'clone_treenode', 'flatten_tree_structure',
           'sort_classifications', 'join_hierarchical_category_path',
           'parse_escaped_hierarchical_category_name',)

# Are you looking for 'generic_rss_renderer'?
# It's defined in nikola.nikola.Nikola (the site object).

# Aliases, previously for Python 2/3 compatibility.
# TODO remove in v9
bytes_str = bytes
unicode_str = str
unichr = chr

# For compatibility with old logging setups.
# TODO remove in v9?
STDERR_HANDLER = None


USE_SLUGIFY = True


def req_missing(names, purpose, python=True, optional=False):
    """Log that we are missing some requirements.

    `names` is a list/tuple/set of missing things.
    `purpose` is a string, specifying the use of the missing things.
              It completes the sentence:
                  In order to {purpose}, you must install ...
    `python` specifies whether the requirements are Python packages
                               or other software.
    `optional` specifies whether the things are required
                                 (this is an error and we exit with code 5)
                                 or not (this is just a warning).

    Returns the message shown to the user (which you can usually discard).
    If no names are specified, False is returned and nothing is shown
    to the user.

    """
    if not (isinstance(names, tuple) or isinstance(names, list) or isinstance(names, set)):
        names = (names,)
    if not names:
        return False
    if python:
        whatarethey_s = 'Python package'
        whatarethey_p = 'Python packages'
    else:
        whatarethey_s = whatarethey_p = 'software'
    if len(names) == 1:
        msg = 'In order to {0}, you must install the "{1}" {2}.'.format(
            purpose, names[0], whatarethey_s)
    else:
        most = '", "'.join(names[:-1])
        pnames = most + '" and "' + names[-1]
        msg = 'In order to {0}, you must install the "{1}" {2}.'.format(
            purpose, pnames, whatarethey_p)

    if optional:
        LOGGER.warning(msg)
    else:
        LOGGER.error(msg)
        LOGGER.error('Exiting due to missing dependencies.')
        sys.exit(5)

    return msg


ENCODING = sys.getfilesystemencoding() or sys.stdin.encoding


def sys_encode(thing):
    """Return bytes encoded in the system's encoding."""
    if isinstance(thing, str):
        return thing.encode(ENCODING)
    return thing


def sys_decode(thing):
    """Return Unicode."""
    if isinstance(thing, bytes):
        return thing.decode(ENCODING)
    return thing


def makedirs(path):
    """Create a folder and its parents if needed (mkdir -p)."""
    if not path:
        return
    if os.path.exists(path):
        if not os.path.isdir(path):
            raise OSError('Path {0} already exists and is not a folder.'.format(path))
        else:
            return
    try:
        os.makedirs(path)
        return
    except Exception:
        if os.path.isdir(path):
            return
        raise


class Functionary(defaultdict):
    """Class that looks like a function, but is a defaultdict."""

    def __init__(self, default, default_lang):
        """Initialize a functionary."""
        super().__init__(default)
        self.default_lang = default_lang

    def __call__(self, key, lang=None):
        """When called as a function, take an optional lang and return self[lang][key]."""
        if lang is None:
            lang = LocaleBorg().current_lang
        return self[lang][key]


class TranslatableSetting(object):
    """A setting that can be translated.

    You can access it via: SETTING(lang).  You can omit lang, in which
    case Nikola will ask LocaleBorg, unless you set SETTING.lang,
    which overrides that call.

    You can also stringify the setting and you will get something
    sensible (in what LocaleBorg claims the language is, can also be
    overriden by SETTING.lang). Note that this second method is
    deprecated.  It is kept for backwards compatibility and
    safety.  It is not guaranteed.

    The underlying structure is a defaultdict.  The language that
    is the default value of the dict is provided with __init__().
    """

    # WARNING: This is generally not used and replaced with a call to
    #          LocaleBorg().  Set this to a truthy value to override that.
    lang = None

    # Note that this setting is global.  DO NOT set on a per-instance basis!
    default_lang = 'en'

    def __getattribute__(self, attr):
        """Return attributes, falling back to string attributes."""
        try:
            return super().__getattribute__(attr)
        except AttributeError:
            return self().__getattribute__(attr)

    def __dir__(self):
        """Return the available methods of TranslatableSettings and strings."""
        return list(set(self.__dict__).union(set(dir(str))))

    def __init__(self, name, inp, translations):
        """Initialize a translated setting.

        Valid inputs include:

        * a string               -- the same will be used for all languages
        * a dict ({lang: value}) -- each language will use the value specified;
                                    if there is none, default_lang is used.
        """
        self.name = name
        self._inp = inp
        self.translations = translations
        self.overriden_default = False
        self.values = defaultdict()

        if isinstance(inp, dict) and inp:
            self.translated = True
            self.values.update(inp)
            if self.default_lang not in self.values.keys():
                self.default_lang = list(self.values.keys())[0]
                self.overridden_default = True
            self.values.default_factory = lambda: self.values[self.default_lang]
            for k in translations.keys():
                if k not in self.values.keys():
                    self.values[k] = inp[self.default_lang]
        else:
            self.translated = False
            self.values[self.default_lang] = inp
            self.values.default_factory = lambda: inp

    def get_lang(self):
        """Return the language that should be used to retrieve settings."""
        if self.lang:
            return self.lang
        elif not self.translated:
            return self.default_lang
        else:
            try:
                return LocaleBorg().current_lang
            except AttributeError:
                return self.default_lang

    def __call__(self, lang=None):
        """Return the value in the requested language.

        While lang is None, self.lang (currently set language) is used.
        Otherwise, the standard algorithm is used (see above).

        """
        if lang is None:
            return self.values[self.get_lang()]
        else:
            return self.values[lang]

    def __str__(self):
        """Return the value in the currently set language (deprecated)."""
        return str(self.values[self.get_lang()])

    def __repr__(self):
        """Provide a representation for programmers."""
        return '<TranslatableSetting: {0!r} = {1!r}>'.format(self.name, self._inp)

    def format(self, *args, **kwargs):
        """Format ALL the values in the setting the same way."""
        for l in self.values:
            self.values[l] = self.values[l].format(*args, **kwargs)
        self.values.default_factory = lambda: self.values[self.default_lang]
        return self

    def langformat(self, formats):
        """Format ALL the values in the setting, on a per-language basis."""
        if not formats:
            # Input is empty.
            return self
        else:
            # This is a little tricky.
            # Basically, we have some things that may very well be dicts.  Or
            # actually, TranslatableSettings in the original unprocessed dict
            # form.  We need to detect them.

            # First off, we need to check what languages we have and what
            # should we use as the default.
            keys = list(formats)
            if self.default_lang in keys:
                d = formats[self.default_lang]
            else:
                d = formats[keys[0]]
            # Discovering languages of the settings here.
            langkeys = []
            for f in formats.values():
                for a in f[0] + tuple(f[1].values()):
                    if isinstance(a, dict):
                        langkeys += list(a)

            # Now that we know all this, we go through all the languages we have.
            allvalues = set(keys + langkeys + list(self.values))
            self.values['__orig__'] = self.values[self.default_lang]
            for l in allvalues:
                if l in keys:
                    oargs, okwargs = formats[l]
                else:
                    oargs, okwargs = d

                args = []
                kwargs = {}

                for a in oargs:
                    # We create temporary TranslatableSettings and replace the
                    # values with them.
                    if isinstance(a, dict):
                        a = TranslatableSetting('NULL', a, self.translations)
                        args.append(a(l))
                    else:
                        args.append(a)

                for k, v in okwargs.items():
                    if isinstance(v, dict):
                        v = TranslatableSetting('NULL', v, self.translations)
                        kwargs.update({k: v(l)})
                    else:
                        kwargs.update({k: v})

                if l in self.values:
                    self.values[l] = self.values[l].format(*args, **kwargs)
                else:
                    self.values[l] = self.values['__orig__'].format(*args, **kwargs)
                self.values.default_factory = lambda: self.values[self.default_lang]

        return self

    def __getitem__(self, key):
        """Provide an alternate interface via __getitem__."""
        return self.values[key]

    def __setitem__(self, key, value):
        """Set values for translations."""
        self.values[key] = value

    def __eq__(self, other):
        """Test whether two TranslatableSettings are equal."""
        try:
            return self.values == other.values
        except AttributeError:
            return self(self.default_lang) == other

    def __ne__(self, other):
        """Test whether two TranslatableSettings are inequal."""
        try:
            return self.values != other.values
        except AttributeError:
            return self(self.default_lang) != other


class TemplateHookRegistry(object):
    r"""A registry for template hooks.

    Usage:

    >>> r = TemplateHookRegistry('foo', None)
    >>> r.append('Hello!')
    >>> r.append(lambda x: 'Hello ' + x + '!', False, 'world')
    >>> repr(r())
    'Hello!\nHello world!'
    """

    def __init__(self, name, site):
        """Initialize a hook registry."""
        self._items = []
        self.name = name
        self.site = site
        self.context = None

    def generate(self):
        """Generate items."""
        for c, inp, site, args, kwargs in self._items:
            if c:
                if site:
                    kwargs['site'] = self.site
                    kwargs['context'] = self.context
                yield inp(*args, **kwargs)
            else:
                yield inp

    def __call__(self):
        """Return items, in a string, separated by newlines."""
        return '\n'.join(self.generate())

    def append(self, inp, wants_site_and_context=False, *args, **kwargs):
        """
        Register an item.

        `inp` can be a string or a callable returning one.
        `wants_site` tells whether there should be a `site` keyword
                     argument provided, for accessing the site.

        Further positional and keyword arguments are passed as-is to the
        callable.

        `wants_site`, args and kwargs are ignored (but saved!) if `inp`
        is not callable.  Callability of `inp` is determined only once.
        """
        c = callable(inp)
        self._items.append((c, inp, wants_site_and_context, args, kwargs))

    def calculate_deps(self):
        """Calculate dependencies for a registry."""
        deps = []
        for is_callable, inp, wants_site_and_context, args, kwargs in self._items:
            if not is_callable:
                name = inp
            elif hasattr(inp, 'template_registry_identifier'):
                name = inp.template_registry_identifier
            elif hasattr(inp, '__doc__'):
                name = inp.__doc__
            else:
                name = '_undefined_callable_'
            deps.append((is_callable, name, wants_site_and_context, args, kwargs))

    def __hash__(self):
        """Return hash of a registry."""
        return hash(config_changed({self.name: self.calculate_deps()})._calc_digest())

    def __str__(self):
        """Stringify a registry."""
        return '<TemplateHookRegistry: {0}>'.format(self._items)

    def __repr__(self):
        """Provide the representation of a registry."""
        return '<TemplateHookRegistry: {0}>'.format(self.name)


class CustomEncoder(json.JSONEncoder):
    """Custom JSON encoder."""

    def default(self, obj):
        """Create default encoding handler."""
        try:
            return super().default(obj)
        except TypeError:
            if isinstance(obj, (set, frozenset)):
                return self.encode(sorted(list(obj)))
            elif isinstance(obj, TranslatableSetting):
                s = json.dumps(obj._inp, cls=CustomEncoder, sort_keys=True)
            else:
                s = repr(obj).split('0x', 1)[0]
            return s


class config_changed(tools.config_changed):
    """A copy of doit's config_changed, using pickle instead of serializing manually."""

    def __init__(self, config, identifier=None):
        """Initialize config_changed."""
        super().__init__(config)
        self.identifier = '_config_changed'
        if identifier is not None:
            self.identifier += ':' + identifier

    # DEBUG (for unexpected rebuilds)
    @classmethod
    def _write_into_debug_db(cls, digest: str, data: str) -> None:  # pragma: no cover
        """Write full values of config_changed into a sqlite3 database."""
        import sqlite3
        try:
            cls.debug_db_cursor
        except AttributeError:
            cls.debug_db_conn = sqlite3.connect("cc_debug.sqlite3")
            cls.debug_db_id = datetime.datetime.now().isoformat()
            cls.debug_db_cursor = cls.debug_db_conn.cursor()
            cls.debug_db_cursor.execute("""
            CREATE TABLE IF NOT EXISTS hashes (hash CHARACTER(32) PRIMARY KEY, json_data TEXT);
            """)
            cls.debug_db_conn.commit()

        try:
            cls.debug_db_cursor.execute("INSERT INTO hashes (hash, json_data) VALUES (?, ?);", (digest, data))
            cls.debug_db_conn.commit()
        except sqlite3.IntegrityError:
            # ON CONFLICT DO NOTHING, except Ubuntu 16.04’s sqlite3 is too ancient for this
            cls.debug_db_conn.rollback()

    def _calc_digest(self):
        """Calculate a config_changed digest."""
        if isinstance(self.config, str):
            return self.config
        elif isinstance(self.config, dict):
            data = json.dumps(self.config, cls=CustomEncoder, sort_keys=True)
            if isinstance(data, str):  # pragma: no cover # python3
                byte_data = data.encode("utf-8")
            else:
                byte_data = data
            digest = hashlib.md5(byte_data).hexdigest()

            # DEBUG (for unexpected rebuilds)
            # self._write_into_debug_db(digest, data)
            # Alternative (without database):
            # LOGGER.debug('{{"{0}": {1}}}'.format(digest, byte_data))
            # Humanized format:
            # LOGGER.debug('[Digest {0} for {2}]\n{1}\n[Digest {0} for {2}]'.format(digest, byte_data, self.identifier))

            return digest
        else:
            raise Exception('Invalid type of config_changed parameter -- got '
                            '{0}, must be string or dict'.format(type(
                                self.config)))

    def configure_task(self, task):
        """Configure a task with a digest."""
        task.value_savers.append(lambda: {self.identifier: self._calc_digest()})

    def __call__(self, task, values):
        """Return True if config values are unchanged."""
        last_success = values.get(self.identifier)
        if last_success is None:
            return False
        return (last_success == self._calc_digest())

    def __repr__(self):
        """Provide a representation of config_changed."""
        return "Change with config: {0}".format(json.dumps(self.config,
                                                           cls=CustomEncoder,
                                                           sort_keys=True))


def get_theme_path_real(theme, themes_dirs):
    """Return the path where the given theme's files are located.

    Looks in ./themes and in the place where themes go when installed.
    """
    for themes_dir in themes_dirs:
        dir_name = os.path.join(themes_dir, theme)
        if os.path.isdir(dir_name):
            return dir_name
    dir_name = resource_filename('nikola', os.path.join('data', 'themes', theme))
    if os.path.isdir(dir_name):
        return dir_name
    raise Exception("Can't find theme '{0}'".format(theme))


def get_theme_path(theme):
    """Return the theme's path, which equals the theme's name."""
    return theme


def parse_theme_meta(theme_dir):
    """Parse a .theme meta file."""
    cp = configparser.ConfigParser()
    # The `or` case is in case theme_dir ends with a trailing slash
    theme_name = os.path.basename(theme_dir) or os.path.basename(os.path.dirname(theme_dir))
    theme_meta_path = os.path.join(theme_dir, theme_name + '.theme')
    cp.read(theme_meta_path)
    return cp if cp.has_section('Theme') else None


def get_template_engine(themes):
    """Get template engine used by a given theme."""
    for theme_name in themes:
        meta = parse_theme_meta(theme_name)
        if meta:
            e = meta.get('Theme', 'engine', fallback=None)
            if e:
                return e
        else:
            # Theme still uses old-style parent/engine files
            engine_path = os.path.join(theme_name, 'engine')
            if os.path.isfile(engine_path):
                with open(engine_path) as fd:
                    return fd.readlines()[0].strip()
    # default
    return 'mako'


def get_parent_theme_name(theme_name, themes_dirs=None):
    """Get name of parent theme."""
    meta = parse_theme_meta(theme_name)
    if meta:
        parent = meta.get('Theme', 'parent', fallback=None)
        if themes_dirs and parent:
            return get_theme_path_real(parent, themes_dirs)
        return parent
    else:
        # Theme still uses old-style parent/engine files
        parent_path = os.path.join(theme_name, 'parent')
        if os.path.isfile(parent_path):
            with open(parent_path) as fd:
                parent = fd.readlines()[0].strip()
            if themes_dirs:
                return get_theme_path_real(parent, themes_dirs)
            return parent
        return None


def get_theme_chain(theme, themes_dirs):
    """Create the full theme inheritance chain including paths."""
    themes = [get_theme_path_real(theme, themes_dirs)]

    while True:
        parent = get_parent_theme_name(themes[-1], themes_dirs=themes_dirs)
        # Avoid silly loops
        if parent is None or parent in themes:
            break
        themes.append(parent)
    return themes


def html_tostring_fragment(document):
    """Convert a HTML snippet to a fragment, ready for insertion elsewhere."""
    try:
        doc = lxml.html.tostring(document.body, encoding='unicode').strip()
    except Exception:
        doc = lxml.html.tostring(document, encoding='unicode').strip()
    start_fragments = ["<html>", "<body>"]
    end_fragments = ["</body>", "</html>"]
    for start in start_fragments:
        if doc.startswith(start):
            doc = doc[len(start):].strip()
    for end in end_fragments:
        if doc.endswith(end):
            doc = doc[:-len(end)].strip()
    return doc


INCOMPLETE_LANGUAGES_WARNED = set()


class LanguageNotFoundError(Exception):
    """An exception thrown if language is not found."""

    def __init__(self, lang, orig):
        """Initialize exception."""
        self.lang = lang
        self.orig = orig

    def __str__(self):
        """Stringify the exception."""
        return 'cannot find language {0}'.format(self.lang)


def load_messages(themes, translations, default_lang, themes_dirs):
    """Load theme's messages into context.

    All the messages from parent themes are loaded,
    and "younger" themes have priority.
    """
    messages = Functionary(dict, default_lang)
    oldpath = list(sys.path)
    found = {lang: False for lang in translations.keys()}
    last_exception = None
    completion_status = {lang: False for lang in translations.keys()}
    for theme_name in themes[::-1]:
        msg_folder = os.path.join(get_theme_path(theme_name), 'messages')
        default_folder = os.path.join(get_theme_path_real('base', themes_dirs), 'messages')
        sys.path.insert(0, default_folder)
        sys.path.insert(0, msg_folder)

        english = __import__('messages_en')
        # If we don't do the reload, the module is cached
        _reload(english)
        for lang in translations.keys():
            try:
                translation = __import__('messages_' + lang)
                # If we don't do the reload, the module is cached
                _reload(translation)
                found[lang] = True
                if sorted(translation.MESSAGES.keys()) != sorted(english.MESSAGES.keys()):
                    completion_status[lang] = completion_status[lang] or False
                else:
                    completion_status[lang] = True

                messages[lang].update(english.MESSAGES)
                for k, v in translation.MESSAGES.items():
                    if v:
                        messages[lang][k] = v
                del translation
            except ImportError as orig:
                last_exception = orig
        del english
        sys.path = oldpath

    if not all(found.values()):
        raise LanguageNotFoundError(lang, last_exception)
    for lang, status in completion_status.items():
        if not status and lang not in INCOMPLETE_LANGUAGES_WARNED:
            LOGGER.warning("Incomplete translation for language '{0}'.".format(lang))
            INCOMPLETE_LANGUAGES_WARNED.add(lang)

    return messages


def copy_tree(src, dst, link_cutoff=None, ignored_filenames=None):
    """Copy a src tree to the dst folder.

    Example:

    src = "themes/default/assets"
    dst = "output/assets"

    should copy "themes/defauts/assets/foo/bar" to
    "output/assets/foo/bar"

    If link_cutoff is set, then the links pointing at things
    *inside* that folder will stay as links, and links
    pointing *outside* that folder will be copied.

    ignored_filenames is a set of file names that will be ignored.
    """
    ignore = set(['.svn', '.git']) | (ignored_filenames or set())
    base_len = len(src.split(os.sep))
    for root, dirs, files in os.walk(src, followlinks=True):
        root_parts = root.split(os.sep)
        if set(root_parts) & ignore:
            continue
        dst_dir = os.path.join(dst, *root_parts[base_len:])
        makedirs(dst_dir)
        for src_name in files:
            if src_name in ('.DS_Store', 'Thumbs.db'):
                continue
            dst_file = os.path.join(dst_dir, src_name)
            src_file = os.path.join(root, src_name)
            yield {
                'name': dst_file,
                'file_dep': [src_file],
                'targets': [dst_file],
                'actions': [(copy_file, (src_file, dst_file, link_cutoff))],
                'clean': True,
            }


def copy_file(source, dest, cutoff=None):
    """Copy a file from source to dest. If link target starts with `cutoff`, symlinks are used."""
    dst_dir = os.path.dirname(dest)
    makedirs(dst_dir)
    if os.path.islink(source):
        link_target = os.path.relpath(
            os.path.normpath(os.path.join(dst_dir, os.readlink(source))))
        # Now we have to decide if we copy the link target or the
        # link itself.
        if cutoff is None or not link_target.startswith(cutoff):
            # We copy
            shutil.copy2(source, dest)
        else:
            # We link
            if os.path.exists(dest) or os.path.islink(dest):
                os.unlink(dest)
            os.symlink(os.readlink(source), dest)
    else:
        shutil.copy2(source, dest)


def remove_file(source):
    """Remove file or directory."""
    if os.path.isdir(source):
        shutil.rmtree(source)
    elif os.path.isfile(source) or os.path.islink(source):
        os.remove(source)


# slugify is adopted from
# https://code.activestate.com/recipes/
# 577257-slugify-make-a-string-usable-in-a-url-or-filename/
_slugify_strip_re = re.compile(r'[^+\w\s-]', re.UNICODE)
_slugify_hyphenate_re = re.compile(r'[-\s]+', re.UNICODE)


def slugify(value, lang=None, force=False):
    u"""Normalize string, convert to lowercase, remove non-alpha characters, convert spaces to hyphens.

    From Django's "django/template/defaultfilters.py".

    >>> print(slugify('áéí.óú', lang='en'))
    aeiou

    >>> print(slugify('foo/bar', lang='en'))
    foobar

    >>> print(slugify('foo bar', lang='en'))
    foo-bar
    """
    if not isinstance(value, str):
        raise ValueError("Not a unicode object: {0}".format(value))
    if USE_SLUGIFY or force:
        # This is the standard state of slugify, which actually does some work.
        # It is the preferred style, especially for Western languages.
        value = str(unidecode(value))
        value = _slugify_strip_re.sub('', value).strip().lower()
        return _slugify_hyphenate_re.sub('-', value)
    else:
        # This is the “disarmed” state of slugify, which lets the user
        # have any character they please (be it regular ASCII with spaces,
        # or another alphabet entirely).  This might be bad in some
        # environments, and as such, USE_SLUGIFY is better off being True!

        # We still replace some characters, though.  In particular, we need
        # to replace ? and #, which should not appear in URLs, and some
        # Windows-unsafe characters.  This list might be even longer.
        rc = '/\\?#"\'\r\n\t*:<>|'

        for c in rc:
            value = value.replace(c, '-')
        return value


def unslugify(value, lang=None, discard_numbers=True):
    """Given a slug string (as a filename), return a human readable string.

    If discard_numbers is True, numbers right at the beginning of input
    will be removed.
    """
    if discard_numbers:
        value = re.sub('^[0-9]+', '', value)
    value = re.sub(r'([_\-\.])', ' ', value)
    value = value.strip().capitalize()
    return value


def encodelink(iri):
    """Given an encoded or unencoded link string, return an encoded string suitable for use as a link in HTML and XML."""
    iri = unicodenormalize('NFC', iri)
    link = OrderedDict(urlparse(iri)._asdict())
    link['path'] = urlquote(urlunquote(link['path']).encode('utf-8'), safe="/~")
    try:
        link['netloc'] = link['netloc'].encode('utf-8').decode('idna').encode('idna').decode('utf-8')
    except UnicodeDecodeError:
        link['netloc'] = link['netloc'].encode('idna').decode('utf-8')
    encoded_link = urlunparse(link.values())
    return encoded_link


def full_path_from_urlparse(parsed) -> str:
    """Given urlparse output, return the full path (with query and fragment)."""
    dst = parsed.path
    if parsed.query:
        dst = "{0}?{1}".format(dst, parsed.query)
    if parsed.fragment:
        dst = "{0}#{1}".format(dst, parsed.fragment)
    return dst

# A very slightly safer version of zip.extractall that works on
# python < 2.6


class UnsafeZipException(Exception):
    """Exception for unsafe zip files."""

    pass


def extract_all(zipfile, path='themes'):
    """Extract all files from a zip file."""
    pwd = os.getcwd()
    makedirs(path)
    os.chdir(path)
    z = zipf(zipfile)
    namelist = z.namelist()
    for f in namelist:
        if f.endswith('/') and '..' in f:
            raise UnsafeZipException('The zip file contains ".." and is '
                                     'not safe to expand.')
    for f in namelist:
        if f.endswith('/'):
            makedirs(f)
        else:
            z.extract(f)
    z.close()
    os.chdir(pwd)


def to_datetime(value, tzinfo=None):
    """Convert string to datetime."""
    try:
        if type(value) is datetime.date:
            # type() instead of isinstance() is expected here, since we don’t
            # want to change datetime.datetime objects.
            value = datetime.datetime.combine(value, datetime.time(0, 0))
        if not isinstance(value, datetime.datetime):
            # dateutil does bad things with TZs like UTC-03:00.
            dateregexp = re.compile(r' UTC([+-][0-9][0-9]:[0-9][0-9])')
            value = re.sub(dateregexp, r'\1', value)
            value = dateutil.parser.parse(value)
        if not value.tzinfo:
            value = value.replace(tzinfo=tzinfo)
        return value
    except Exception:
        raise ValueError('Unrecognized date/time: {0!r}'.format(value))


def get_tzname(dt):
    """Given a datetime value, find the name of the time zone.

    DEPRECATED: This thing returned basically the 1st random zone
    that matched the offset.
    """
    return dt.tzname()


def current_time(tzinfo=None):
    """Get current time."""
    if tzinfo is not None:
        dt = datetime.datetime.now(tzinfo)
    else:
        dt = datetime.datetime.now(dateutil.tz.tzlocal())
    return dt


from nikola import filters as task_filters  # NOQA


def apply_filters(task, filters, skip_ext=None):
    """Apply filters to a task.

    If any of the targets of the given task has a filter that matches,
    adds the filter commands to the commands of the task,
    and the filter itself to the uptodate of the task.
    """
    if '.php' in filters.keys():
        if task_filters.php_template_injection not in filters['.php']:
            filters['.php'].append(task_filters.php_template_injection)
    else:
        filters['.php'] = [task_filters.php_template_injection]

    def filter_matches(ext):
        for key, value in list(filters.items()):
            if isinstance(key, (tuple, list)):
                if ext in key:
                    return value
            elif isinstance(key, (bytes, str)):
                if ext == key:
                    return value
            else:
                raise ValueError("Cannot find filter match for {0}".format(key))

    for target in task.get('targets', []):
        ext = os.path.splitext(target)[-1].lower()
        if skip_ext and ext in skip_ext:
            continue
        filter_ = filter_matches(ext)
        if filter_:
            for action in filter_:
                def unlessLink(action, target):
                    if not os.path.islink(target):
                        if isinstance(action, Callable):
                            action(target)
                        else:
                            subprocess.check_call(action % target, shell=True)

                task['actions'].append((unlessLink, (action, target)))
    return task


def get_crumbs(path, is_file=False, index_folder=None, lang=None):
    """Create proper links for a crumb bar.

    index_folder is used if you want to use title from index file
    instead of folder name as breadcrumb text.

    >>> crumbs = get_crumbs('galleries')
    >>> len(crumbs)
    1
    >>> crumbs[0]
    ['#', 'galleries']

    >>> crumbs = get_crumbs(os.path.join('galleries','demo'))
    >>> len(crumbs)
    2
    >>> crumbs[0]
    ['..', 'galleries']
    >>> crumbs[1]
    ['#', 'demo']

    >>> crumbs = get_crumbs(os.path.join('listings','foo','bar'), is_file=True)
    >>> len(crumbs)
    3
    >>> crumbs[0]
    ['..', 'listings']
    >>> crumbs[1]
    ['.', 'foo']
    >>> crumbs[2]
    ['#', 'bar']
    """
    crumbs = path.split(os.sep)
    _crumbs = []
    if is_file:
        for i, crumb in enumerate(crumbs[-3::-1]):  # Up to parent folder only
            _path = '/'.join(['..'] * (i + 1))
            _crumbs.append([_path, crumb])
        if len(crumbs) >= 2:
            _crumbs.insert(0, ['.', crumbs[-2]])  # file's folder
        if len(crumbs) >= 1:
            _crumbs.insert(0, ['#', crumbs[-1]])  # file itself
    else:
        for i, crumb in enumerate(crumbs[::-1]):
            _path = '/'.join(['..'] * i) or '#'
            _crumbs.append([_path, crumb])
    if index_folder and hasattr(index_folder, 'parse_index'):
        folder = path
        for i, crumb in enumerate(crumbs[::-1]):
            if folder[-1] == os.sep:
                folder = folder[:-1]
            # We don't care about the created Post() object except for its title;
            # hence, the input_folder and output_folder given to
            # index_folder.parse_index() don't matter
            index_post = index_folder.parse_index(folder, '', '')
            folder = folder.replace(crumb, '')
            if index_post:
                crumb = index_post.title(lang) or crumb
            _crumbs[i][1] = crumb
    return list(reversed(_crumbs))


def get_asset_path(path, themes, files_folders={'files': ''}, output_dir='output'):
    """Return the "real", absolute path to the asset.

    By default, it checks which theme provides the asset.
    If the asset is not provided by a theme, then it will be checked for
    in the FILES_FOLDERS.
    If it's not provided by either, it will be chacked in output, where
    it may have been created by another plugin.

    >>> print(get_asset_path('assets/css/nikola_rst.css', get_theme_chain('bootstrap3', ['themes'])))
    /.../nikola/data/themes/base/assets/css/nikola_rst.css

    >>> print(get_asset_path('assets/css/theme.css', get_theme_chain('bootstrap3', ['themes'])))
    /.../nikola/data/themes/bootstrap3/assets/css/theme.css

    >>> print(get_asset_path('nikola.py', get_theme_chain('bootstrap3', ['themes']), {'nikola': ''}))
    /.../nikola/nikola.py

    >>> print(get_asset_path('nikola.py', get_theme_chain('bootstrap3', ['themes']), {'nikola': 'nikola'}))
    None

    >>> print(get_asset_path('nikola/nikola.py', get_theme_chain('bootstrap3', ['themes']), {'nikola': 'nikola'}))
    /.../nikola/nikola.py

    """
    for theme_name in themes:
        candidate = os.path.join(get_theme_path(theme_name), path)
        if os.path.isfile(candidate):
            return candidate
    for src, rel_dst in files_folders.items():
        relpath = os.path.normpath(os.path.relpath(path, rel_dst))
        if not relpath.startswith('..' + os.path.sep):
            candidate = os.path.abspath(os.path.join(src, relpath))
            if os.path.isfile(candidate):
                return candidate

    if output_dir:
        candidate = os.path.join(output_dir, path)
        if os.path.isfile(candidate):
            return candidate

    # whatever!
    return None


class LocaleBorgUninitializedException(Exception):
    """Exception for unitialized LocaleBorg."""

    def __init__(self):
        """Initialize exception."""
        super().__init__("Attempt to use LocaleBorg before initialization")


# Customized versions of babel.dates functions that don't do weird stuff with
# timezones. Without these fixes, DST would follow local settings (because
# dateutil’s timezones return stuff depending on their input, and datetime.time
# objects have no year/month/day to base the information on.
def format_datetime(datetime=None, format='medium',
                    locale=babel.dates.LC_TIME):
    """Format a datetime object."""
    locale = babel.dates.Locale.parse(locale)
    if format in ('full', 'long', 'medium', 'short'):
        return babel.dates.get_datetime_format(format, locale=locale) \
            .replace("'", "") \
            .replace('{0}', format_time(datetime, format, locale=locale)) \
            .replace('{1}', babel.dates.format_date(datetime, format, locale=locale))
    else:
        return babel.dates.parse_pattern(format).apply(datetime, locale)


def format_time(time=None, format='medium', locale=babel.dates.LC_TIME):
    """Format time. Input can be datetime.time or datetime.datetime."""
    locale = babel.dates.Locale.parse(locale)
    if format in ('full', 'long', 'medium', 'short'):
        format = babel.dates.get_time_format(format, locale=locale)
    return babel.dates.parse_pattern(format).apply(time, locale)


def format_skeleton(skeleton, datetime=None, fo=None, fuzzy=True,
                    locale=babel.dates.LC_TIME):
    """Format a datetime based on a skeleton."""
    locale = babel.dates.Locale.parse(locale)
    if fuzzy and skeleton not in locale.datetime_skeletons:
        skeleton = babel.dates.match_skeleton(skeleton, locale.datetime_skeletons)
    format = locale.datetime_skeletons[skeleton]
    return format_datetime(datetime, format, locale)


class LocaleBorg(object):
    """Provide locale related services and autoritative current_lang.

    This class stores information about the locales used and interfaces
    with the Babel library to provide internationalization services.

    Usage:
        # early in cmd or test execution
        LocaleBorg.initialize(...)

        # any time later
        lang = LocaleBorg().<service>

    Available services:
        .current_lang: autoritative current_lang, the last seen in set_locale
        .formatted_date: format a date(time) according to locale rules
        .format_date_in_string: take a message and format the date in it

    The default implementation uses the Babel package and completely ignores
    the Python `locale` module. If you wish to override this, write functions
    and assign them to the appropriate names. The functions are:

     * LocaleBorg.datetime_formatter(date, date_format, lang, locale)
     * LocaleBorg.in_string_formatter(date, mode, custom_format, lang, locale)
    """

    initialized = False

    # Can be used to override Babel
    datetime_formatter = None
    in_string_formatter = None

    @classmethod
    def initialize(cls, locales: 'typing.Dict[str, str]', initial_lang: str):
        """Initialize LocaleBorg.

        locales: dict with custom locale name overrides.
        """
        if not initial_lang:
            raise ValueError("Unknown initial language {0}".format(initial_lang))
        cls.reset()
        cls.locales = locales
        cls.__initial_lang = initial_lang
        cls.initialized = True

    def __get_shared_state(self):
        if not self.initialized:  # pragma: no cover
            raise LocaleBorgUninitializedException()
        shared_state = getattr(self.__thread_local, 'shared_state', None)
        if shared_state is None:
            shared_state = {'current_lang': self.__initial_lang}
            self.__thread_local.shared_state = shared_state
        return shared_state

    @classmethod
    def reset(cls):
        """Reset LocaleBorg.

        Used in testing to prevent leaking state between tests.
        """
        cls.__thread_local = threading.local()
        cls.__thread_lock = threading.Lock()

        cls.locales = {}
        cls.initialized = False
        cls.thread_local = None
        cls.datetime_formatter = None
        cls.in_string_formatter = None

    def __init__(self):
        """Initialize."""
        if not self.initialized:
            raise LocaleBorgUninitializedException()

    @property
    def current_lang(self) -> str:
        """Return the current language."""
        return self.__get_shared_state()['current_lang']

    def set_locale(self, lang: str) -> str:
        """Set the current language and return an empty string (to make use in templates easier)."""
        with self.__thread_lock:
            self.__get_shared_state()['current_lang'] = lang
            return ''

    def formatted_date(self, date_format: 'str',
                       date: 'typing.Union[datetime.date, datetime.datetime]',
                       lang: 'typing.Optional[str]' = None) -> str:
        """Return the formatted date/datetime as a string."""
        if lang is None:
            lang = self.current_lang
        locale = self.locales.get(lang, lang)
        # Get a string out of a TranslatableSetting
        if isinstance(date_format, TranslatableSetting):
            date_format = date_format(lang)

        # Always ask Python if the date_format is webiso
        if date_format == 'webiso':
            # Formatted after RFC 3339 (web ISO 8501 profile) with Zulu
            # zone designator for times in UTC and no microsecond precision.
            return date.replace(microsecond=0).isoformat().replace('+00:00', 'Z')
        elif LocaleBorg.datetime_formatter is not None:
            return LocaleBorg.datetime_formatter(date, date_format, lang, locale)
        else:
            return format_datetime(date, date_format, locale=locale)

    def format_date_in_string(self, message: str, date: datetime.date, lang: 'typing.Optional[str]' = None) -> str:
        """Format date inside a string (message).

        Accepted modes: month, month_year, month_day_year.
        Format: {month} for standard, {month:MMMM} for customization.
        """
        modes = {
            'month': ('date', 'LLLL'),
            'month_year': ('skeleton', 'yMMMM'),
            'month_day_year': ('date', 'long')
        }

        if lang is None:
            lang = self.current_lang
        locale = self.locales.get(lang, lang)

        def date_formatter(match: typing.Match) -> str:
            """Format a date as requested."""
            mode, custom_format = match.groups()
            if LocaleBorg.in_string_formatter is not None:
                return LocaleBorg.in_string_formatter(date, mode, custom_format, lang, locale)
            elif custom_format:
                return babel.dates.format_date(date, custom_format, locale)
            else:
                function, fmt = modes[mode]
                if function == 'skeleton':
                    return format_skeleton(fmt, date, locale=locale)
                else:
                    return babel.dates.format_date(date, fmt, locale)

        return re.sub(r'{(.*?)(?::(.*?))?}', date_formatter, message)


class ExtendedRSS2(rss.RSS2):
    """Extended RSS class."""

    xsl_stylesheet_href = None

    def publish(self, handler):
        """Publish a feed."""
        if self.xsl_stylesheet_href:
            handler.processingInstruction("xml-stylesheet", 'type="text/xsl" href="{0}" media="all"'.format(self.xsl_stylesheet_href))
        super().publish(handler)

    def publish_extensions(self, handler):
        """Publish extensions."""
        if self.self_url:
            handler.startElement("atom:link", {
                'href': self.self_url,
                'rel': "self",
                'type': "application/rss+xml"
            })
            handler.endElement("atom:link")


class ExtendedItem(rss.RSSItem):
    """Extended RSS item."""

    def __init__(self, **kw):
        """Initialize RSS item."""
        self.creator = kw.pop('creator', None)

        # It's an old style class
        rss.RSSItem.__init__(self, **kw)

    def publish_extensions(self, handler):
        """Publish extensions."""
        if self.creator:
            handler.startElement("dc:creator", {})
            handler.characters(self.creator)
            handler.endElement("dc:creator")


# \x00 means the "<" was backslash-escaped
explicit_title_re = re.compile(r'^(.+?)\s*(?<!\x00)<(.*?)>$', re.DOTALL)


def split_explicit_title(text):
    """Split role content into title and target, if given.

    From Sphinx's "sphinx/util/nodes.py"
    """
    match = explicit_title_re.match(text)
    if match:
        return True, match.group(1), match.group(2)
    return False, text, text


def first_line(doc):
    """Extract first non-blank line from text, to extract docstring title."""
    if doc is not None:
        for line in doc.splitlines():
            striped = line.strip()
            if striped:
                return striped
    return ''


def demote_headers(doc, level=1):
    """Demote <hN> elements by one."""
    if level == 0:
        return doc
    elif level > 0:
        levels = range(1, 7 - (level - 1))
        levels = reversed(levels)
    elif level < 0:
        levels = range(2 + level, 7)

    for before in levels:
        after = before + level
        if after < 1:
            # html headers can't go lower than 1
            after = 1
        elif after > 6:
            # html headers go until 6
            after = 6

        if before == after:
            continue

        elements = doc.xpath('//h{}'.format(before))
        new_tag = 'h{}'.format(after)
        for element in elements:
            element.tag = new_tag


def get_root_dir():
    """Find root directory of nikola site by looking for conf.py."""
    root = os.getcwd()

    confname = 'conf.py'

    while True:
        if os.path.exists(os.path.join(root, confname)):
            return root
        else:
            basedir = os.path.split(root)[0]
            # Top directory, already checked
            if basedir == root:
                break
            root = basedir

    return None


def get_translation_candidate(config, path, lang):
    """Return a possible path where we can find the translated version of some page, based on the TRANSLATIONS_PATTERN configuration variable.

    >>> config = {'TRANSLATIONS_PATTERN': '{path}.{lang}.{ext}', 'DEFAULT_LANG': 'en', 'TRANSLATIONS': {'es':'1', 'en': 1}}
    >>> print(get_translation_candidate(config, '*.rst', 'es'))
    *.es.rst
    >>> print(get_translation_candidate(config, 'fancy.post.rst', 'es'))
    fancy.post.es.rst
    >>> print(get_translation_candidate(config, '*.es.rst', 'es'))
    *.es.rst
    >>> print(get_translation_candidate(config, '*.es.rst', 'en'))
    *.rst
    >>> print(get_translation_candidate(config, 'cache/posts/fancy.post.es.html', 'en'))
    cache/posts/fancy.post.html
    >>> print(get_translation_candidate(config, 'cache/posts/fancy.post.html', 'es'))
    cache/posts/fancy.post.es.html
    >>> print(get_translation_candidate(config, 'cache/pages/charts.html', 'es'))
    cache/pages/charts.es.html
    >>> print(get_translation_candidate(config, 'cache/pages/charts.html', 'en'))
    cache/pages/charts.html

    >>> config = {'TRANSLATIONS_PATTERN': '{path}.{ext}.{lang}', 'DEFAULT_LANG': 'en', 'TRANSLATIONS': {'es':'1', 'en': 1}}
    >>> print(get_translation_candidate(config, '*.rst', 'es'))
    *.rst.es
    >>> print(get_translation_candidate(config, '*.rst.es', 'es'))
    *.rst.es
    >>> print(get_translation_candidate(config, '*.rst.es', 'en'))
    *.rst
    >>> print(get_translation_candidate(config, 'cache/posts/fancy.post.html.es', 'en'))
    cache/posts/fancy.post.html
    >>> print(get_translation_candidate(config, 'cache/posts/fancy.post.html', 'es'))
    cache/posts/fancy.post.html.es
    """
    # FIXME: this is rather slow and this function is called A LOT
    # Convert the pattern into a regexp
    pattern = config['TRANSLATIONS_PATTERN']
    # This will still break if the user has ?*[]\ in the pattern. But WHY WOULD HE?
    pattern = pattern.replace('.', r'\.')
    pattern = pattern.replace('{path}', '(?P<path>.+?)')
    pattern = pattern.replace('{ext}', r'(?P<ext>[^\./]+)')
    pattern = pattern.replace('{lang}', '(?P<lang>{0})'.format('|'.join(config['TRANSLATIONS'].keys())))
    m = re.match(pattern, path)
    if m and all(m.groups()):  # It's a translated path
        p, e, l = m.group('path'), m.group('ext'), m.group('lang')
        if l == lang:  # Nothing to do
            return path
        elif lang == config['DEFAULT_LANG']:  # Return untranslated path
            return '{0}.{1}'.format(p, e)
        else:  # Change lang and return
            return config['TRANSLATIONS_PATTERN'].format(path=p, ext=e, lang=lang)
    else:
        # It's a untranslated path, assume it's path.ext
        p, e = os.path.splitext(path)
        e = e[1:]  # No initial dot
        if lang == config['DEFAULT_LANG']:  # Nothing to do
            return path
        else:  # Change lang and return
            return config['TRANSLATIONS_PATTERN'].format(path=p, ext=e, lang=lang)


def write_metadata(data, metadata_format=None, comment_wrap=False, site=None, compiler=None):
    """Write metadata.

    Recommended usage: pass `site`, `comment_wrap` (True, False, or a 2-tuple of start/end markers), and optionally `compiler`. Other options are for backwards compatibility.
    """
    # API compatibility
    if metadata_format is None and site is not None:
        metadata_format = site.config.get('METADATA_FORMAT', 'nikola').lower()
    if metadata_format is None:
        metadata_format = 'nikola'

    if site is None:
        import nikola.metadata_extractors
        metadata_extractors_by = nikola.metadata_extractors.default_metadata_extractors_by()
        nikola.metadata_extractors.load_defaults(site, metadata_extractors_by)
    else:
        metadata_extractors_by = site.metadata_extractors_by

    # Pelican is mapped to rest_docinfo, markdown_meta, or nikola.
    if metadata_format == 'pelican':
        if compiler and compiler.name == 'rest':
            metadata_format = 'rest_docinfo'
        elif compiler and compiler.name == 'markdown':
            metadata_format = 'markdown_meta'
        else:
            # Quiet fallback.
            metadata_format = 'nikola'

    default_meta = ('nikola', 'rest_docinfo', 'markdown_meta')
    extractor = metadata_extractors_by['name'].get(metadata_format)
    if extractor and extractor.supports_write:
        extractor.check_requirements()
        return extractor.write_metadata(data, comment_wrap)
    elif extractor and metadata_format not in default_meta:
        LOGGER.warning('Writing METADATA_FORMAT {} is not supported, using "nikola" format'.format(metadata_format))
    elif metadata_format not in default_meta:
        LOGGER.warning('Unknown METADATA_FORMAT {}, using "nikola" format'.format(metadata_format))

    if metadata_format == 'rest_docinfo':
        title = data['title']
        results = [
            '=' * len(title),
            title,
            '=' * len(title),
            ''
        ] + [':{0}: {1}'.format(k, v) for k, v in data.items() if v and k != 'title'] + ['']
        return '\n'.join(results)
    elif metadata_format == 'markdown_meta':
        results = ['{0}: {1}'.format(k, v) for k, v in data.items() if v] + ['', '']
        return '\n'.join(results)
    else:  # Nikola, default
        from nikola.metadata_extractors import DEFAULT_EXTRACTOR
        return DEFAULT_EXTRACTOR.write_metadata(data, comment_wrap)


def bool_from_meta(meta, key, fallback=False, blank=None):
    """Convert a boolean-ish meta value to a boolean."""
    value = meta.get(key)
    if isinstance(value, str):
        value_lowercase = value.lower().strip()
        if value_lowercase in {"true", "yes", "1"}:
            return True
        elif value_lowercase in {"false", "no", "0"}:
            return False
        elif not value_lowercase:
            return blank
    elif isinstance(value, int):
        return bool(value)
    elif value is None:
        return blank
    return fallback


def ask(query, default=None):
    """Ask a question."""
    if default:
        default_q = ' [{0}]'.format(default)
    else:
        default_q = ''
    inp = input("{query}{default_q}: ".format(query=query, default_q=default_q)).strip()
    if inp or default is None:
        return inp
    else:
        return default


def ask_yesno(query, default=None):
    """Ask a yes/no question."""
    if default is None:
        default_q = ' [y/n]'
    elif default is True:
        default_q = ' [Y/n]'
    elif default is False:
        default_q = ' [y/N]'
    inp = input("{query}{default_q} ".format(query=query, default_q=default_q)).strip()
    if inp:
        return inp.lower().startswith('y')
    elif default is not None:
        return default
    else:
        # Loop if no answer and no default.
        return ask_yesno(query, default)


class CommandWrapper(object):
    """Converts commands into functions."""

    def __init__(self, cmd, commands_object):
        self.cmd = cmd
        self.commands_object = commands_object

    def __call__(self, *args, **kwargs):
        if args or (not args and not kwargs):
            self.commands_object._run([self.cmd] + list(args))
        else:
            # Here's where the keyword magic would have to go
            self.commands_object._run_with_kw(self.cmd, *args, **kwargs)


class Commands(object):
    """Nikola Commands.

    Sample usage:
    >>> commands.check('-l')                     # doctest: +SKIP

    Or, if you know the internal argument names:
    >>> commands.check(list=True)                # doctest: +SKIP
    """

    def __init__(self, main, config, doitargs):
        """Take a main instance, work as wrapper for commands."""
        self._cmdnames = []
        self._main = main
        self._config = config
        self._doitargs = doitargs
        try:
            cmdict = self._doitargs['cmds'].to_dict()
        except AttributeError:  # not a doit PluginDict
            cmdict = self._doitargs['cmds']
        for k, v in cmdict.items():
            # cleanup: run is doit-only, init is useless in an existing site
            if k in ['run', 'init']:
                continue

            self._cmdnames.append(k)

            try:
                # nikola command: already instantiated (singleton)
                opt = v.get_options()
            except TypeError:
                # doit command: needs some help
                opt = v(config=self._config, **self._doitargs).get_options()
            nc = type(
                k,
                (CommandWrapper,),
                {
                    '__doc__': options2docstring(k, opt)
                })
            setattr(self, k, nc(k, self))

    def _run(self, cmd_args):
        self._main.run(cmd_args)

    def _run_with_kw(self, cmd, *a, **kw):
        # cyclic import hack
        from nikola.plugin_categories import Command
        try:
            cmd = self._doitargs['cmds'].get_plugin(cmd)
        except AttributeError:  # not a doit PluginDict
            cmd = self._doitargs['cmds'][cmd]
        try:
            opt = cmd.get_options()
        except TypeError:
            cmd = cmd(config=self._config, **self._doitargs)
            opt = cmd.get_options()

        options, _ = CmdParse(opt).parse([])
        options.update(kw)
        if isinstance(cmd, Command):
            cmd.execute(options=options, args=a)
        else:  # Doit command
            cmd.execute(options, a)

    def __repr__(self):
        """Return useful and verbose help."""
        return """\
<Nikola Commands>

    Sample usage:
    >>> commands.check('-l')

    Or, if you know the internal argument names:
    >>> commands.check(list=True)

Available commands: {0}.""".format(', '.join(self._cmdnames))


def options2docstring(name, options):
    """Translate options to a docstring."""
    result = ['Function wrapper for command %s' % name, 'arguments:']
    for opt in options:
        result.append('{0} type {1} default {2}'.format(opt.name, opt.type.__name__, opt.default))
    return '\n'.join(result)


class NikolaPygmentsHTML(BetterHtmlFormatter):
    """A Nikola-specific modification of Pygments' HtmlFormatter."""

    def __init__(self, anchor_ref=None, classes=None, **kwargs):
        """Initialize formatter."""
        if classes is None:
            classes = ['code', 'literal-block']
        if anchor_ref:
            kwargs['lineanchors'] = slugify(
                anchor_ref, lang=LocaleBorg().current_lang, force=True)
        self.nclasses = classes
        kwargs['cssclass'] = 'code'
        if not kwargs.get('linenos'):
            # Default to no line numbers (Issue #3426)
            kwargs['linenos'] = False
        if kwargs.get('linenos') not in {'table', 'inline', 'ol', False}:
            # Map invalid values to table
            kwargs['linenos'] = 'table'
        kwargs['anchorlinenos'] = kwargs['linenos'] == 'table'
        kwargs['nowrap'] = False
        super().__init__(**kwargs)

    def wrap(self, source, *args):
        """Wrap the ``source``, which is a generator yielding individual lines, in custom generators."""
        style = []
        if self.prestyles:
            style.append(self.prestyles)
        if self.noclasses:
            style.append('line-height: 125%')
        style = '; '.join(style)
        classes = ' '.join(self.nclasses)

        yield 0, ('<pre class="{0}"'.format(classes) + (style and ' style="{0}"'.format(style)) + '>')
        for tup in source:
            yield tup
        yield 0, '</pre>'


# For consistency, override the default formatter.
pygments.formatters._formatter_cache['HTML'] = NikolaPygmentsHTML
pygments.formatters._formatter_cache['html'] = NikolaPygmentsHTML
_original_find_formatter_class = pygments.formatters.find_formatter_class


def nikola_find_formatter_class(alias):
    """Nikola-specific version of find_formatter_class."""
    if "html" in alias.lower():
        return NikolaPygmentsHTML
    return _original_find_formatter_class(alias)


pygments.formatters.find_formatter_class = nikola_find_formatter_class


def get_displayed_page_number(i, num_pages, site):
    """Get page number to be displayed for entry `i`."""
    if not i:
        i = 0
    if site.config["INDEXES_STATIC"]:
        return i if i > 0 else num_pages
    else:
        return i + 1 if site.config["INDEXES_PAGES_MAIN"] else i


def adjust_name_for_index_path_list(path_list, i, displayed_i, lang, site, force_addition=False, extension=None):
    """Retrurn a path list for a given index page."""
    index_file = site.config["INDEX_FILE"]
    if i or force_addition:
        path_list = list(path_list)
        if force_addition and not i:
            i = 0
        if not extension:
            _, extension = os.path.splitext(index_file)
        if len(path_list) > 0 and path_list[-1] == '':
            path_list[-1] = index_file
        elif len(path_list) == 0 or not path_list[-1].endswith(extension):
            path_list.append(index_file)
        if site.config["PRETTY_URLS"] and site.config["INDEXES_PRETTY_PAGE_URL"](lang) and path_list[-1] == index_file:
            path_schema = site.config["INDEXES_PRETTY_PAGE_URL"](lang)
            if isinstance(path_schema, (bytes, str)):
                path_schema = [path_schema]
        else:
            path_schema = None
        if path_schema is not None:
            del path_list[-1]
            for entry in path_schema:
                path_list.append(entry.format(number=displayed_i, old_number=i, index_file=index_file))
        else:
            path_list[-1] = '{0}-{1}{2}'.format(os.path.splitext(path_list[-1])[0], i, extension)
    return path_list


def os_path_split(path):
    """Split a path."""
    result = []
    while True:
        previous_path = path
        path, tail = os.path.split(path)
        if path == previous_path and tail == '':
            result.insert(0, path)
            break
        result.insert(0, tail)
        if len(path) == 0:
            break
    return result


def adjust_name_for_index_path(name, i, displayed_i, lang, site, force_addition=False, extension=None):
    """Return file name for a given index file."""
    return os.path.join(*adjust_name_for_index_path_list(os_path_split(name), i, displayed_i, lang, site, force_addition, extension))


def adjust_name_for_index_link(name, i, displayed_i, lang, site, force_addition=False, extension=None):
    """Return link for a given index file."""
    link = adjust_name_for_index_path_list(name.split('/'), i, displayed_i, lang, site, force_addition, extension)
    if not extension == ".atom":
        if len(link) > 0 and link[-1] == site.config["INDEX_FILE"] and site.config["STRIP_INDEXES"]:
            link[-1] = ''
    return '/'.join(link)


def create_redirect(src, dst):
    """Create a redirection."""
    makedirs(os.path.dirname(src))
    with io.open(src, "w+", encoding="utf8") as fd:
        fd.write('<!DOCTYPE html>\n<head>\n<meta charset="utf-8">\n'
                 '<title>Redirecting...</title>\n<meta name="robots" '
                 'content="noindex">\n<meta http-equiv="refresh" content="0; '
                 'url={0}">\n</head>\n<body>\n<p>Page moved '
                 '<a href="{0}">here</a>.</p>\n</body>'.format(dst))


def colorize_str_from_base_color(string, base_color):
    """Find a perceptual similar color from a base color based on the hash of a string.

    Make up to 16 attempts (number of bytes returned by hashing) at picking a
    hue for our color at least 27 deg removed from the base color, leaving
    lightness and saturation untouched using HSLuv colorspace.
    """
    def hash_str(string, pos):
        return hashlib.md5(string.encode('utf-8')).digest()[pos]

    def degreediff(dega, degb):
        return min(abs(dega - degb), abs((degb - dega) + 360))

    if hsluv is None:
        req_missing(['hsluv'], 'Use color mixing (section colors)',
                    optional=True)
        return base_color
    h, s, l = hsluv.hex_to_hsluv(base_color)
    old_h = h
    idx = 0
    while degreediff(old_h, h) < 27 and idx < 16:
        h = 360.0 * (float(hash_str(string, idx)) / 255)
        idx += 1
    return hsluv.hsluv_to_hex((h, s, l))


def colorize_str(string: str, base_color: str, presets: dict):
    """Colorize a string by using a presets dict or generate one based on base_color."""
    if string in presets:
        return presets[string]
    return colorize_str_from_base_color(string, base_color)


def color_hsl_adjust_hex(hexstr, adjust_h=None, adjust_s=None, adjust_l=None):
    """Adjust a hex color using HSL arguments, adjustments in percentages 1.0 to -1.0. Returns a hex color."""
    h, s, l = hsluv.hex_to_hsluv(hexstr)

    if adjust_h:
        h = h + (adjust_h * 360.0)

    if adjust_s:
        s = s + (adjust_s * 100.0)

    if adjust_l:
        l = l + (adjust_l * 100.0)

    return hsluv.hsluv_to_hex((h, s, l))


def dns_sd(port, inet6):
    """Optimistically publish a HTTP service to the local network over DNS-SD.

    Works only on Linux/FreeBSD.  Requires the `avahi` and `dbus` modules (symlinks in virtualenvs)
    """
    try:
        import avahi
        import dbus
        inet = avahi.PROTO_INET6 if inet6 else avahi.PROTO_INET
        name = "{0}'s Nikola Server on {1}".format(os.getlogin(), socket.gethostname())
        bus = dbus.SystemBus()
        bus_server = dbus.Interface(bus.get_object(avahi.DBUS_NAME,
                                                   avahi.DBUS_PATH_SERVER),
                                    avahi.DBUS_INTERFACE_SERVER)
        bus_group = dbus.Interface(bus.get_object(avahi.DBUS_NAME,
                                                  bus_server.EntryGroupNew()),
                                   avahi.DBUS_INTERFACE_ENTRY_GROUP)
        bus_group.AddService(avahi.IF_UNSPEC, inet, dbus.UInt32(0),
                             name, '_http._tcp', '', '',
                             dbus.UInt16(port), '')
        bus_group.Commit()
        return bus_group  # remember to bus_group.Reset() to unpublish
    except Exception:
        return None


def clean_before_deployment(site):
    """Clean drafts and future posts before deployment."""
    undeployed_posts = []
    deploy_drafts = site.config.get('DEPLOY_DRAFTS', True)
    deploy_future = site.config.get('DEPLOY_FUTURE', False)
    if not (deploy_drafts and deploy_future):  # == !drafts || !future
        # Remove drafts and future posts
        out_dir = site.config['OUTPUT_FOLDER']
        site.scan_posts()
        for post in site.timeline:
            if (not deploy_drafts and post.is_draft) or (not deploy_future and post.publish_later):
                for lang in post.translated_to:
                    remove_file(os.path.join(out_dir, post.destination_path(lang)))
                    source_path = post.destination_path(lang, post.source_ext(True))
                    remove_file(os.path.join(out_dir, source_path))
                undeployed_posts.append(post)
    return undeployed_posts


def sort_posts(posts, *keys):
    """Sort posts by a given predicate. Helper function for templates.

    If a key starts with '-', it is sorted in descending order.

    Usage examples::

        sort_posts(timeline, 'title', 'date')
        sort_posts(timeline, 'author', '-section_name')
    """
    # We reverse the keys to get the usual ordering method: the first key
    # provided is the most important sorting predicate (first by 'title', then
    # by 'date' in the first example)
    for key in reversed(keys):
        if key.startswith('-'):
            key = key[1:]
            reverse = True
        else:
            reverse = False
        try:
            # An attribute (or method) of the Post object
            a = getattr(posts[0], key)
            if callable(a):
                keyfunc = operator.methodcaller(key)
            else:
                keyfunc = operator.attrgetter(key)
        except AttributeError:
            # Post metadata
            keyfunc = operator.methodcaller('meta', key)

        posts = sorted(posts, reverse=reverse, key=keyfunc)
    return posts


def smartjoin(join_char: str, string_or_iterable) -> str:
    """Join string_or_iterable with join_char if it is iterable; otherwise converts it to string.

    >>> smartjoin('; ', 'foo, bar')
    'foo, bar'
    >>> smartjoin('; ', ['foo', 'bar'])
    'foo; bar'
    >>> smartjoin(' to ', ['count', 42])
    'count to 42'
    """
    if isinstance(string_or_iterable, (str, bytes)):
        return string_or_iterable
    elif isinstance(string_or_iterable, Iterable):
        return join_char.join([str(e) for e in string_or_iterable])
    else:
        return str(string_or_iterable)


def _smartjoin_filter(string_or_iterable, join_char: str) -> str:
    """Join stuff smartly, with reversed arguments for Jinja2 filters."""
    # http://jinja.pocoo.org/docs/2.10/api/#custom-filters
    return smartjoin(join_char, string_or_iterable)


# Stolen from textwrap in Python 3.4.3.
def indent(text, prefix, predicate=None):
    """Add 'prefix' to the beginning of selected lines in 'text'.

    If 'predicate' is provided, 'prefix' will only be added to the lines
    where 'predicate(line)' is True. If 'predicate' is not provided,
    it will default to adding 'prefix' to all non-empty lines that do not
    consist solely of whitespace characters.
    """
    if predicate is None:
        def predicate(line):
            return line.strip()

    def prefixed_lines():
        for line in text.splitlines(True):
            yield (prefix + line if predicate(line) else line)
    return ''.join(prefixed_lines())


def load_data(path):
    """Given path to a file, load data from it."""
    ext = os.path.splitext(path)[-1]
    loader = None
    function = 'load'
    if ext in {'.yml', '.yaml'}:
        if YAML is None:
            req_missing(['ruamel.yaml'], 'use YAML data files')
            return {}
        loader = YAML(typ='safe')
        function = 'load'
    elif ext in {'.json', '.js'}:
        loader = json
    elif ext in {'.toml', '.tml'}:
        if toml is None:
            req_missing(['toml'], 'use TOML data files')
            return {}
        loader = toml
    if loader is None:
        return
    with io.open(path, 'r', encoding='utf-8-sig') as inf:
        return getattr(loader, function)(inf)


def rss_writer(rss_obj, output_path):
    """Write an RSS object to an xml file."""
    dst_dir = os.path.dirname(output_path)
    makedirs(dst_dir)
    with io.open(output_path, "w+", encoding="utf-8") as rss_file:
        data = rss_obj.to_xml(encoding='utf-8')
        if isinstance(data, bytes):
            data = data.decode('utf-8')
        rss_file.write(data)


def map_metadata(meta, key, config):
    """Map metadata from other platforms to Nikola names.

    This uses the METADATA_MAPPING and METADATA_VALUE_MAPPING settings (via ``config``) and modifies the dict in place.
    """
    for foreign, ours in config.get('METADATA_MAPPING', {}).get(key, {}).items():
        if foreign in meta:
            meta[ours] = meta[foreign]

    for meta_key, hook in config.get('METADATA_VALUE_MAPPING', {}).get(key, {}).items():
        if meta_key in meta:
            meta[meta_key] = hook(meta[meta_key])


def parselinenos(spec: str, total: int) -> List[int]:
    """Parse a line number spec.

    Example: "1,2,4-6" -> [0, 1, 3, 4, 5]
    """
    items = list()
    parts = spec.split(',')
    for part in parts:
        try:
            begend = part.strip().split('-')
            if ['', ''] == begend:
                raise ValueError
            elif len(begend) == 1:
                items.append(int(begend[0]) - 1)
            elif len(begend) == 2:
                start = int(begend[0] or 1)  # left half open (cf. -10)
                end = int(begend[1] or max(start, total))  # right half open (cf. 10-)
                if start > end:  # invalid range (cf. 10-1)
                    raise ValueError
                items.extend(range(start - 1, end))
            else:
                raise ValueError
        except Exception as exc:
            raise ValueError('invalid line number spec: %r' % spec) from exc
    return items


class ClassificationTranslationManager(object):
    """Keeps track of which classifications could be translated as which others.

    The internal structure is as follows:
    - per language, you have a map of classifications to maps
    - the inner map is a map from other languages to sets of classifications
      which are considered as translations
    """

    def __init__(self):
        self._data = defaultdict(dict)

    def add_translation(self, translation_map):
        """Add translation of one classification.

        ``translation_map`` must be a dictionary mapping languages to their
        translations of the added classification.
        """
        for lang, classification in translation_map.items():
            clmap = self._data[lang]
            cldata = clmap.get(classification)
            if cldata is None:
                cldata = defaultdict(set)
                clmap[classification] = cldata
            for other_lang, other_classification in translation_map.items():
                if other_lang != lang:
                    cldata[other_lang].add(other_classification)

    def get_translations(self, classification, lang):
        """Get a dict mapping other languages to (unsorted) lists of translated classifications."""
        clmap = self._data[lang]
        cldata = clmap.get(classification)
        if cldata is None:
            return {}
        else:
            return {other_lang: list(classifications) for other_lang, classifications in cldata.items()}

    def get_translations_as_list(self, classification, lang, classifications_per_language):
        """Get a list of pairs ``(other_lang, other_classification)`` which are translations of ``classification``.

        Avoid classifications not in ``classifications_per_language``.
        """
        clmap = self._data[lang]
        cldata = clmap.get(classification)
        if cldata is None:
            return []
        else:
            result = []
            for other_lang, classifications in cldata.items():
                for other_classification in classifications:
                    if other_classification in classifications_per_language[other_lang]:
                        result.append((other_lang, other_classification))
            return result

    def has_translations(self, classification, lang):
        """Return whether we know about the classification in that language.

        Note that this function returning ``True`` does not mean that
        ``get_translations`` returns a non-empty dict or that
        ``get_translations_as_list`` returns a non-empty list, but only
        that this classification was explicitly added with
        ``add_translation`` at some point.
        """
        return self._data[lang].get(classification) is not None

    def add_defaults(self, posts_per_classification_per_language):
        """Treat every classification as its own literal translation into every other language.

        ``posts_per_classification_per_language`` should be the first argument
        to ``Taxonomy.postprocess_posts_per_classification``.
        """
        # First collect all classifications from all languages
        all_classifications = set()
        for _, classifications in posts_per_classification_per_language.items():
            all_classifications.update(classifications.keys())
        # Next, add translation records for all of them
        for classification in all_classifications:
            record = {tlang: classification for tlang in posts_per_classification_per_language}
            self.add_translation(record)

    def read_from_config(self, site, basename, posts_per_classification_per_language, add_defaults_default):
        """Read translations from config.

        ``site`` should be the Nikola site object. Will consider
        the variables ``<basename>_TRANSLATIONS`` and
        ``<basename>_TRANSLATIONS_ADD_DEFAULTS``.

        ``posts_per_classification_per_language`` should be the first argument
        to ``Taxonomy.postprocess_posts_per_classification``, i.e. this function
        should be called from that function. ``add_defaults_default`` specifies
        what the default value for ``<basename>_TRANSLATIONS_ADD_DEFAULTS`` is.

        Also sends signal via blinker to allow interested plugins to add
        translations by themselves. The signal name used is
        ``<lower(basename)>_translations_config``, and the argument is a dict
        with entries ``translation_manager``, ``site`` and
        ``posts_per_classification_per_language``.
        """
        # Add translations
        for record in site.config.get('{}_TRANSLATIONS'.format(basename), []):
            self.add_translation(record)
        # Add default translations
        if site.config.get('{}_TRANSLATIONS_ADD_DEFAULTS'.format(basename), add_defaults_default):
            self.add_defaults(posts_per_classification_per_language)
        # Use blinker to inform interested parties (plugins) that they can add
        # translations themselves
        args = {'translation_manager': self, 'site': site,
                'posts_per_classification_per_language': posts_per_classification_per_language}
        signal('{}_translations_config'.format(basename.lower())).send(args)
