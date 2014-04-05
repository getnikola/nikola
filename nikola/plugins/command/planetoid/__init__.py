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

from __future__ import print_function, unicode_literals
import codecs
import datetime
import hashlib
from optparse import OptionParser
import os
import sys

from doit.tools import timeout
from nikola.plugin_categories import Command, Task
from nikola.utils import config_changed, req_missing, get_logger, STDERR_HANDLER

LOGGER = get_logger('planetoid', STDERR_HANDLER)

try:
    import feedparser
except ImportError:
    feedparser = None  # NOQA

try:
    import peewee
except ImportError:
    peewee = None


if peewee is not None:
    class Feed(peewee.Model):
        name = peewee.CharField()
        url = peewee.CharField(max_length=200)
        last_status = peewee.CharField(null=True)
        etag = peewee.CharField(max_length=200)
        last_modified = peewee.DateTimeField()

    class Entry(peewee.Model):
        date = peewee.DateTimeField()
        feed = peewee.ForeignKeyField(Feed)
        content = peewee.TextField()
        link = peewee.CharField(max_length=200)
        title = peewee.CharField(max_length=200)
        guid = peewee.CharField(max_length=200)


class Planetoid(Command, Task):
    """Maintain a planet-like thing."""
    name = "planetoid"

    def init_db(self):
        # setup database
        Feed.create_table(fail_silently=True)
        Entry.create_table(fail_silently=True)

    def gen_tasks(self):
        if peewee is None or sys.version_info[0] == 3:
            if sys.version_info[0] == 3:
                message = 'Peewee, a requirement of the "planetoid" command, is currently incompatible with Python 3.'
            else:
                req_missing('peewee', 'use the "planetoid" command')
                message = ''
            yield {
                'basename': self.name,
                'name': '',
                'verbosity': 2,
                'actions': ['echo "%s"' % message]
            }
        else:
            self.init_db()
            self.load_feeds()
            for task in self.task_update_feeds():
                yield task
            for task in self.task_generate_posts():
                yield task
            yield {
                'basename': self.name,
                'name': '',
                'actions': [],
                'file_dep': ['feeds'],
                'task_dep': [
                    self.name + "_fetch_feed",
                    self.name + "_generate_posts",
                ]
            }

    def run(self, *args):
        parser = OptionParser(usage="nikola %s [options]" % self.name)
        (options, args) = parser.parse_args(list(args))

    def load_feeds(self):
        "Read the feeds file, add it to the database."
        feeds = []
        feed = name = None
        for line in codecs.open('feeds', 'r', 'utf-8'):
            line = line.strip()
            if line.startswith("#"):
                continue
            elif line.startswith('http'):
                feed = line
            elif line:
                name = line
            if feed and name:
                feeds.append([feed, name])
                feed = name = None

        def add_feed(name, url):
            f = Feed.create(
                name=name,
                url=url,
                etag='foo',
                last_modified=datetime.datetime(1970, 1, 1),
            )
            f.save()

        def update_feed_url(feed, url):
            feed.url = url
            feed.save()

        for feed, name in feeds:
            f = Feed.select().where(Feed.name == name)
            if not list(f):
                add_feed(name, feed)
            elif list(f)[0].url != feed:
                update_feed_url(list(f)[0], feed)

    def task_update_feeds(self):
        """Download feed contents, add entries to the database."""
        def update_feed(feed):
            modified = feed.last_modified.timetuple()
            etag = feed.etag
            try:
                parsed = feedparser.parse(
                    feed.url,
                    etag=etag,
                    modified=modified
                )
                feed.last_status = str(parsed.status)
            except:  # Probably a timeout
                # TODO: log failure
                return
            if parsed.feed.get('title'):
                LOGGER.info(parsed.feed.title)
            else:
                LOGGER.info(feed.url)
            feed.etag = parsed.get('etag', 'foo')
            modified = tuple(parsed.get('date_parsed', (1970, 1, 1)))[:6]
            LOGGER.info("==========>", modified)
            modified = datetime.datetime(*modified)
            feed.last_modified = modified
            feed.save()
            # No point in adding items from missinfg feeds
            if parsed.status > 400:
                # TODO log failure
                return
            for entry_data in parsed.entries:
                LOGGER.info("=========================================")
                date = entry_data.get('published_parsed', None)
                if date is None:
                    date = entry_data.get('updated_parsed', None)
                if date is None:
                    LOGGER.error("Can't parse date from:\n", entry_data)
                    return False
                LOGGER.info("DATE:===>", date)
                date = datetime.datetime(*(date[:6]))
                title = "%s: %s" % (feed.name, entry_data.get('title', 'Sin título'))
                content = entry_data.get('content', None)
                if content:
                    content = content[0].value
                if not content:
                    content = entry_data.get('description', None)
                if not content:
                    content = entry_data.get('summary', 'Sin contenido')
                guid = str(entry_data.get('guid', entry_data.link))
                link = entry_data.link
                LOGGER.info(repr([date, title]))
                e = list(Entry.select().where(Entry.guid == guid))
                LOGGER.info(
                    repr(dict(
                        date=date,
                        title=title,
                        content=content,
                        guid=guid,
                        feed=feed,
                        link=link,
                    ))
                )
                if not e:
                    entry = Entry.create(
                        date=date,
                        title=title,
                        content=content,
                        guid=guid,
                        feed=feed,
                        link=link,
                    )
                else:
                    entry = e[0]
                    entry.date = date
                    entry.title = title
                    entry.content = content
                    entry.link = link
                entry.save()
        flag = False
        for feed in Feed.select():
            flag = True
            task = {
                'basename': self.name + "_fetch_feed",
                'name': str(feed.url),
                'actions': [(update_feed, (feed, ))],
                'uptodate': [timeout(datetime.timedelta(minutes=self.site.config.get('PLANETOID_REFRESH', 60)))],
            }
            yield task
        if not flag:
            yield {
                'basename': self.name + "_fetch_feed",
                'name': '',
                'actions': [],
            }

    def task_generate_posts(self):
        """Generate post files for the blog entries."""
        def gen_id(entry):
            h = hashlib.md5()
            h.update(entry.feed.name.encode('utf8'))
            h.update(entry.guid)
            return h.hexdigest()

        def generate_post(entry):
            unique_id = gen_id(entry)
            meta_path = os.path.join('posts', unique_id + '.meta')
            post_path = os.path.join('posts', unique_id + '.txt')
            with codecs.open(meta_path, 'wb+', 'utf8') as fd:
                fd.write('%s\n' % entry.title.replace('\n', ' '))
                fd.write('%s\n' % unique_id)
                fd.write('%s\n' % entry.date.strftime('%Y/%m/%d %H:%M'))
                fd.write('\n')
                fd.write('%s\n' % entry.link)
            with codecs.open(post_path, 'wb+', 'utf8') as fd:
                fd.write('.. raw:: html\n\n')
                content = entry.content
                if not content:
                    content = 'Sin contenido'
                for line in content.splitlines():
                    fd.write('    %s\n' % line)

        if not os.path.isdir('posts'):
            os.mkdir('posts')
        flag = False
        for entry in Entry.select().order_by(Entry.date.desc()):
            flag = True
            entry_id = gen_id(entry)
            yield {
                'basename': self.name + "_generate_posts",
                'targets': [os.path.join('posts', entry_id + '.meta'), os.path.join('posts', entry_id + '.txt')],
                'name': entry_id,
                'actions': [(generate_post, (entry,))],
                'uptodate': [config_changed({1: entry})],
                'task_dep': [self.name + "_fetch_feed"],
            }
        if not flag:
            yield {
                'basename': self.name + "_generate_posts",
                'name': '',
                'actions': [],
            }
