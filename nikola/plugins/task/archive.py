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

"""Render the post archives."""

from __future__ import division
import math
import copy
import os
try:
    from urlparse import urljoin
except ImportError:
    from urllib.parse import urljoin  # NOQA
# for tearDown with _reload we cannot use 'import from' to access LocaleBorg
import nikola.utils
import datetime
from nikola.plugin_categories import Task
from nikola.utils import config_changed, adjust_name_for_index_path, adjust_name_for_index_link


class Archive(Task):
    """Render the post archives."""

    name = "render_archive"

    def set_site(self, site):
        """Set Nikola site."""
        site.register_path_handler('archive', self.archive_path)
        site.register_path_handler('archive_atom', self.archive_atom_path)
        site.register_path_handler('archive_rss', self.archive_rss_path)
        return super(Archive, self).set_site(site)

    def _prepare_task(self, kw, name, lang, posts, items, template_name,
                      title, deps_translatable=None,
                      archivefeed=[None, None, None, None]):
        """Prepare an archive task."""
        # name: used to build permalink and destination
        # posts, items: posts or items; only one of them should be used,
        #               the other should be None
        # template_name: name of the template to use
        # title: the (translated) title for the generated page
        # deps_translatable: dependencies (None if not added)
        assert posts is not None or items is not None
        task_cfg = [copy.copy(kw)]
        context = {}
        context["lang"] = lang
        context["title"] = title
        context["permalink"] = self.site.link("archive", name, lang)
        context["pagekind"] = ["list", "archive_page"]
        if posts is not None:
            context["posts"] = posts
            # Depend on all post metadata because it can be used in templates (Issue #1931)
            task_cfg.append([repr(p) for p in posts])
        else:
            # Depend on the content of items, to rebuild if links change (Issue #1931)
            context["items"] = items
            task_cfg.append(items)
        output_name = os.path.join(kw['output_folder'], self.site.path("archive", name, lang))
        task = self.site.generic_post_list_renderer(
            lang,
            [],
            output_name,
            template_name,
            kw['filters'],
            context,
        )

        task_cfg = {i: x for i, x in enumerate(task_cfg)}
        if deps_translatable is not None:
            task_cfg[3] = deps_translatable
        task['uptodate'] = task['uptodate'] + [config_changed(task_cfg, 'nikola.plugins.task.archive')]
        task['basename'] = self.name
        yield task

        if posts and (kw['generate_atom'] or kw['generate_rss']):
            kw['blog_description'] = self.site.config['BLOG_DESCRIPTION']
            kw['base_url'] = self.site.config['BASE_URL']
            page_link, _ = self._page_link_path(lang, name)
            ipages_i = nikola.utils.get_displayed_page_number(0, 1, self.site)
            description = kw['blog_description'](lang)
            targets = []

            atom_path = None
            atom_output_name = None
            if kw['generate_atom']:
                atom_currentlink = self.site.link("atom", None, lang)
                atom_path = page_link(0, ipages_i, 1, False, extension=".atom")
                atom_output_name = os.path.join(kw['output_folder'],
                                                atom_path.lstrip('/'))
                targets.append(atom_output_name)

            rss_path = None
            rss_output_name = None
            if kw['generate_rss']:
                rss_currentlink = self.site.link("rss", None, lang)
                rss_path = page_link(0, ipages_i, 1, False, extension=".xml")
                rss_output_name = os.path.join(kw['output_folder'],
                                               rss_path.lstrip('/'))
                targets.append(rss_output_name)

            feed_task = {
                'basename': self.name,
                'name': lang + ':' + ':'.join(targets),
                'actions': [(self.site.feedutil.gen_feed_generator,
                             (lang, posts, urljoin(
                                 kw['base_url'],
                                 context["permalink"].lstrip('/')),
                              title, description,
                              atom_output_name, atom_path,
                              rss_output_name, rss_path,
                              archivefeed[1], archivefeed[0],
                              None, None,
                              archivefeed[2], archivefeed[3],
                              None, None,
                              atom_currentlink, rss_currentlink))],
                'targets': targets,
                'file_dep': [output_name],
                'clean': True,
                'uptodate': task['uptodate']
            }
            yield feed_task

    def _generate_posts_task(self, kw, name, lang, posts, title, deps_translatable,
                             archivefeed=[None, None, None, None]):
        """Generate a task for an archive with posts."""
        if kw['archives_are_indexes']:
            page_link, page_path = self._page_link_path(lang, name)
            uptodate = []
            if deps_translatable is not None:
                uptodate += [config_changed(deps_translatable, 'nikola.plugins.task.archive')]
            context = {}
            context['archive_name'] = name
            context['archivefeed'] = archivefeed
            context['pagekind'] = ['index', 'archive_page']
            yield self.site.generic_index_renderer(
                lang,
                posts,
                title,
                "archiveindex.tmpl",
                context,
                kw,
                str(self.name),
                page_link,
                page_path,
                uptodate)
        else:
            yield self._prepare_task(kw, name, lang, posts, None,
                                     "list_post.tmpl", title, deps_translatable,
                                     archivefeed)

    def _feed_fl_links(self, kw, posts, page_link):
        """Get first/last links every year for feeds."""
        atom_firstlink = None
        atom_lastlink = None
        rss_firstlink = None
        rss_lastlink = None

        if kw['archives_are_indexes']:
            num_pages = math.ceil(len(posts) / kw["index_display_post_count"])
        else:
            num_pages = 1
        if kw['indexes_static']:
            if num_pages > 1:
                first = 1
            else:
                first = 0
        else:
            first = num_pages - 1
        last = 0
        firstpages_i = nikola.utils.get_displayed_page_number(
            first, num_pages, self.site)
        lastpages_i = nikola.utils.get_displayed_page_number(
            last, num_pages, self.site)

        if kw['generate_atom']:
            atom_firstlink = page_link(first, firstpages_i, num_pages, False,
                                       extension=".atom")
            atom_lastlink = page_link(last, lastpages_i, num_pages, False,
                                      extension=".atom")
        if kw['generate_rss']:
            rss_firstlink = page_link(first, firstpages_i, num_pages, False,
                                      extension=".xml")
            rss_lastlink = page_link(last, lastpages_i, num_pages, False,
                                     extension=".xml")

        return [atom_firstlink, atom_lastlink, rss_firstlink, rss_lastlink]

    def _page_link_path(self, lang, name):
        def _get_feed(extension):
            if extension == ".atom":
                return "_atom"
            elif extension == ".xml":
                return "_rss"
            else:
                return ""

        def page_link(i, displayed_i, num_pages, force_addition, extension=None):
            feed = _get_feed(extension)
            return adjust_name_for_index_link(
                self.site.link("archive" + feed, name, lang),
                i, displayed_i, lang, self.site, force_addition, extension)

        def page_path(i, displayed_i, num_pages, force_addition, extension=None):
            feed = _get_feed(extension)
            return adjust_name_for_index_path(
                self.site.path("archive" + feed, name, lang),
                i, displayed_i, lang, self.site, force_addition, extension)
        return page_link, page_path

    def _generate_tasks(self, kw, lang, idxs, datadict):
        """Generate tasks for an archive with posts."""
        if kw['generate_atom'] or kw['generate_rss']:
            for name in idxs:
                posts = datadict[name][0]
                page_link, _ = self._page_link_path(lang, name)
                fl_links =  self._feed_fl_links(kw, posts, page_link)
                datadict[name][3:] = fl_links

            oldest = len(idxs) - 1
            for i, name in enumerate(idxs):
                atom_prevlink = None
                atom_nextlink = None
                rss_prevlink = None
                rss_nextlink = None
                if i > 0:
                    atom_nextlink = datadict[idxs[i-1]][3] # atom_firstlink
                    rss_nextlink = datadict[idxs[i-1]][5] # rss_firstlink
                if i < oldest:
                    atom_prevlink = datadict[idxs[i+1]][4] # atom_lastlink
                    rss_prevlink = datadict[idxs[i+1]][6] # rss_lastlink

                yield self._generate_posts_task(kw, name, lang,
                                                datadict[name][0],
                                                datadict[name][1],
                                                datadict[name][2],
                                                [atom_prevlink, atom_nextlink,
                                                 rss_prevlink, rss_nextlink])
        else:
            for name in idxs:
                yield self._generate_posts_task(kw, name, lang,
                                                datadict[name][0],
                                                datadict[name][1],
                                                datadict[name][2])

    def gen_tasks(self):
        """Generate archive tasks."""
        kw = {
            "messages": self.site.MESSAGES,
            "translations": self.site.config['TRANSLATIONS'],
            "output_folder": self.site.config['OUTPUT_FOLDER'],
            "filters": self.site.config['FILTERS'],
            "archives_are_indexes": self.site.config['ARCHIVES_ARE_INDEXES'],
            "create_monthly_archive": self.site.config['CREATE_MONTHLY_ARCHIVE'],
            "create_single_archive": self.site.config['CREATE_SINGLE_ARCHIVE'],
            "show_untranslated_posts": self.site.config['SHOW_UNTRANSLATED_POSTS'],
            "create_full_archives": self.site.config['CREATE_FULL_ARCHIVES'],
            "create_daily_archive": self.site.config['CREATE_DAILY_ARCHIVE'],
            "pretty_urls": self.site.config['PRETTY_URLS'],
            "strip_indexes": self.site.config['STRIP_INDEXES'],
            "index_file": self.site.config['INDEX_FILE'],
            "index_display_post_count": self.site.config['INDEX_DISPLAY_POST_COUNT'],
            "indexes_static": self.site.config['INDEXES_STATIC'],
            "generate_atom": self.site.config["GENERATE_ATOM"],
            "generate_rss": self.site.config["GENERATE_RSS"]
        }
        self.site.scan_posts()
        yield self.group_task()

        if (kw['create_monthly_archive'] and kw['create_single_archive']) and not kw['create_full_archives']:
            raise Exception('Cannot create monthly and single archives at the same time.')

        for lang in kw["translations"]:
            deps_translatable = {}
            for k in self.site._GLOBAL_CONTEXT_TRANSLATABLE:
                deps_translatable[k] = self.site.GLOBAL_CONTEXT[k](lang)

            if kw['create_single_archive'] or kw['create_full_archives']:
                posts = self.site.posts
                # Filter untranslated posts (Issue #1360)
                if not kw["show_untranslated_posts"]:
                    posts = [p for p in posts if lang in p.translated_to]
                    if len(posts) == 0:
                        continue
                posts = sorted(posts, key=lambda a: a.date, reverse=True)
                title = kw["messages"][lang]["Archive"]
                yield self._generate_posts_task(kw, None, lang, posts, title,
                                                deps_translatable)
                if kw['create_single_archive']:
                    continue

            # if we are not creating one single archive, start with all years
            archdata = self.site.posts_per_year.copy()
            years = list(archdata.keys())

            for year in years[:]:
                posts = archdata[year]
                # Filter untranslated posts (Issue #1360)
                if not kw["show_untranslated_posts"]:
                    posts = [p for p in posts if lang in p.translated_to]
                    if len(posts) == 0:
                        years.remove(year)
                        continue
                posts = sorted(posts, key=lambda a: a.date, reverse=True)
                # Add archive per year or total archive
                title = kw["messages"][lang]["Posts for year %s"] % year
                archdata[year] = [posts, title, deps_translatable, None, None, None, None]
            years.sort(reverse=True)

            if not kw['create_full_archives']:
                items = [(y, self.site.link("archive", y, lang), len(self.site.posts_per_year[y])) for y in years]
                yield self._prepare_task(kw, None, lang, None, items,
                                         "list.tmpl",
                                         kw["messages"][lang]["Archive"])

            if not kw["create_monthly_archive"] or kw["create_full_archives"]:
                yield self._generate_tasks(kw, lang, years, archdata)

            if (not kw["create_monthly_archive"]
                and not kw["create_full_archives"]
                and not kw["create_daily_archive"]):
                continue  # Just to avoid nesting the other loop in this if

            ymarchdata = self.site.posts_per_month.copy()
            yearmonths = list(ymarchdata.keys())
            for yearmonth in yearmonths[:]:
                posts = self.site.posts_per_month[yearmonth]
                # Filter untranslated posts (via Issue #1360)
                if not kw["show_untranslated_posts"]:
                    posts = [p for p in posts if lang in p.translated_to]
                    if len(posts) == 0:
                        yearmonths.remove(yearmonth)
                        continue
                posts = sorted(posts, key=lambda a: a.date, reverse=True)
                # Add archive per month
                year, month = yearmonth.split('/')
                title = kw["messages"][lang]["Posts for {month} {year}"].format(
                    year=year, month=nikola.utils.LocaleBorg().get_month_name(int(month), lang))
                ymarchdata[yearmonth] = [posts, title, None, None, None, None, None]
            yearmonths.sort(reverse=True)

            if kw["create_monthly_archive"] and not kw["create_full_archives"]:
                for year in years:
                    arch = archdata[year]
                    months = []
                    for m in yearmonths:
                        if m.startswith(year):
                            months.append([m.split('/')[1],
                                           self.site.link("archive", m, lang),
                                           len(ymarchdata[m][0])])
                    items = []
                    for month, link, count in months:
                        items.append(
                            [nikola.utils.LocaleBorg().get_month_name(int(month), lang),
                             link, count])
                    yield self._prepare_task(kw, year, lang, None, items,
                                             "list.tmpl",
                                             arch[1],
                                             arch[2])

            if kw["create_monthly_archive"] or kw["create_full_archives"]:
                yield self._generate_tasks(kw, lang, yearmonths, ymarchdata)

            if kw["create_daily_archive"] or kw["create_full_archives"]:
                # Add archive per day
                daysdata = {}
                days = []
                for yearmonth in yearmonths:
                    posts = ymarchdata[yearmonth][0]
                    year, month = yearmonth.split('/')

                    for p in posts:
                        yearmonthday = yearmonth + '/{0:02d}'.format(p.date.day)
                        d = daysdata.get(yearmonthday)
                        if not d:
                            title = kw["messages"][lang]["Posts for {month} {day}, {year}"].format(
                                year=year, month=nikola.utils.LocaleBorg().get_month_name(int(month), lang), day=p.date.day)
                            d = [list(), title, None, None, None, None, None]
                            daysdata[yearmonthday] = d
                            days.append(yearmonthday)
                        d[0].append(p)

                yield self._generate_tasks(kw, lang, days, daysdata)

    def archive_path(self, name, lang):
        """Link to archive path, name is the year.

        Example:

        link://archive/2013 => /archives/2013/index.html
        """
        archive_file = self.site.config['ARCHIVE_FILENAME']
        index_file = self.site.config['INDEX_FILE']
        if name:
            return [_f for _f in [self.site.config['TRANSLATIONS'][lang],
                                  self.site.config['ARCHIVE_PATH'], name,
                                  index_file] if _f]
        else:
            return [_f for _f in [self.site.config['TRANSLATIONS'][lang],
                                  self.site.config['ARCHIVE_PATH'],
                                  archive_file] if _f]

    def _archive_feed_path(self, name, lang, extension):
        """Link to feed archive path, name is the year."""
        archive_file = os.path.splitext(self.site.config['ARCHIVE_FILENAME'])[0] + extension
        index_file = os.path.splitext(self.site.config['INDEX_FILE'])[0] + extension
        if name:
            return [_f for _f in [self.site.config['TRANSLATIONS'][lang],
                                  self.site.config['ARCHIVE_PATH'], name,
                                  index_file] if _f]
        else:
            return [_f for _f in [self.site.config['TRANSLATIONS'][lang],
                                  self.site.config['ARCHIVE_PATH'],
                                  archive_file] if _f]

    def archive_atom_path(self, name, lang):
        """Link to atom archive path, name is the year.

        Example:

        link://archive_atom/2013 => /archives/2013/index.atom
        """
        return self._archive_feed_path(name, lang, ".atom")

    def archive_rss_path(self, name, lang):
        """Link to RSS archive path, name is the year.

        Example:

        link://archive_atom/2013 => /archives/2013/index.xml
        """
        return self._archive_feed_path(name, lang, ".xml")
