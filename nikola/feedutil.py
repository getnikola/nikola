# -*- coding: utf-8 -*-

# Copyright © 2015 IGARASHI Masanao

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

"""Utility functions for feed"""

from __future__ import unicode_literals
import os
import sys
try:
    from urlparse import urljoin
except ImportError:
    from urllib.parse import urljoin  # NOQA
import io
import uuid
import mimetypes
from datetime import datetime
import dateutil.tz
import lxml.html
from lxml.html import fragment_fromstring
import lxml.etree
import html5lib
from feedgen.feed import FeedGenerator
from .image_processing import ImageProcessor

from . import utils


xml_dec_line = '<?xml version="1.0" encoding="utf-8"?>\n'
xsl_line = '<?xml-stylesheet type="text/xsl" href="{0}" media="all"?>\n'

class FeedUtil(object):

    """The utility class for feed."""

    def __init__(self, site):
        """Setup."""
        self.site = site

    def atom_renderer(self, fg, output_path, atom_path, xsl_stylesheet_href):
        """Render a Atom file."""
        dst_dir = os.path.dirname(output_path)
        utils.makedirs(dst_dir)
        with io.open(output_path, 'w+', encoding='utf-8') as atom_file:
            atom_file.write(xml_dec_line)
            atom_file.write(xsl_line.format(xsl_stylesheet_href))
            atom_file.write(fg.atom_str(pretty=True))

    def rss_renderer(self, fg, output_path, rss_path, xsl_stylesheet_href):
        """Render a RSS file."""
        dst_dir = os.path.dirname(output_path)
        utils.makedirs(dst_dir)
        with io.open(output_path, 'w+', encoding='utf-8') as rss_file:
            rss_file.write(xml_dec_line)
            rss_file.write(xsl_line.format(xsl_stylesheet_href))
            rss_file.write(fg.rss_str(pretty=True))

    def _tzdatetime(self, dt):
        """Get a datetime for feed."""
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=self.site.tzinfo)
        return dt.astimezone(dateutil.tz.tzutc())

    def _enclosure(self, post, lang):
        """Get an enclosure infomation from a post."""
        enclosure = post.meta('enclosure', lang)
        if enclosure:
            length = 0
            url = enclosure
            mime = mimetypes.guess_type(url)[0]
            return url, length, mime

    def get_feed_content(self, data, lang, post, enclosure_details,
                         preview_image=None, default_image=None):
        """Create a feed content."""
        try:
            doc = html5lib.html5parser.parse(data, treebuilder='lxml',
                                             namespaceHTMLElements=False)
            doc = fragment_fromstring(lxml.html.tostring(doc), create_parent=True)
            doc.rewrite_links(
                lambda dst: self.site.url_replacer(post.permalink(), dst, lang,
                                                   'absolute'))
            try:
                src = None
                if preview_image:
                    src = preview_image
                elif (enclosure_details and
                      enclosure_details[2].split('/')[0] == 'image'):
                    src = enclosure_details[0]
                else:
                    postdoc = html5lib.html5parser.parse(post.text(lang),
                                                         treebuilder='lxml',
                                                         namespaceHTMLElements=False)
                    found = postdoc.xpath('//img')
                    for img in found:
                        src = img.attrib.get('src')
                        if src:
                            break
                    if src is None and default_image:
                        src = default_image
                if src is not None and src not in data:
                    f = lxml.etree.Element('fiture')
                    a = lxml.etree.SubElement(f, 'a')
                    a.attrib['href'] = post.permalink(lang, absolute=True)
                    img = lxml.etree.SubElement(a, 'img')
                    img.attrib['src'] = src
                    img.attrib['alt'] = 'thumbnail'
                    doc.insert(0, f)

                data = (doc.text or '') + ''.join(
                    [lxml.html.tostring(child, encoding='unicode')
                     for child in doc.iterchildren()])
            # No body there, it happens sometimes
            except IndexError:
                data = ''
        except lxml.etree.ParserError as e:
            if str(e) == "Document is empty":
                data = ""
            else:  # let other errors raise
                raise(e)
        return data

    def gen_urn(self, path):
        """Create a URN string."""
        if sys.version_info[0] == 3:
            return 'urn:uuid:{0}'.format(uuid.uuid5(uuid.NAMESPACE_URL, path))
        else:
            return 'urn:uuid:{0}'.format(uuid.uuid5(uuid.NAMESPACE_URL,
                                                    path.encode('utf-8')))

    def gen_feed_generator(self, lang, timeline, altlink, title, subtitle,
                           atom_output_name, atom_path, rss_output_name,
                           rss_path, atom_nextlink=None, atom_prevlink=None,
                           atom_firstlink=None, atom_lastlink=None,
                           rss_nextlink=None, rss_prevlink=None,
                           rss_firstlink=None, rss_lastlink=None,
                           atom_currentlink=None, rss_currentlink=None):
        """Generate feed tasks."""
        config = self.site.config
        base_url = config["BASE_URL"]
        feed_links_append_query = config["FEED_LINKS_APPEND_QUERY"]
        blog_author = config["BLOG_AUTHOR"](lang)
        feed_plain = config["FEED_PLAIN"]
        feed_teasers = config["FEED_TEASERS"]
        feed_push = config["FEED_PUSH"]
        feed_previewimage = config["FEED_PREVIEWIMAGE"]
        feed_previewimage_default = config["FEED_PREVIEWIMAGE_DEFAULT"]

        fg = FeedGenerator()
        fg.load_extension('dc', atom=False,rss=True)
        if atom_currentlink or rss_currentlink:
            fg.load_extension('history', atom=True, rss=True)
        fg.updated(datetime.now(dateutil.tz.tzutc()))
        fg.title(title=title, type=None, cdata=False)
        fg.subtitle(subtitle=subtitle, type=None, cdata=False)
        fg.author({'name': blog_author})
        links = [{'href': altlink, 'rel': 'alternate'}]

        if atom_output_name:
            atom_feed_url = urljoin(base_url, atom_path.lstrip('/'))
            atom_append_query = None
            if feed_links_append_query:
                atom_append_query = feed_links_append_query.format(
                    feedRelUri=atom_path, feedFormat='atom')
            fg.id(self.gen_urn(atom_feed_url))
            links.append({'href': atom_feed_url, 'rel': 'self'})

        if feed_push:
            links.append({'href': feed_push, 'rel': 'hub'})

        if atom_output_name:
            if atom_currentlink:
                fg.history.history_archive()
                links.append({'href': urljoin(base_url,
                                              atom_currentlink.lstrip('/')),
                              'rel': 'current'})
                if atom_nextlink is not None:
                    links.append({'href': urljoin(base_url,
                                                  atom_nextlink.lstrip('/')),
                                  'rel': 'next-archive'})
                if atom_prevlink is not None:
                    links.append({'href': urljoin(base_url,
                                                  atom_prevlink.lstrip('/')),
                                  'rel': 'prev-archive'})
            else:
                if atom_nextlink is not None:
                    links.append({'href': urljoin(base_url,
                                                  atom_nextlink.lstrip('/')),
                                  'rel': 'next'})
                if atom_prevlink is not None:
                    links.append({'href': urljoin(base_url,
                                                  atom_prevlink.lstrip('/')),
                                  'rel': 'previous'})
                if atom_firstlink is not None:
                    links.append({'href': urljoin(base_url,
                                                  atom_firstlink.lstrip('/')),
                                  'rel': 'first'})
                if atom_lastlink is not None:
                    links.append({'href': urljoin(base_url,
                                                  atom_lastlink.lstrip('/')),
                                  'rel': 'last'})
        fg.link(links)

        if rss_output_name:
            rss_feed_url = urljoin(base_url, rss_path.lstrip('/'))
            rss_append_query = None
            if feed_links_append_query:
                rss_append_query = feed_links_append_query.format(
                    feedRelUri=rss_path, feedFormat='rss')

            fg.rss_atom_link_self(rss_feed_url)
            rss_links = []
            if rss_currentlink:
                fg.history.history_archive()
                rss_links.append({'href': urljoin(base_url,
                                                  rss_currentlink.lstrip('/')),
                                  'rel': 'current'})
                if rss_nextlink is not None:
                    rss_links.append({'href': urljoin(base_url,
                                                      rss_nextlink.lstrip('/')),
                                      'rel': 'next-archive'})
                if rss_prevlink is not None:
                    rss_links.append({'href': urljoin(base_url,
                                                      rss_prevlink.lstrip('/')),
                                      'rel': 'prev-archive'})
            else:
                if rss_nextlink is not None:
                    rss_links.append({'href': urljoin(base_url,
                                                      rss_nextlink.lstrip('/')),
                                      'rel': 'next'})
                if rss_prevlink is not None:
                    rss_links.append({'href': urljoin(base_url,
                                                      rss_prevlink.lstrip('/')),
                                      'rel': 'previous'})
                if rss_firstlink is not None:
                    rss_links.append({'href': urljoin(base_url,
                                                      rss_firstlink.lstrip('/')),
                                      'rel': 'first'})
                if rss_lastlink is not None:
                    rss_links.append({'href': urljoin(base_url,
                                                      rss_lastlink.lstrip('/')),
                                      'rel': 'last'})
            if len(rss_links):
                fg.rss_atom_link(rss_links)

        for post in timeline:
            entry_date = self._tzdatetime(post.date)
            entry_updated = self._tzdatetime(post.updated)

            entry_id = self.gen_urn(post.permalink(lang, absolute=True))

            fe = fg.add_entry()
            fe.id(entry_id)
            fe.title(title=post.title(lang), type='text', cdata=False)
            fe.updated(entry_updated)
            fe.published(entry_date)
            if post.author(lang):
                fe.author({'name': post.author(lang)})
            if post.description(lang):
                fe.summary(summary=post.description(lang), type=None,
                           cdata=False)
            categories = set([])
            if post.meta('category'):
                categories.add(post.meta('category'))
            tags = set(post._tags.get(lang, []))
            categories.update(tags)
            if len(categories):
                fe.category([{'term': x} for x in categories])

            # enclosure callback returns None if post has no enclosure, or a
            # 3-tuple of (url, length (0 is valid), mimetype)
            enclosure_details = self._enclosure(post=post, lang=lang)
            if enclosure_details is not None:
                feed_enclosure = config["FEED_ENCLOSURE"]
                if feed_enclosure == 'link':
                    fe.link([{
                        'href': enclosure_details[0],
                        'length': enclosure_details[1],
                        'type': enclosure_details[2],
                        'rel': 'enclosure'
                    }])
                elif feed_enclosure == 'media':
                    fg.load_extension('media', atom=True, rss=True)
                    fe.media.thumbnail([{
                        'url': enclosure_details[0],
                    }])
            if feed_previewimage:
                if 'previewimage' in post.meta[lang]:
                    preview_image = post.meta[lang]['previewimage']
                else:
                    preview_image = None
                default_image = feed_previewimage_default
            else:
                preview_image = None
                default_image = None

            if atom_output_name:
                fe.link([{'href': post.permalink(
                    lang, absolute=True, query=atom_append_query),
                          'rel': 'alternate'}])

                data = post.text(
                    lang, teaser_only=feed_teasers,
                    strip_html=feed_plain,
                    feed_read_more_link=True,
                    feed_links_append_query=atom_append_query)
                if data:
                    # Massage the post's HTML (unless plain)
                    if feed_plain:
                        fe.content(content=data, src=None, type='text',
                                   cdata=False)
                    else:
                        data = self.get_feed_content(data, lang, post,
                                                     enclosure_details,
                                                     preview_image,
                                                     default_image)
                        fe.content(content=data, src=None, type='html',
                                   cdata=True)

            if rss_output_name:
                fe.rss_link(post.permalink(
                    lang, absolute=True, query=rss_append_query))

                data = post.text(
                    lang, teaser_only=feed_teasers,
                    strip_html=feed_plain,
                    feed_read_more_link=True,
                    feed_links_append_query=rss_append_query)
                if data:
                    # Massage the post's HTML (unless plain)
                    if feed_plain:
                        fe.rss_content(content=data, cdata=False)
                    else:
                        data = self.get_feed_content(data, lang, post,
                                                     enclosure_details,
                                                     preview_image,
                                                     default_image)
                        fe.rss_content(content=data, cdata=True)

        if atom_output_name:
            self.atom_renderer(fg, atom_output_name, atom_path,
                               self.site.url_replacer(atom_path,
                                                      "/assets/xml/atom.xsl"))
        if rss_output_name:
            self.rss_renderer(fg, rss_output_name, rss_path,
                              self.site.url_replacer(rss_path,
                                                     "/assets/xml/rss.xsl"))

    def gallery_feed_generator(self, lang,
                               img_list, dest_img_list, img_titles,
                               image_processor,
                               altlink, title, subtitle,
                               atom_output_name, atom_path, rss_output_name,
                               rss_path, atom_nextlink=None, atom_prevlink=None,
                               atom_firstlink=None, atom_lastlink=None,
                               rss_nextlink=None, rss_prevlink=None,
                               rss_firstlink=None, rss_lastlink=None):
        """Generate feed tasks for gallery."""
        config = self.site.config
        base_url = config["BASE_URL"]
        feed_links_append_query = config["FEED_LINKS_APPEND_QUERY"]
        blog_author = config["BLOG_AUTHOR"](lang)
        feed_push = config["FEED_PUSH"]

        fg = FeedGenerator()
        fg.load_extension('dc', atom=False,rss=True)
        fg.updated(datetime.now(dateutil.tz.tzutc()))
        fg.title(title=title, type=None, cdata=False)
        fg.subtitle(subtitle=subtitle, type=None, cdata=False)
        fg.author({'name': blog_author})
        links = [{'href': altlink, 'rel': 'alternate'}]

        if atom_output_name:
            atom_feed_url = urljoin(base_url, atom_path.lstrip('/'))
            atom_append_query = None
            if feed_links_append_query:
                atom_append_query = feed_links_append_query.format(
                    feedRelUri=atom_path, feedFormat='atom')
            fg.id(self.gen_urn(atom_feed_url))
            links.append({'href': atom_feed_url, 'rel': 'self'})

        if feed_push:
            links.append({'href': feed_push, 'rel': 'hub'})

        if atom_output_name:
            if atom_nextlink is not None:
                links.append({'href': urljoin(base_url,
                                              atom_nextlink.lstrip('/')),
                              'rel': 'next'})
            if atom_prevlink is not None:
                links.append({'href': urljoin(base_url,
                                              atom_prevlink.lstrip('/')),
                              'rel': 'previous'})
            if atom_firstlink is not None:
                links.append({'href': urljoin(base_url,
                                              atom_firstlink.lstrip('/')),
                              'rel': 'first'})
            if atom_lastlink is not None:
                links.append({'href': urljoin(base_url,
                                              atom_lastlink.lstrip('/')),
                              'rel': 'last'})
        fg.link(links)

        if rss_output_name:
            rss_feed_url = urljoin(base_url, rss_path.lstrip('/'))
            rss_append_query = None
            if feed_links_append_query:
                rss_append_query = feed_links_append_query.format(
                    feedRelUri=rss_path, feedFormat='rss')

            fg.rss_atom_link_self(rss_feed_url)
            rss_links = []
            if rss_nextlink is not None:
                rss_links.append({'href': urljoin(base_url,
                                                  rss_nextlink.lstrip('/')),
                                  'rel': 'next'})
            if rss_prevlink is not None:
                rss_links.append({'href': urljoin(base_url,
                                                  rss_prevlink.lstrip('/')),
                                  'rel': 'previous'})
            if rss_firstlink is not None:
                rss_links.append({'href': urljoin(base_url,
                                                  rss_firstlink.lstrip('/')),
                                  'rel': 'first'})
            if rss_lastlink is not None:
                rss_links.append({'href': urljoin(base_url,
                                                  rss_lastlink.lstrip('/')),
                                  'rel': 'last'})
            if len(rss_links):
                fg.rss_atom_link(rss_links)

        for img, srcimg, imgtitle in zip(dest_img_list, img_list, img_titles):
            entry_date = self._tzdatetime(image_processor.image_date(srcimg))

            img_url = urljoin(self.site.config['BASE_URL'], img.lstrip('/'))

            entry_id = self.gen_urn(img_url)
            fe = fg.add_entry()
            fe.id(entry_id)
            fe.title(title=imgtitle, type='text', cdata=False)
            fe.updated(entry_date)
            fe.published(entry_date)

            img_size = os.stat(img).st_size

            feed_enclosure = config["FEED_ENCLOSURE"]
            if feed_enclosure is not None and feed_enclosure == 'media':
                fg.load_extension('media', atom=True, rss=True)
                fe.media.add_content({
                    'url': img_url,
                    'type': mimetypes.guess_type(img)[0],
                    'fileSize': str(img_size),
                    'medium': 'image',
                })
            else:
                fe.link([{
                    'href': img_url,
                    'length': str(img_size),
                    'type': mimetypes.guess_type(img)[0],
                    'rel': 'enclosure'
                }])

            if atom_output_name:
                fe.link([{'href': img_url, 'rel': 'alternate'}])

            if rss_output_name:
                fe.rss_link(img_url)

        if atom_output_name:
            self.atom_renderer(fg, atom_output_name, atom_path,
                               self.site.url_replacer(atom_path,
                                                      "/assets/xml/atom.xsl"))
        if rss_output_name:
            self.rss_renderer(fg, rss_output_name, rss_path,
                              self.site.url_replacer(rss_path,
                                                     "/assets/xml/rss.xsl"))
