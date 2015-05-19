# -*- coding: utf-8 -*-

# Copyright © 2012-2015 Roberto Alsina and others.

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

from __future__ import unicode_literals, print_function
import io
import datetime
import os
import sys
import subprocess

from blinker import signal
import dateutil.tz

from nikola.plugin_categories import Command
from nikola import utils

POSTLOGGER = utils.get_logger('new_post', utils.STDERR_HANDLER)
PAGELOGGER = utils.get_logger('new_page', utils.STDERR_HANDLER)
LOGGER = POSTLOGGER


def filter_post_pages(compiler, is_post, compilers, post_pages, compiler_names):
    """Given a compiler ("markdown", "rest"), and whether it's meant for
    a post or a page, and compilers, return the correct entry from
    post_pages."""

    # First throw away all the post_pages with the wrong is_post
    filtered = [entry for entry in post_pages if entry[3] == is_post]

    # These are the extensions supported by the required format
    extensions = compilers.get(compiler)
    if extensions is None:
        if compiler in compiler_names:
            LOGGER.error("There is a {0} compiler available, but it's not set in your COMPILERS option.".format(compiler))
        else:
            LOGGER.error('Unknown format {0}'.format(compiler))
        sys.exit(1)

    # Throw away the post_pages with the wrong extensions
    filtered = [entry for entry in filtered if any([ext in entry[0] for ext in
                                                    extensions])]

    if not filtered:
        type_name = "post" if is_post else "page"
        LOGGER.error("Can't find a way, using your configuration, to create "
                     "a {0} in format {1}. You may want to tweak "
                     "COMPILERS or {2}S in conf.py".format(
                         type_name, compiler, type_name.upper()))
        sys.exit(1)
    return filtered[0]


def get_default_compiler(is_post, compilers, post_pages):
    """Given compilers and post_pages, return a reasonable
    default compiler for this kind of post/page.
    """

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
    """Returns a date stamp, given a recurrence rule.

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

    return date.strftime('%Y-%m-%d %H:%M:%S') + tz_str


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
            'help': 'Markup format for the post, one of rest, markdown, wiki, '
                    'bbcode, html, textile, txt2tags',
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

        if is_page:
            LOGGER = PAGELOGGER
        else:
            LOGGER = POSTLOGGER

        if twofile:
            onefile = False
        if not onefile and not twofile:
            onefile = self.site.config.get('ONE_FILE_POSTS', True)

        content_format = options['content_format']

        if not content_format:  # Issue #400
            content_format = get_default_compiler(
                is_post,
                self.site.config['COMPILERS'],
                self.site.config['post_pages'])

        if content_format not in compiler_names:
            LOGGER.error("Unknown {0} format {1}, maybe you need to install a plugin?".format(content_type, content_format))
            return
        compiler_plugin = self.site.plugin_manager.getPluginByName(
            content_format, "PageCompiler").plugin_object

        # Guess where we should put this
        entry = filter_post_pages(content_format, is_post,
                                  self.site.config['COMPILERS'],
                                  self.site.config['post_pages'],
                                  compiler_names)

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
            slug = utils.slugify(title)
        else:
            if isinstance(path, utils.bytes_str):
                try:
                    path = path.decode(sys.stdin.encoding)
                except (AttributeError, TypeError):  # for tests
                    path = path.decode('utf-8')
            slug = utils.slugify(os.path.splitext(os.path.basename(path))[0])

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
        date = get_date(schedule, rule, last_date, self.site.tzinfo, self.site.config['FORCE_ISO8601'])
        data = {
            'title': title,
            'slug': slug,
            'date': date,
            'tags': tags,
            'link': '',
            'description': '',
            'type': 'text',
        }
        output_path = os.path.dirname(entry[0])
        meta_path = os.path.join(output_path, slug + ".meta")
        pattern = os.path.basename(entry[0])
        suffix = pattern[1:]
        if not path:
            txt_path = os.path.join(output_path, slug + suffix)
        else:
            txt_path = os.path.join(self.site.original_cwd, path)

        if (not onefile and os.path.isfile(meta_path)) or \
                os.path.isfile(txt_path):

            # Emit an event when a post exists
            event = dict(path=txt_path)
            if not onefile:  # write metadata file
                event['meta_path'] = meta_path
            signal('existing_' + content_type).send(self, **event)

            LOGGER.error("The title already exists!")
            exit(8)

        d_name = os.path.dirname(txt_path)
        utils.makedirs(d_name)
        metadata = {}
        if author:
            metadata['author'] = author
        metadata.update(self.site.config['ADDITIONAL_METADATA'])
        data.update(metadata)

        # Override onefile if not really supported.
        if not compiler_plugin.supports_onefile and onefile:
            onefile = False
            LOGGER.warn('This compiler does not support one-file posts.')

        if import_file:
            with io.open(import_file, 'r', encoding='utf-8') as fh:
                content = fh.read()
        else:
            # ipynb's create_post depends on this exact string, take care
            # if you're changing it
            content = "Write your {0} here.".format('page' if is_page else 'post')
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
