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

"""Create a new post."""

from __future__ import unicode_literals, print_function
import io
import datetime
import operator
import os
import shutil
import subprocess
import sys

from blinker import signal
import dateutil.tz

from nikola.plugin_categories import Command
from nikola import utils

COMPILERS_DOC_LINK = 'https://getnikola.com/handbook.html#configuring-other-input-formats'
POSTLOGGER = utils.get_logger('new_post', utils.STDERR_HANDLER)
PAGELOGGER = utils.get_logger('new_page', utils.STDERR_HANDLER)
LOGGER = POSTLOGGER


def get_default_compiler(is_post, compilers, post_pages):
    """Given compilers and post_pages, return a reasonable default compiler for this kind of post/page."""
    # First throw away all the post_pages with the wrong is_post
    filtered = [entry for entry in post_pages if entry[3] == is_post]

    # Get extensions in filtered post_pages until one matches a compiler
    for entry in filtered:
        extension = os.path.splitext(entry[0])[-1]
        for compiler, extensions in compilers.items():
            if extension in extensions:
                return compiler
    # No idea, back to default behaviour
    return 'rest'


def get_date(schedule=False, rule=None, last_date=None, tz=None, iso8601=False):
    """Return a date stamp, given a recurrence rule.

    schedule - bool:
        whether to use the recurrence rule or not

    rule - str:
        an iCal RRULE string that specifies the rule for scheduling posts

    last_date - datetime:
        timestamp of the last post

    tz - tzinfo:
        the timezone used for getting the current time.

    iso8601 - bool:
        whether to force ISO 8601 dates (instead of locale-specific ones)

    """
    if tz is None:
        tz = dateutil.tz.tzlocal()
    date = now = datetime.datetime.now(tz)
    if schedule:
        try:
            from dateutil import rrule
        except ImportError:
            LOGGER.error('To use the --schedule switch of new_post, '
                         'you have to install the "dateutil" package.')
            rrule = None  # NOQA
    if schedule and rrule and rule:
        try:
            rule_ = rrule.rrulestr(rule, dtstart=last_date or date)
        except Exception:
            LOGGER.error('Unable to parse rule string, using current time.')
        else:
            date = rule_.after(max(now, last_date or now), last_date is None)

    offset = tz.utcoffset(now)
    offset_sec = (offset.days * 24 * 3600 + offset.seconds)
    offset_hrs = offset_sec // 3600
    offset_min = offset_sec % 3600
    if iso8601:
        tz_str = '{0:+03d}:{1:02d}'.format(offset_hrs, offset_min // 60)
    else:
        if offset:
            tz_str = ' UTC{0:+03d}:{1:02d}'.format(offset_hrs, offset_min // 60)
        else:
            tz_str = ' UTC'

    return (date.strftime('%Y-%m-%d %H:%M:%S') + tz_str, date)


class CommandNewPost(Command):
    """Create a new post."""

    name = "new_post"
    doc_usage = "[options] [path]"
    doc_purpose = "create a new blog post or site page"
    cmd_options = [
        {
            'name': 'is_page',
            'short': 'p',
            'long': 'page',
            'type': bool,
            'default': False,
            'help': 'Create a page instead of a blog post. (see also: `nikola new_page`)'
        },
        {
            'name': 'title',
            'short': 't',
            'long': 'title',
            'type': str,
            'default': '',
            'help': 'Title for the post.'
        },
        {
            'name': 'author',
            'short': 'a',
            'long': 'author',
            'type': str,
            'default': '',
            'help': 'Author of the post.'
        },
        {
            'name': 'tags',
            'long': 'tags',
            'type': str,
            'default': '',
            'help': 'Comma-separated tags for the post.'
        },
        {
            'name': 'onefile',
            'short': '1',
            'type': bool,
            'default': False,
            'help': 'Create the post with embedded metadata (single file format)'
        },
        {
            'name': 'twofile',
            'short': '2',
            'type': bool,
            'default': False,
            'help': 'Create the post with separate metadata (two file format)'
        },
        {
            'name': 'edit',
            'short': 'e',
            'type': bool,
            'default': False,
            'help': 'Open the post (and meta file, if any) in $EDITOR after creation.'
        },
        {
            'name': 'content_format',
            'short': 'f',
            'long': 'format',
            'type': str,
            'default': '',
            'help': 'Markup format for the post (use --available-formats for list)',
        },
        {
            'name': 'available-formats',
            'short': 'F',
            'long': 'available-formats',
            'type': bool,
            'default': False,
            'help': 'List all available input formats'
        },
        {
            'name': 'schedule',
            'short': 's',
            'type': bool,
            'default': False,
            'help': 'Schedule the post based on recurrence rule'
        },
        {
            'name': 'import',
            'short': 'i',
            'long': 'import',
            'type': str,
            'default': '',
            'help': 'Import an existing file instead of creating a placeholder'
        },
        {
            'name': 'date-path',
            'short': 'd',
            'long': 'date-path',
            'type': bool,
            'default': False,
            'help': 'Create post with date path (eg. year/month/day, see NEW_POST_DATE_PATH_FORMAT in config)'
        },
    ]

    def _execute(self, options, args):
        """Create a new post or page."""
        global LOGGER
        compiler_names = [p.name for p in
                          self.site.plugin_manager.getPluginsOfCategory(
                              "PageCompiler")]

        if len(args) > 1:
            print(self.help())
            return False
        elif args:
            path = args[0]
        else:
            path = None

        # Even though stuff was split into `new_page`, it’s easier to do it
        # here not to duplicate the code.
        is_page = options.get('is_page', False)
        is_post = not is_page
        content_type = 'page' if is_page else 'post'
        title = options['title'] or None
        author = options['author'] or ''
        tags = options['tags']
        onefile = options['onefile']
        twofile = options['twofile']
        import_file = options['import']
        wants_available = options['available-formats']
        date_path_opt = options['date-path']
        date_path_auto = self.site.config['NEW_POST_DATE_PATH'] and content_type == 'post'
        date_path_format = self.site.config['NEW_POST_DATE_PATH_FORMAT'].strip('/')

        if wants_available:
            self.print_compilers()
            return

        if is_page:
            LOGGER = PAGELOGGER
        else:
            LOGGER = POSTLOGGER

        if twofile:
            onefile = False
        if not onefile and not twofile:
            onefile = self.site.config.get('ONE_FILE_POSTS', True)

        content_format = options['content_format']
        content_subformat = None

        if "@" in content_format:
            content_format, content_subformat = content_format.split("@")

        if not content_format and path:
            # content_format not specified. If path was given, use
            # it to guess (Issue #2798)
            extension = os.path.splitext(path)[-1]
            for compiler, extensions in self.site.config['COMPILERS'].items():
                if extension in extensions:
                    content_format = compiler

        elif not content_format and import_file:
            # content_format not specified. If import_file was given, use
            # it to guess (Issue #2798)
            extension = os.path.splitext(import_file)[-1]
            for compiler, extensions in self.site.config['COMPILERS'].items():
                if extension in extensions:
                    content_format = compiler

        elif not content_format:  # Issue #400
            content_format = get_default_compiler(
                is_post,
                self.site.config['COMPILERS'],
                self.site.config['post_pages'])

        elif content_format not in compiler_names:
            LOGGER.error("Unknown {0} format {1}, maybe you need to install a plugin or enable an existing one?".format(content_type, content_format))
            self.print_compilers()
            return

        compiler_plugin = self.site.plugin_manager.getPluginByName(
            content_format, "PageCompiler").plugin_object

        # Guess where we should put this
        entry = self.filter_post_pages(content_format, is_post)

        if entry is False:
            return 1

        if import_file:
            print("Importing Existing {xx}".format(xx=content_type.title()))
            print("-----------------------\n")
        else:
            print("Creating New {xx}".format(xx=content_type.title()))
            print("-----------------\n")
        if title is not None:
            print("Title:", title)
        else:
            while not title:
                title = utils.ask('Title')

        if isinstance(title, utils.bytes_str):
            try:
                title = title.decode(sys.stdin.encoding)
            except (AttributeError, TypeError):  # for tests
                title = title.decode('utf-8')

        title = title.strip()
        if not path:
            slug = utils.slugify(title, lang=self.site.default_lang)
        else:
            if isinstance(path, utils.bytes_str):
                try:
                    path = path.decode(sys.stdin.encoding)
                except (AttributeError, TypeError):  # for tests
                    path = path.decode('utf-8')
            if os.path.isdir(path):
                # If the user provides a directory, add the file name generated from title (Issue #2651)
                slug = utils.slugify(title, lang=self.site.default_lang)
                pattern = os.path.basename(entry[0])
                suffix = pattern[1:]
                path = os.path.join(path, slug + suffix)
            else:
                slug = utils.slugify(os.path.splitext(os.path.basename(path))[0], lang=self.site.default_lang)

        if isinstance(author, utils.bytes_str):
                try:
                    author = author.decode(sys.stdin.encoding)
                except (AttributeError, TypeError):  # for tests
                    author = author.decode('utf-8')

        # Calculate the date to use for the content
        schedule = options['schedule'] or self.site.config['SCHEDULE_ALL']
        rule = self.site.config['SCHEDULE_RULE']
        self.site.scan_posts()
        timeline = self.site.timeline
        last_date = None if not timeline else timeline[0].date
        date, dateobj = get_date(schedule, rule, last_date, self.site.tzinfo, self.site.config['FORCE_ISO8601'])
        data = {
            'title': title,
            'slug': slug,
            'date': date,
            'tags': tags,
            'link': '',
            'description': '',
            'type': 'text',
        }

        if not path:
            pattern = os.path.basename(entry[0])
            suffix = pattern[1:]
            output_path = os.path.dirname(entry[0])
            if date_path_auto or date_path_opt:
                output_path += os.sep + dateobj.strftime(date_path_format)

            txt_path = os.path.join(output_path, slug + suffix)
            meta_path = os.path.join(output_path, slug + ".meta")
        else:
            if date_path_opt:
                LOGGER.warn("A path has been specified, ignoring -d")
            txt_path = os.path.join(self.site.original_cwd, path)
            meta_path = os.path.splitext(txt_path)[0] + ".meta"

        if (not onefile and os.path.isfile(meta_path)) or \
                os.path.isfile(txt_path):

            # Emit an event when a post exists
            event = dict(path=txt_path)
            if not onefile:  # write metadata file
                event['meta_path'] = meta_path
            signal('existing_' + content_type).send(self, **event)

            LOGGER.error("The title already exists!")
            LOGGER.info("Existing {0}'s text is at: {1}".format(content_type, txt_path))
            if not onefile:
                LOGGER.info("Existing {0}'s metadata is at: {1}".format(content_type, meta_path))
            return 8

        d_name = os.path.dirname(txt_path)
        utils.makedirs(d_name)
        metadata = {}
        if author:
            metadata['author'] = author
        metadata.update(self.site.config['ADDITIONAL_METADATA'])
        data.update(metadata)

        # ipynb plugin needs the ipython kernel info. We get the kernel name
        # from the content_subformat and pass it to the compiler in the metadata
        if content_format == "ipynb" and content_subformat is not None:
            metadata["ipython_kernel"] = content_subformat

        # Override onefile if not really supported.
        if not compiler_plugin.supports_onefile and onefile:
            onefile = False
            LOGGER.warn('This compiler does not support one-file posts.')

        if onefile and import_file:
            with io.open(import_file, 'r', encoding='utf-8') as fh:
                content = fh.read()
        elif not import_file:
            if is_page:
                content = self.site.MESSAGES[self.site.default_lang]["Write your page here."]
            else:
                content = self.site.MESSAGES[self.site.default_lang]["Write your post here."]

        if (not onefile) and import_file:
            # Two-file posts are copied  on import (Issue #2380)
            shutil.copy(import_file, txt_path)
        else:
            compiler_plugin.create_post(
                txt_path, content=content, onefile=onefile, title=title,
                slug=slug, date=date, tags=tags, is_page=is_page, **metadata)

        event = dict(path=txt_path)

        if not onefile:  # write metadata file
            with io.open(meta_path, "w+", encoding="utf8") as fd:
                fd.write(utils.write_metadata(data))
            LOGGER.info("Your {0}'s metadata is at: {1}".format(content_type, meta_path))
            event['meta_path'] = meta_path
        LOGGER.info("Your {0}'s text is at: {1}".format(content_type, txt_path))

        signal('new_' + content_type).send(self, **event)

        if options['edit']:
            editor = os.getenv('EDITOR', '').split()
            to_run = editor + [txt_path]
            if not onefile:
                to_run.append(meta_path)
            if editor:
                subprocess.call(to_run)
            else:
                LOGGER.error('$EDITOR not set, cannot edit the post.  Please do it manually.')

    def filter_post_pages(self, compiler, is_post):
        """Return the correct entry from post_pages.

        Information based on:
        * selected compilers
        * available compilers
        * post/page status
        """
        compilers = self.site.config['COMPILERS']
        post_pages = self.site.config['post_pages']
        compiler_objs = self.site.compilers

        # First throw away all the post_pages with the wrong is_post
        filtered = [entry for entry in post_pages if entry[3] == is_post]

        # These are the extensions supported by the required format
        extensions = compilers.get(compiler)
        if extensions is None:
            if compiler in compiler_objs:
                LOGGER.error("There is a {0} compiler available, but it's not set in your COMPILERS option.".format(compiler))
                LOGGER.info("Read more: {0}".format(COMPILERS_DOC_LINK))
            else:
                LOGGER.error('Unknown format {0}'.format(compiler))
                self.print_compilers()
            return False

        # Throw away the post_pages with the wrong extensions
        filtered = [entry for entry in filtered if any([ext in entry[0] for ext in
                                                        extensions])]

        if not filtered:
            type_name = "post" if is_post else "page"
            LOGGER.error("Can't find a way, using your configuration, to create "
                         "a {0} in format {1}. You may want to tweak "
                         "COMPILERS or {2}S in conf.py".format(
                             type_name, compiler, type_name.upper()))
            LOGGER.info("Read more: {0}".format(COMPILERS_DOC_LINK))

            return False
        return filtered[0]

    def print_compilers(self):
        """List all available compilers in a human-friendly format."""
        # We use compilers_raw, because the normal dict can contain
        # garbage coming from the translation candidate implementation.
        # Entries are in format: (name, extensions, used_in_post_pages)

        compilers_raw = self.site.config['_COMPILERS_RAW']

        used_compilers = []
        unused_compilers = []
        disabled_compilers = []

        for name, plugin in self.site.compilers.items():
            if name in compilers_raw:
                used_compilers.append([
                    name,
                    plugin.friendly_name or name,
                    compilers_raw[name],
                    True
                ])
            else:
                disabled_compilers.append([
                    name,
                    plugin.friendly_name or name,
                    (),
                    False
                ])

        for name, (_, _, pi) in self.site.disabled_compilers.items():
            if pi.details.has_option('Nikola', 'Friendlyname'):
                f_name = pi.details.get('Nikola', 'Friendlyname')
            else:
                f_name = name
            if name in compilers_raw:
                unused_compilers.append([
                    name,
                    f_name,
                    compilers_raw[name],
                    False
                ])
            else:
                disabled_compilers.append([
                    name,
                    f_name,
                    (),
                    False
                ])

        used_compilers.sort(key=operator.itemgetter(0))
        unused_compilers.sort(key=operator.itemgetter(0))
        disabled_compilers.sort(key=operator.itemgetter(0))

        # We also group the compilers by status for readability.
        parsed_list = used_compilers + unused_compilers + disabled_compilers

        print("Available input formats:\n")

        name_width = max([len(i[0]) for i in parsed_list] + [4])  # 4 == len('NAME')
        fname_width = max([len(i[1]) for i in parsed_list] + [11])  # 11 == len('DESCRIPTION')

        print((' {0:<' + str(name_width) + '}  {1:<' + str(fname_width) + '}  EXTENSIONS\n').format('NAME', 'DESCRIPTION'))

        for name, fname, extensions, used in parsed_list:
            flag = ' ' if used else '!'
            flag = flag if extensions else '~'

            extensions = ', '.join(extensions) if extensions else '(disabled: not in COMPILERS)'

            print(('{flag}{name:<' + str(name_width) + '}  {fname:<' + str(fname_width) + '}  {extensions}').format(flag=flag, name=name, fname=fname, extensions=extensions))

        print("""
    More compilers are available in the Plugins Index.

    Compilers marked with ! and ~ require additional configuration:
        ! not in the POSTS/PAGES tuples and any post scanners (unused)
        ~ not in the COMPILERS dict (disabled)
    Read more: {0}""".format(COMPILERS_DOC_LINK))
