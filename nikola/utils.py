# -*- coding: utf-8 -*-

# Copyright © 2012-2017 Roberto Alsina and others.

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

from __future__ import print_function, unicode_literals, absolute_import
import calendar
import configparser
import datetime
import dateutil.tz
import hashlib
import io
import locale
import logging
import natsort
import operator
import os
import re
import json
import shutil
import socket
import subprocess
import sys
import dateutil.parser
import dateutil.tz
import logbook
try:
    from urllib import quote as urlquote
    from urllib import unquote as urlunquote
    from urlparse import urlparse, urlunparse
except ImportError:
    from urllib.parse import quote as urlquote  # NOQA
    from urllib.parse import unquote as urlunquote  # NOQA
    from urllib.parse import urlparse, urlunparse  # NOQA
import warnings
import PyRSS2Gen as rss
try:
    import pytoml as toml
except ImportError:
    toml = None
try:
    import yaml
except ImportError:
    yaml = None
try:
    import husl
except ImportError:
    husl = None

from blinker import signal
from collections import defaultdict, Callable, OrderedDict
from logbook.compat import redirect_logging
from logbook.more import ExceptionHandler, ColorizedStderrHandler
from pygments.formatters import HtmlFormatter
from zipfile import ZipFile as zipf
from doit import tools
from unidecode import unidecode
from unicodedata import normalize as unicodenormalize
from pkg_resources import resource_filename
from doit.cmdparse import CmdParse

from nikola import DEBUG

__all__ = ('CustomEncoder', 'get_theme_path', 'get_theme_path_real',
           'get_theme_chain', 'load_messages', 'copy_tree', 'copy_file',
           'slugify', 'unslugify', 'to_datetime', 'apply_filters',
           'config_changed', 'get_crumbs', 'get_tzname', 'get_asset_path',
           '_reload', 'unicode_str', 'bytes_str', 'unichr', 'Functionary',
           'TranslatableSetting', 'TemplateHookRegistry', 'LocaleBorg',
           'sys_encode', 'sys_decode', 'makedirs', 'get_parent_theme_name',
           'demote_headers', 'get_translation_candidate', 'write_metadata',
           'ask', 'ask_yesno', 'options2docstring', 'os_path_split',
           'get_displayed_page_number', 'adjust_name_for_index_path_list',
           'adjust_name_for_index_path', 'adjust_name_for_index_link',
           'NikolaPygmentsHTML', 'create_redirect', 'clean_before_deployment',
           'sort_posts', 'indent', 'load_data', 'html_unescape', 'rss_writer',
           'map_metadata',
           # Deprecated, moved to hierarchy_utils:
           'TreeNode', 'clone_treenode', 'flatten_tree_structure',
           'sort_classifications', 'join_hierarchical_category_path',
           'parse_escaped_hierarchical_category_name',)

from .hierarchy_utils import TreeNode, clone_treenode, flatten_tree_structure, sort_classifications
from .hierarchy_utils import join_hierarchical_category_path, parse_escaped_hierarchical_category_name

# Are you looking for 'generic_rss_renderer'?
# It's defined in nikola.nikola.Nikola (the site object).

if sys.version_info[0] == 3:
    # Python 3
    bytes_str = bytes
    unicode_str = str
    unichr = chr
    raw_input = input
    from imp import reload as _reload
else:
    bytes_str = str
    unicode_str = unicode  # NOQA
    _reload = reload  # NOQA
    unichr = unichr


class ApplicationWarning(Exception):
    pass


class ColorfulStderrHandler(ColorizedStderrHandler):
    """Stream handler with colors."""

    _colorful = False

    def should_colorize(self, record):
        """Inform about colorization using the value obtained from Nikola."""
        return self._colorful


def get_logger(name, handlers):
    """Get a logger with handlers attached."""
    l = logbook.Logger(name)
    for h in handlers:
        if isinstance(h, list):
            l.handlers += h
        else:
            l.handlers.append(h)
    return l


STDERR_HANDLER = [ColorfulStderrHandler(
    level=logbook.INFO if not DEBUG else logbook.DEBUG,
    format_string=u'[{record.time:%Y-%m-%dT%H:%M:%SZ}] {record.level_name}: {record.channel}: {record.message}'
)]


LOGGER = get_logger('Nikola', STDERR_HANDLER)
STRICT_HANDLER = ExceptionHandler(ApplicationWarning, level='WARNING')

USE_SLUGIFY = True

redirect_logging()

if DEBUG:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)


def showwarning(message, category, filename, lineno, file=None, line=None):
    """Show a warning (from the warnings module) to the user."""
    try:
        n = category.__name__
    except AttributeError:
        n = str(category)
    get_logger(n, STDERR_HANDLER).warn('{0}:{1}: {2}'.format(filename, lineno, message))


warnings.showwarning = showwarning


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
        LOGGER.warn(msg)
    else:
        LOGGER.error(msg)
        LOGGER.error('Exiting due to missing dependencies.')
        sys.exit(5)

    return msg


ENCODING = sys.getfilesystemencoding() or sys.stdin.encoding


def sys_encode(thing):
    """Return bytes encoded in the system's encoding."""
    if isinstance(thing, unicode_str):
        return thing.encode(ENCODING)
    return thing


def sys_decode(thing):
    """Return Unicode."""
    if isinstance(thing, bytes_str):
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
        super(Functionary, self).__init__(default)
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
            return super(TranslatableSetting, self).__getattribute__(attr)
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
        return self.values[self.get_lang()]

    def __unicode__(self):
        """Return the value in the currently set language (deprecated)."""
        return self.values[self.get_lang()]

    def __repr__(self):
        """Provide a representation for programmers."""
        return '<TranslatableSetting: {0!r}>'.format(self.name)

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
            return super(CustomEncoder, self).default(obj)
        except TypeError:
            if isinstance(obj, (set, frozenset)):
                return self.encode(sorted(list(obj)))
            else:
                s = repr(obj).split('0x', 1)[0]
            return s


class config_changed(tools.config_changed):
    """A copy of doit's config_changed, using pickle instead of serializing manually."""

    def __init__(self, config, identifier=None):
        """Initialize config_changed."""
        super(config_changed, self).__init__(config)
        self.identifier = '_config_changed'
        if identifier is not None:
            self.identifier += ':' + identifier

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


language_incomplete_warned = []


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
    for theme_name in themes[::-1]:
        msg_folder = os.path.join(get_theme_path(theme_name), 'messages')
        default_folder = os.path.join(get_theme_path_real('base', themes_dirs), 'messages')
        sys.path.insert(0, default_folder)
        sys.path.insert(0, msg_folder)
        english = __import__('messages_en')
        # If we don't do the reload, the module is cached
        _reload(english)
        for lang in list(translations.keys()):
            try:
                translation = __import__('messages_' + lang)
                # If we don't do the reload, the module is cached
                _reload(translation)
                if sorted(translation.MESSAGES.keys()) !=\
                        sorted(english.MESSAGES.keys()) and \
                        lang not in language_incomplete_warned:
                    language_incomplete_warned.append(lang)
                    LOGGER.warn("Incomplete translation for language "
                                "'{0}'.".format(lang))
                messages[lang].update(english.MESSAGES)
                for k, v in translation.MESSAGES.items():
                    if v:
                        messages[lang][k] = v
                del(translation)
            except ImportError as orig:
                raise LanguageNotFoundError(lang, orig)
        del(english)
    sys.path = oldpath
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
# http://code.activestate.com/recipes/
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
    if lang is None:  # TODO: remove in v8
        LOGGER.warn("slugify() called without language!")
    if not isinstance(value, unicode_str):
        raise ValueError("Not a unicode object: {0}".format(value))
    if USE_SLUGIFY or force:
        # This is the standard state of slugify, which actually does some work.
        # It is the preferred style, especially for Western languages.
        value = unicode_str(unidecode(value))
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
    if lang is None:  # TODO: remove in v8
        LOGGER.warn("unslugify() called without language!")
    if discard_numbers:
        value = re.sub('^[0-9]+', '', value)
    value = re.sub('([_\-\.])', ' ', value)
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
            elif isinstance(key, (bytes_str, unicode_str)):
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

    >>> print(get_asset_path('assets/css/rst.css', get_theme_chain('bootstrap3', ['themes'])))
    /.../nikola/data/themes/base/assets/css/rst.css

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
        super(LocaleBorgUninitializedException, self).__init__("Attempt to use LocaleBorg before initialization")


class LocaleBorg(object):
    """Provide locale related services and autoritative current_lang.

    current_lang is the last lang for which the locale was set
    and is meant to be set only by LocaleBorg.set_locale.

    python's locale code should not be directly called from code outside of
    LocaleBorg, they are compatibilty issues with py version and OS support
    better handled at one central point, LocaleBorg.

    In particular, don't call locale.setlocale outside of LocaleBorg.

    Assumptions:
        We need locales only for the languages there is a nikola translation.
        We don't need to support current_lang through nested contexts

    Usage:
        # early in cmd or test execution
        LocaleBorg.initialize(...)

        # any time later
        lang = LocaleBorg().<service>

    Available services:
        .current_lang : autoritative current_lang , the last seen in set_locale
        .set_locale(lang) : sets current_lang and sets the locale for lang
        .get_month_name(month_no, lang) : returns the localized month name

    NOTE: never use locale.getlocale() , it can return values that
    locale.setlocale will not accept in Windows XP, 7 and pythons 2.6, 2.7, 3.3
    Examples: "Spanish", "French" can't do the full circle set / get / set
    """

    initialized = False

    @classmethod
    def initialize(cls, locales, initial_lang):
        """Initialize LocaleBorg.

        locales : dict with lang: locale_n
            the same keys as in nikola's TRANSLATIONS
            locale_n a sanitized locale, meaning
                locale.setlocale(locale.LC_ALL, locale_n) will succeed
                locale_n expressed in the string form, like "en.utf8"
        """
        if initial_lang is None or initial_lang not in locales:
            raise ValueError("Unknown initial language {0}".format(initial_lang))
        cls.reset()
        cls.locales = locales
        cls.month_name_handlers = []
        cls.formatted_date_handlers = []

        # needed to decode some localized output in py2x
        encodings = {}
        for lang in locales:
            locale.setlocale(locale.LC_ALL, locales[lang])
            loc, encoding = locale.getlocale()
            encodings[lang] = encoding

        cls.encodings = encodings
        cls.__initial_lang = initial_lang
        cls.initialized = True

    def __get_shared_state(self):
        if not self.initialized:
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
        import threading
        cls.__thread_local = threading.local()
        cls.__thread_lock = threading.Lock()

        cls.locales = {}
        cls.encodings = {}
        cls.initialized = False
        cls.month_name_handlers = []
        cls.formatted_date_handlers = []
        cls.thread_local = None
        cls.thread_lock = None

    @classmethod
    def add_handler(cls, month_name_handler=None, formatted_date_handler=None):
        """Allow to add month name and formatted date handlers.

        If month_name_handler is not None, it is expected to be a callable
        which accepts (month_no, lang) and returns either a string or None.

        If formatted_date_handler is not None, it is expected to be a callable
        which accepts (date_format, date, lang) and returns either a string or
        None.

        A handler is expected to either return the correct result for the given
        language and data, or return None to indicate it is not able to do the
        job. In that case, the next handler is asked, and finally the default
        implementation is used.
        """
        if month_name_handler is not None:
            cls.month_name_handlers.append(month_name_handler)
        if formatted_date_handler is not None:
            cls.formatted_date_handlers.append(formatted_date_handler)

    def __init__(self):
        """Initialize."""
        if not self.initialized:
            raise LocaleBorgUninitializedException()

    @property
    def current_lang(self):
        """Return the current language."""
        return self.__get_shared_state()['current_lang']

    def __set_locale(self, lang):
        """Set the locale for language lang without updating current_lang."""
        locale_n = self.locales[lang]
        locale.setlocale(locale.LC_ALL, locale_n)

    def set_locale(self, lang):
        """Set the locale for language lang, returns an empty string.

        in linux the locale encoding is set to utf8,
        in windows that cannot be guaranted.
        In either case, the locale encoding is available in cls.encodings[lang]
        """
        with self.__thread_lock:
            # intentional non try-except: templates must ask locales with a lang,
            # let the code explode here and not hide the point of failure
            # Also, not guarded with an if lang==current_lang because calendar may
            # put that out of sync
            self.__set_locale(lang)
            self.__get_shared_state()['current_lang'] = lang
            return ''

    def get_month_name(self, month_no, lang):
        """Return localized month name in an unicode string."""
        # For thread-safety
        with self.__thread_lock:
            for handler in self.month_name_handlers:
                res = handler(month_no, lang)
                if res is not None:
                    return res
            old_lang = self.current_lang
            self.__set_locale(lang)
            s = calendar.month_name[month_no]
            self.__set_locale(old_lang)
            if sys.version_info[0] == 2:
                enc = self.encodings[lang]
                if not enc:
                    enc = 'UTF-8'

                s = s.decode(enc)
            return s

    def formatted_date(self, date_format, date):
        """Return the formatted date as unicode."""
        with self.__thread_lock:
            current_lang = self.current_lang
            # For thread-safety
            self.__set_locale(current_lang)
            fmt_date = None
            # Get a string out of a TranslatableSetting
            if isinstance(date_format, TranslatableSetting):
                date_format = date_format(current_lang)
            # Always ask Python if the date_format is webiso
            if date_format == 'webiso':
                # Formatted after RFC 3339 (web ISO 8501 profile) with Zulu
                # zone designator for times in UTC and no microsecond precision.
                fmt_date = date.replace(microsecond=0).isoformat().replace('+00:00', 'Z')
            # If not, check handlers
            else:
                for handler in self.formatted_date_handlers:
                    fmt_date = handler(date_format, date, current_lang)
                    if fmt_date is not None:
                        break
                # If no handler was able to format the date, ask Python
                if fmt_date is None:
                    fmt_date = date.strftime(date_format)

            # Issue #383, this changes from py2 to py3
            if isinstance(fmt_date, bytes_str):
                fmt_date = fmt_date.decode('utf8')
            return fmt_date


class ExtendedRSS2(rss.RSS2):
    """Extended RSS class."""

    xsl_stylesheet_href = None

    def publish(self, handler):
        """Publish a feed."""
        if self.xsl_stylesheet_href:
            handler.processingInstruction("xml-stylesheet", 'type="text/xsl" href="{0}" media="all"'.format(self.xsl_stylesheet_href))
        # old-style class in py2
        rss.RSS2.publish(self, handler)

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
        r = range(1, 7 - level)
    elif level < 0:
        r = range(1 + level, 7)
    for i in reversed(r):
        # html headers go to 6, so we can’t “lower” beneath five
        elements = doc.xpath('//h' + str(i))
        for e in elements:
            e.tag = 'h' + str(i + level)


def get_root_dir():
    """Find root directory of nikola site by looking for conf.py."""
    root = os.getcwd()

    if sys.version_info[0] == 2:
        confname = b'conf.py'
    else:
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
    pattern = pattern.replace('{ext}', '(?P<ext>[^\./]+)')
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


def write_metadata(data, _format='nikola'):
    """Write metadata."""
    _format = _format.lower()
    if _format not in ['nikola', 'yaml', 'toml', 'pelican_rest', 'pelican_md']:
        LOGGER.warn('Unknown METADATA_FORMAT %s, using "nikola" format', _format)

    if _format == 'yaml':
        if yaml is None:
            req_missing('pyyaml', 'use YAML metadata', optional=False)
        return '\n'.join(('---', yaml.safe_dump(data, default_flow_style=False).strip(), '---', '', ''))

    elif _format == 'toml':
        if toml is None:
            req_missing('toml', 'use TOML metadata', optional=False)
        return '\n'.join(('+++', toml.dumps(data).strip(), '+++', '', ''))

    elif _format == 'pelican_rest':
        title = data.pop('title')
        results = [
            '=' * len(title),
            title,
            '=' * len(title),
            ''
        ] + [':{0}: {1}'.format(k, v) for k, v in data.items() if v] + ['']
        return '\n'.join(results)

    elif _format == 'pelican_md':
        results = ['{0}: {1}'.format(k, v) for k, v in data.items() if v] + ['', '']
        return '\n'.join(results)

    else:  # Nikola, default
        order = ('title', 'slug', 'date', 'tags', 'category', 'link', 'description', 'type')
        f = '.. {0}: {1}'
        meta = []
        for k in order:
            try:
                meta.append(f.format(k, data.pop(k)))
            except KeyError:
                pass
        # Leftover metadata (user-specified/non-default).
        for k in natsort.natsorted(list(data.keys()), alg=natsort.ns.F | natsort.ns.IC):
            meta.append(f.format(k, data[k]))
        meta.append('')
        return '\n'.join(meta)


def ask(query, default=None):
    """Ask a question."""
    if default:
        default_q = ' [{0}]'.format(default)
    else:
        default_q = ''
    if sys.version_info[0] == 3:
        inp = raw_input("{query}{default_q}: ".format(query=query, default_q=default_q)).strip()
    else:
        inp = raw_input("{query}{default_q}: ".format(query=query, default_q=default_q).encode('utf-8')).strip()
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
    if sys.version_info[0] == 3:
        inp = raw_input("{query}{default_q} ".format(query=query, default_q=default_q)).strip()
    else:
        inp = raw_input("{query}{default_q} ".format(query=query, default_q=default_q).encode('utf-8')).strip()
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
            if sys.version_info[0] == 2:
                k2 = bytes(k)
            else:
                k2 = k

            self._cmdnames.append(k)

            try:
                # nikola command: already instantiated (singleton)
                opt = v.get_options()
            except TypeError:
                # doit command: needs some help
                opt = v(config=self._config, **self._doitargs).get_options()
            nc = type(
                k2,
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


class NikolaPygmentsHTML(HtmlFormatter):
    """A Nikola-specific modification of Pygments' HtmlFormatter."""

    def __init__(self, anchor_ref, classes=None, linenos='table', linenostart=1):
        """Initialize formatter."""
        if classes is None:
            classes = ['code', 'literal-block']
        self.nclasses = classes
        super(NikolaPygmentsHTML, self).__init__(
            cssclass='code', linenos=linenos, linenostart=linenostart, nowrap=False,
            lineanchors=slugify(anchor_ref, lang=LocaleBorg().current_lang, force=True), anchorlinenos=True)

    def wrap(self, source, outfile):
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
            if isinstance(path_schema, (bytes_str, unicode_str)):
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
    lightness and saturation untouched using HUSL colorspace.
    """
    def hash_str(string, pos):
        x = hashlib.md5(string.encode('utf-8')).digest()[pos]
        try:
            # Python 2: a string
            # TODO: remove in v8
            return ord(x)
        except TypeError:
            # Python 3: already an integer
            return x

    def degreediff(dega, degb):
        return min(abs(dega - degb), abs((degb - dega) + 360))

    if husl is None:
        req_missing(['husl'], 'Use color mixing (section colors)',
                    optional=True)
        return base_color
    h, s, l = husl.hex_to_husl(base_color)
    old_h = h
    idx = 0
    while degreediff(old_h, h) < 27 and idx < 16:
        h = 360.0 * (float(hash_str(string, idx)) / 255)
        idx += 1
    return husl.husl_to_hex(h, s, l)


def color_hsl_adjust_hex(hexstr, adjust_h=None, adjust_s=None, adjust_l=None):
    """Adjust a hex color using HSL arguments, adjustments in percentages 1.0 to -1.0. Returns a hex color."""
    h, s, l = husl.hex_to_husl(hexstr)

    if adjust_h:
        h = h + (adjust_h * 360.0)

    if adjust_s:
        s = s + (adjust_s * 100.0)

    if adjust_l:
        l = l + (adjust_l * 100.0)

    return husl.husl_to_hex(h, s, l)


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
        loader = yaml
        function = 'safe_load'
        if yaml is None:
            req_missing(['yaml'], 'use YAML data files')
            return {}
    elif ext in {'.json', '.js'}:
        loader = json
    elif ext in {'.toml', '.tml'}:
        if toml is None:
            req_missing(['toml'], 'use TOML data files')
            return {}
        loader = toml
    if loader is None:
        return
    with io.open(path, 'r', encoding='utf8') as inf:
        return getattr(loader, function)(inf)


# see http://stackoverflow.com/a/2087433
try:
    import html  # Python 3.4 and newer
    html_unescape = html.unescape
except (AttributeError, ImportError):
    try:
        from HTMLParser import HTMLParser  # Python 2.7
    except ImportError:
        from html.parser import HTMLParser  # Python 3 (up to 3.4)

    def html_unescape(s):
        """Convert all named and numeric character references in the string s to the corresponding unicode characters."""
        h = HTMLParser()
        return h.unescape(s)


def rss_writer(rss_obj, output_path):
    """Write an RSS object to an xml file."""
    dst_dir = os.path.dirname(output_path)
    makedirs(dst_dir)
    with io.open(output_path, "w+", encoding="utf-8") as rss_file:
        data = rss_obj.to_xml(encoding='utf-8')
        if isinstance(data, bytes_str):
            data = data.decode('utf-8')
        rss_file.write(data)


def map_metadata(meta, key, config):
    """Map metadata from other platforms to Nikola names.

    This uses the METADATA_MAPPING setting (via ``config``) and modifies the dict in place.
    """
    for foreign, ours in config.get('METADATA_MAPPING', {}).get(key, {}).items():
        if foreign in meta:
            meta[ours] = meta[foreign]


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
