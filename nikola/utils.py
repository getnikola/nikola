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

"""Utility functions."""

from __future__ import print_function, unicode_literals
from collections import defaultdict, Callable
import calendar
import datetime
import hashlib
import locale
import logging
import os
import re
import codecs
import json
import shutil
import subprocess
import sys
from zipfile import ZipFile as zip
try:
    from imp import reload
except ImportError:
    pass

import logbook
from logbook.more import ExceptionHandler
import pytz


class ApplicationWarning(Exception):
    pass


def get_logger(name, handlers):
    """Get a logger with handlers attached."""
    l = logbook.Logger(name)
    for h in handlers:
        if isinstance(h, list):
            l.handlers += h
        else:
            l.handlers.append(h)
    return l


STDERR_HANDLER = [logbook.StderrHandler(
    level=logbook.NOTICE if not os.getenv('NIKOLA_DEBUG') else logbook.DEBUG,
    format_string=u'[{record.time:%Y-%m-%dT%H:%M:%SZ}] {record.level_name}: {record.channel}: {record.message}'
)]
LOGGER = get_logger('Nikola', STDERR_HANDLER)
STRICT_HANDLER = ExceptionHandler(ApplicationWarning, level='WARNING')

if os.getenv('NIKOLA_DEBUG'):
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.WARNING)


def req_missing(names, purpose, python=True, optional=False):
    """Log that we are missing some requirements."""
    if not (isinstance(names, tuple) or isinstance(names, list) or isinstance(names, set)):
        names = (names,)
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
        raise Exception('Missing dependencies: {0}'.format(', '.join(names)))

    return msg

if sys.version_info[0] == 3:
    # Python 3
    bytes_str = bytes
    unicode_str = str
    unichr = chr
    from imp import reload as _reload
else:
    bytes_str = str
    unicode_str = unicode  # NOQA
    _reload = reload  # NOQA
    unichr = unichr

from doit import tools
from unidecode import unidecode

import PyRSS2Gen as rss

__all__ = ['get_theme_path', 'get_theme_chain', 'load_messages', 'copy_tree',
           'generic_rss_renderer', 'copy_file', 'slugify', 'unslugify',
           'to_datetime', 'apply_filters', 'config_changed', 'get_crumbs',
           'get_tzname', 'get_asset_path', '_reload', 'unicode_str', 'bytes_str',
           'unichr', 'Functionary', 'LocaleBorg', 'sys_encode', 'sys_decode',
           'makedirs', 'get_parent_theme_name', 'ExtendedRSS2', 'demote_headers']


ENCODING = sys.getfilesystemencoding() or sys.stdin.encoding


def sys_encode(thing):
    """Return bytes encoded in the system's encoding."""
    if isinstance(thing, unicode_str):
        return thing.encode(ENCODING)
    return thing


def sys_decode(thing):
    """Returns unicode."""
    if isinstance(thing, bytes_str):
        return thing.decode(ENCODING)
    return thing


def makedirs(path):
    """Create a folder."""
    if not path or os.path.isdir(path):
        return
    if os.path.exists(path):
        raise OSError('Path {0} already exists and is not a folder.')
    os.makedirs(path)


class Functionary(defaultdict):

    """Class that looks like a function, but is a defaultdict."""

    def __init__(self, default, default_lang):
        super(Functionary, self).__init__(default)
        self.default_lang = default_lang

    def __call__(self, key, lang=None):
        """When called as a function, take an optional lang
        and return self[lang][key]."""

        if lang is None:
            lang = LocaleBorg().current_lang
        return self[lang][key]


class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        try:
            return json.JSONEncoder.default(self, obj)
        except TypeError:
            s = repr(obj).split('0x', 1)[0]
            return s


class config_changed(tools.config_changed):
    """ A copy of doit's but using pickle instead of serializing manually."""

    def _calc_digest(self):
        if isinstance(self.config, str):
            return self.config
        elif isinstance(self.config, dict):
            data = json.dumps(self.config, cls=CustomEncoder, sort_keys=True)
            if isinstance(data, str):  # pragma: no cover # python3
                byte_data = data.encode("utf-8")
            else:
                byte_data = data
            return hashlib.md5(byte_data).hexdigest()
        else:
            raise Exception('Invalid type of config_changed parameter -- got '
                            '{0}, must be string or dict'.format(type(
                                self.config)))

    def __repr__(self):
        return "Change with config: {0}".format(json.dumps(self.config,
                                                           cls=CustomEncoder))


def get_theme_path(theme):
    """Given a theme name, returns the path where its files are located.

    Looks in ./themes and in the place where themes go when installed.
    """
    dir_name = os.path.join('themes', theme)
    if os.path.isdir(dir_name):
        return dir_name
    dir_name = os.path.join(os.path.dirname(__file__),
                            'data', 'themes', theme)
    if os.path.isdir(dir_name):
        return dir_name
    raise Exception("Can't find theme '{0}'".format(theme))


def get_template_engine(themes):
    for theme_name in themes:
        engine_path = os.path.join(get_theme_path(theme_name), 'engine')
        if os.path.isfile(engine_path):
            with open(engine_path) as fd:
                return fd.readlines()[0].strip()
    # default
    return 'mako'


def get_parent_theme_name(theme_name):
    parent_path = os.path.join(get_theme_path(theme_name), 'parent')
    if os.path.isfile(parent_path):
        with open(parent_path) as fd:
            return fd.readlines()[0].strip()
    return None


def get_theme_chain(theme):
    """Create the full theme inheritance chain."""
    themes = [theme]

    while True:
        parent = get_parent_theme_name(themes[-1])
        # Avoid silly loops
        if parent is None or parent in themes:
            break
        themes.append(parent)
    return themes


warned = []


def load_messages(themes, translations, default_lang):
    """ Load theme's messages into context.

    All the messages from parent themes are loaded,
    and "younger" themes have priority.
    """
    messages = Functionary(dict, default_lang)
    oldpath = sys.path[:]
    for theme_name in themes[::-1]:
        msg_folder = os.path.join(get_theme_path(theme_name), 'messages')
        default_folder = os.path.join(get_theme_path('base'), 'messages')
        sys.path.insert(0, default_folder)
        sys.path.insert(0, msg_folder)
        english = __import__('messages_en')
        for lang in list(translations.keys()):
            # If we don't do the reload, the module is cached
            translation = __import__('messages_' + lang)
            reload(translation)
            if sorted(translation.MESSAGES.keys()) !=\
                    sorted(english.MESSAGES.keys()) and \
                    lang not in warned:
                warned.append(lang)
                LOGGER.warn("Incomplete translation for language "
                            "'{0}'.".format(lang))
            messages[lang].update(english.MESSAGES)
            messages[lang].update(translation.MESSAGES)
            del(translation)
    sys.path = oldpath
    return messages


def copy_tree(src, dst, link_cutoff=None):
    """Copy a src tree to the dst folder.

    Example:

    src = "themes/default/assets"
    dst = "output/assets"

    should copy "themes/defauts/assets/foo/bar" to
    "output/assets/foo/bar"

    if link_cutoff is set, then the links pointing at things
    *inside* that folder will stay as links, and links
    pointing *outside* that folder will be copied.
    """
    ignore = set(['.svn'])
    base_len = len(src.split(os.sep))
    for root, dirs, files in os.walk(src):
        root_parts = root.split(os.sep)
        if set(root_parts) & ignore:
            continue
        dst_dir = os.path.join(dst, *root_parts[base_len:])
        makedirs(dst_dir)
        for src_name in files:
            if src_name == '.DS_Store':
                continue
            dst_file = os.path.join(dst_dir, src_name)
            src_file = os.path.join(root, src_name)
            yield {
                'name': str(dst_file),
                'file_dep': [src_file],
                'targets': [dst_file],
                'actions': [(copy_file, (src_file, dst_file, link_cutoff))],
                'clean': True,
            }


def generic_rss_renderer(lang, title, link, description, timeline, output_path,
                         rss_teasers, feed_length=10, feed_url=None):
    """Takes all necessary data, and renders a RSS feed in output_path."""
    items = []
    for post in timeline[:feed_length]:
        args = {
            'title': post.title(lang),
            'link': post.permalink(lang, absolute=True),
            'description': post.text(lang, teaser_only=rss_teasers, really_absolute=True),
            'guid': post.permalink(lang, absolute=True),
            # PyRSS2Gen's pubDate is GMT time.
            'pubDate': (post.date if post.date.tzinfo is None else
                        post.date.astimezone(pytz.timezone('UTC'))),
            'categories': post._tags.get(lang, []),
            'author': post.meta('author'),
        }

        items.append(ExtendedItem(**args))
    rss_obj = ExtendedRSS2(
        title=title,
        link=link,
        description=description,
        lastBuildDate=datetime.datetime.now(),
        items=items,
        generator='nikola',
        language=lang
    )
    rss_obj.self_url = feed_url
    rss_obj.rss_attrs["xmlns:atom"] = "http://www.w3.org/2005/Atom"
    rss_obj.rss_attrs["xmlns:dc"] = "http://purl.org/dc/elements/1.1/"
    dst_dir = os.path.dirname(output_path)
    makedirs(dst_dir)
    with codecs.open(output_path, "wb+", "utf-8") as rss_file:
        data = rss_obj.to_xml(encoding='utf-8')
        if isinstance(data, bytes_str):
            data = data.decode('utf-8')
        rss_file.write(data)


def copy_file(source, dest, cutoff=None):
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
    if os.path.isdir(source):
        shutil.rmtree(source)
    elif os.path.isfile(source) or os.path.islink(source):
        os.remove(source)

# slugify is copied from
# http://code.activestate.com/recipes/
# 577257-slugify-make-a-string-usable-in-a-url-or-filename/
_slugify_strip_re = re.compile(r'[^\w\s-]')
_slugify_hyphenate_re = re.compile(r'[-\s]+')


def slugify(value):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.

    From Django's "django/template/defaultfilters.py".

    >>> print(slugify('\xe1\xe9\xed.\xf3\xfa'))
    aeiou

    >>> print(slugify('foo/bar'))
    foobar

    >>> print(slugify('foo bar'))
    foo-bar

    """
    if not isinstance(value, unicode_str):
        raise ValueError("Not a unicode object: {0}".format(value))
    value = unidecode(value)
    # WARNING: this may not be python2/3 equivalent
    # value = unicode(_slugify_strip_re.sub('', value).strip().lower())
    value = str(_slugify_strip_re.sub('', value).strip().lower())
    return _slugify_hyphenate_re.sub('-', value)


def unslugify(value):
    """
    Given a slug string (as a filename), return a human readable string
    """
    value = re.sub('^[0-9]+', '', value)
    value = re.sub('([_\-\.])', ' ', value)
    value = value.strip().capitalize()
    return value


# A very slightly safer version of zip.extractall that works on
# python < 2.6

class UnsafeZipException(Exception):
    pass


def extract_all(zipfile, path='themes'):
    pwd = os.getcwd()
    makedirs(path)
    os.chdir(path)
    with zip(zipfile) as z:
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
    os.chdir(pwd)


# From https://github.com/lepture/liquidluck/blob/develop/liquidluck/utils.py
def to_datetime(value, tzinfo=None):
    if isinstance(value, datetime.datetime):
        return value
    supported_formats = [
        '%Y/%m/%d %H:%M',
        '%Y/%m/%d %H:%M:%S',
        '%Y/%m/%d %I:%M:%S %p',
        '%a %b %d %H:%M:%S %Y',
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d %H:%M',
        '%Y-%m-%dT%H:%M',
        '%Y%m%d %H:%M:%S',
        '%Y%m%d %H:%M',
        '%Y-%m-%d',
        '%Y%m%d',
    ]
    for format in supported_formats:
        try:
            dt = datetime.datetime.strptime(value, format)
            if tzinfo is None:
                return dt
            # Build a localized time by using a given time zone.
            return tzinfo.localize(dt)
        except ValueError:
            pass
    # So, let's try dateutil
    try:
        from dateutil import parser
        dt = parser.parse(value)
        if tzinfo is None or dt.tzinfo:
            return dt
        return tzinfo.localize(dt)
    except ImportError:
        raise ValueError('Unrecognized date/time: {0!r}, try installing dateutil...'.format(value))
    except Exception:
        raise ValueError('Unrecognized date/time: {0!r}'.format(value))


def get_tzname(dt):
    """
    Given a datetime value, find the name of the time zone.
    """
    try:
        from dateutil import tz
    except ImportError:
        raise ValueError('Unrecognized date/time: {0!r}, try installing dateutil...'.format(dt))

    tzoffset = dt.strftime('%z')
    for name in pytz.common_timezones:
        timezone = tz.gettz(name)
        now = dt.now(timezone)
        offset = now.strftime('%z')
        if offset == tzoffset:
            return name
    raise ValueError('Unrecognized date/time: {0!r}'.format(dt))


def current_time(tzinfo=None):
    dt = datetime.datetime.now()
    if tzinfo is not None:
        dt = tzinfo.localize(dt)
    return dt


def apply_filters(task, filters):
    """
    Given a task, checks its targets.
    If any of the targets has a filter that matches,
    adds the filter commands to the commands of the task,
    and the filter itself to the uptodate of the task.
    """

    def filter_matches(ext):
        for key, value in list(filters.items()):
            if isinstance(key, (tuple, list)):
                if ext in key:
                    return value
            elif isinstance(key, (bytes_str, unicode_str)):
                if ext == key:
                    return value
            else:
                assert False, key

    for target in task.get('targets', []):
        ext = os.path.splitext(target)[-1].lower()
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


def get_crumbs(path, is_file=False, index_folder=None):
    """Create proper links for a crumb bar. 
    index_folder is used if you want to use title from index file 
    instead of folder name as breadcrumb text. 

    >>> crumbs = get_crumbs('galleries')
    >>> len(crumbs)
    1
    >>> print('|'.join(crumbs[0]))
    #|galleries

    >>> crumbs = get_crumbs(os.path.join('galleries','demo'))
    >>> len(crumbs)
    2
    >>> print('|'.join(crumbs[0]))
    ..|galleries
    >>> print('|'.join(crumbs[1]))
    #|demo

    >>> crumbs = get_crumbs(os.path.join('listings','foo','bar'), is_file=True)
    >>> len(crumbs)
    3
    >>> print('|'.join(crumbs[0]))
    ..|listings
    >>> print('|'.join(crumbs[1]))
    .|foo
    >>> print('|'.join(crumbs[2]))
    #|bar
    """

    crumbs = path.split(os.sep)
    _crumbs = []
    if is_file:
        for i, crumb in enumerate(crumbs[-3::-1]):  # Up to parent folder only
            _path = '/'.join(['..'] * (i + 1))
            _crumbs.append([_path, crumb])
        _crumbs.insert(0, ['.', crumbs[-2]])  # file's folder
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
            index_post = index_folder.parse_index(folder)
            folder = folder.replace(crumb, '')
            if index_post:
                crumb = index_post.title() or crumb
            _crumbs[i][1] = crumb
    return list(reversed(_crumbs))


def get_asset_path(path, themes, files_folders={'files': ''}):
    """
    .. versionchanged:: 6.1.0

    Checks which theme provides the path with the given asset,
    and returns the "real", absolute path to the asset.

    If the asset is not provided by a theme, then it will be checked for
    in the FILES_FOLDERS

    >>> print(get_asset_path('assets/css/rst.css', ['bootstrap', 'base'])) # doctest: +SKIP
    [...]/nikola/data/themes/base/assets/css/rst.css

    >>> print(get_asset_path('assets/css/theme.css', ['bootstrap', 'base'])) # doctest: +SKIP
    [...]/nikola/data/themes/bootstrap/assets/css/theme.css

    >>> print(get_asset_path('nikola.py', ['bootstrap', 'base'], {'nikola': ''})) # doctest: +SKIP
    [...]/nikola/nikola.py

    >>> print(get_asset_path('nikola/nikola.py', ['bootstrap', 'base'], {'nikola':'nikola'})) # doctest: +SKIP
    [...]/nikola/nikola.py

    """
    for theme_name in themes:
        candidate = os.path.join(
            get_theme_path(theme_name),
            path
        )
        if os.path.isfile(candidate):
            return candidate
    for src, rel_dst in files_folders.items():
        candidate = os.path.abspath(os.path.join(src, path))
        if os.path.isfile(candidate):
            return candidate

    # whatever!
    return None


class LocaleBorg(object):
    """
    Provides locale related services and autoritative current_lang,
    where current_lang is the last lang for which the locale was set.

    current_lang is meant to be set only by LocaleBorg.set_locale

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
    That used to break calendar, but now seems is not the case, with month at least
    """
    @classmethod
    def initialize(cls, locales, initial_lang):
        """
        locales : dict with lang: locale_n
            the same keys as in nikola's TRANSLATIONS
            locale_n a sanitized locale, meaning
                locale.setlocale(locale.LC_ALL, locale_n) will succeed
                locale_n expressed in the string form, like "en.utf8"
        """
        assert initial_lang is not None and initial_lang in locales
        cls.reset()
        cls.locales = locales

        # needed to decode some localized output in py2x
        encodings = {}
        for lang in locales:
            locale.setlocale(locale.LC_ALL, locales[lang])
            loc, encoding = locale.getlocale()
            encodings[lang] = encoding

        cls.encodings = encodings
        cls.__shared_state['current_lang'] = initial_lang
        cls.initialized = True

    @classmethod
    def reset(cls):
        """used in testing to not leak state between tests"""
        cls.locales = {}
        cls.encodings = {}
        cls.__shared_state = {'current_lang': None}
        cls.initialized = False

    def __init__(self):
        if not self.initialized:
            raise Exception("Attempt to use LocaleBorg before initialization")
        self.__dict__ = self.__shared_state

    def set_locale(self, lang):
        """Sets the locale for language lang, returns ''

        in linux the locale encoding is set to utf8,
        in windows that cannot be guaranted.
        In either case, the locale encoding is available in cls.encodings[lang]
        """
        # intentional non try-except: templates must ask locales with a lang,
        # let the code explode here and not hide the point of failure
        # Also, not guarded with an if lang==current_lang because calendar may
        # put that out of sync
        locale_n = self.locales[lang]
        self.__shared_state['current_lang'] = lang
        locale.setlocale(locale.LC_ALL, locale_n)
        return ''

    def get_month_name(self, month_no, lang):
        """returns localized month name in an unicode string"""
        if sys.version_info[0] == 3:  # Python 3
            with calendar.different_locale(self.locales[lang]):
                s = calendar.month_name[month_no]
            # for py3 s is unicode
        else:  # Python 2
            with calendar.TimeEncoding(self.locales[lang]):
                s = calendar.month_name[month_no]
            s = s.decode(self.encodings[lang])
        # paranoid about calendar ending in the wrong locale (windows)
        self.set_locale(self.current_lang)
        return s


class ExtendedRSS2(rss.RSS2):
    def publish_extensions(self, handler):
        if self.self_url:
            handler.startElement("atom:link", {
                'href': self.self_url,
                'rel': "self",
                'type': "application/rss+xml"
            })
            handler.endElement("atom:link")


class ExtendedItem(rss.RSSItem):

    def __init__(self, **kw):
        author = kw.pop('author')
        if author and '@' in author[1:]:  # Yes, this is a silly way to validate an email
            kw['author'] = author
            self.creator = None
        else:
            self.creator = author
        # It's an old style class
        return rss.RSSItem.__init__(self, **kw)

    def publish_extensions(self, handler):
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
    """extract first non-blank line from text, to extract docstring title"""
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
    """Find root directory of nikola installation by looking for conf.py"""
    root = os.getcwd()

    while True:
        if os.path.exists(os.path.join(root, 'conf.py')):
            return root
        else:
            basedir = os.path.split(root)[0]
            # Top directory, already checked
            if basedir == root:
                break
            root = basedir

    return None
