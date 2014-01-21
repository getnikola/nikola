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

from __future__ import unicode_literals
import codecs
import datetime
import glob
import json
import mimetypes
import os
try:
    from urlparse import urljoin
except ImportError:
    from urllib.parse import urljoin  # NOQA

Image = None
try:
    from PIL import Image, ExifTags  # NOQA
except ImportError:
    try:
        import Image as _Image
        import ExifTags
        Image = _Image
    except ImportError:
        pass
import PyRSS2Gen as rss

from nikola.plugin_categories import Task
from nikola import utils
from nikola.post import Post
from nikola.utils import req_missing


class Galleries(Task):
    """Render image galleries."""

    name = 'render_galleries'
    dates = {}

    def set_site(self, site):
        site.register_path_handler('gallery', self.gallery_path)
        site.register_path_handler('gallery_rss', self.gallery_rss_path)
        return super(Galleries, self).set_site(site)

    def gallery_path(self, name, lang):
        return [_f for _f in [self.site.config['TRANSLATIONS'][lang],
                              self.site.config['GALLERY_PATH'], name,
                              self.site.config['INDEX_FILE']] if _f]

    def gallery_rss_path(self, name, lang):
        return [_f for _f in [self.site.config['TRANSLATIONS'][lang],
                              self.site.config['GALLERY_PATH'], name,
                              'rss.xml'] if _f]

    def gen_tasks(self):
        """Render image galleries."""

        if Image is None:
            req_missing(['pillow'], 'render galleries')

        self.logger = utils.get_logger('render_galleries', self.site.loghandlers)
        self.image_ext_list = ['.jpg', '.png', '.jpeg', '.gif', '.svg', '.bmp', '.tiff']
        self.image_ext_list.extend(self.site.config.get('EXTRA_IMAGE_EXTENSIONS', []))

        self.kw = {
            'thumbnail_size': self.site.config['THUMBNAIL_SIZE'],
            'max_image_size': self.site.config['MAX_IMAGE_SIZE'],
            'output_folder': self.site.config['OUTPUT_FOLDER'],
            'cache_folder': self.site.config['CACHE_FOLDER'],
            'default_lang': self.site.config['DEFAULT_LANG'],
            'use_filename_as_title': self.site.config['USE_FILENAME_AS_TITLE'],
            'gallery_path': self.site.config['GALLERY_PATH'],
            'sort_by_date': self.site.config['GALLERY_SORT_BY_DATE'],
            'filters': self.site.config['FILTERS'],
            'translations': self.site.config['TRANSLATIONS'],
            'global_context': self.site.GLOBAL_CONTEXT,
            "feed_length": self.site.config['FEED_LENGTH'],
        }

        yield self.group_task()

        template_name = "gallery.tmpl"

        # Find all galleries we need to process
        self.find_galleries()

        # Create all output folders
        for task in self.create_galleries():
            yield task

        # For each gallery:
        for gallery in self.gallery_list:

            # Create subfolder list
            folder_list = [(x, x.split(os.sep)[-2]) for x in
                           glob.glob(os.path.join(gallery, '*') + os.sep)]

            # Parse index into a post (with translations)
            post = self.parse_index(gallery)

            # Create image list, filter exclusions
            image_list = self.get_image_list(gallery)

            # Sort as needed
            # Sort by date
            if self.kw['sort_by_date']:
                image_list.sort(key=lambda a: self.image_date(a))
            else:  # Sort by name
                image_list.sort()

            # Create thumbnails and large images in destination
            for image in image_list:
                for task in self.create_target_images(image):
                    yield task

            # Remove excluded images
            for image in self.get_excluded_images(gallery):
                for task in self.remove_excluded_image(image):
                    yield task

            crumbs = utils.get_crumbs(gallery, index_folder=self)

            # Create index.html for each language
            for lang in self.kw['translations']:
                dst = os.path.join(
                    self.kw['output_folder'],
                    self.site.path(
                        "gallery",
                        os.path.relpath(gallery, self.kw['gallery_path']), lang))
                dst = os.path.normpath(dst)

                context = {}
                context["lang"] = lang
                if post:
                    context["title"] = post.title(lang)
                else:
                    context["title"] = os.path.basename(gallery)
                context["description"] = None

                image_name_list = [os.path.basename(p) for p in image_list]

                if self.kw['use_filename_as_title']:
                    img_titles = []
                    for fn in image_name_list:
                        name_without_ext = os.path.splitext(fn)[0]
                        img_titles.append(
                            'id="{0}" alt="{1}" title="{2}"'.format(
                                name_without_ext,
                                name_without_ext,
                                utils.unslugify(name_without_ext)))
                else:
                    img_titles = [''] * len(image_name_list)

                thumbs = ['.thumbnail'.join(os.path.splitext(p)) for p in image_list]
                thumbs = [os.path.join(self.kw['output_folder'], t) for t in thumbs]

                folders = []

                # Generate friendly gallery names
                for path, folder in folder_list:
                    fpost = self.parse_index(path)
                    if fpost:
                        ft = fpost.title(lang) or folder
                    else:
                        ft = folder
                    folders.append((folder, ft))

                ## TODO: in v7 remove images from context, use photo_array
                context["images"] = list(zip(image_name_list, thumbs, img_titles))
                context["folders"] = folders
                context["crumbs"] = crumbs
                context["permalink"] = self.site.link(
                    "gallery", os.path.basename(gallery), lang)
                # FIXME: use kw
                context["enable_comments"] = (
                    self.site.config["COMMENTS_IN_GALLERIES"])
                context["thumbnail_size"] = self.kw["thumbnail_size"]

                # FIXME: render post in a task
                if post:
                    post.compile(lang)
                    context['text'] = post.text(lang)
                else:
                    context['text'] = ''

                file_dep = self.site.template_system.template_deps(
                    template_name) + image_list + thumbs

                yield utils.apply_filters({
                    'basename': self.name,
                    'name': dst,
                    'file_dep': file_dep,
                    'targets': [dst],
                    'actions': [
                        (self.render_gallery_index, (
                            template_name,
                            dst,
                            context,
                            image_list,
                            thumbs,
                            file_dep))],
                    'clean': True,
                    'uptodate': [utils.config_changed({
                        1: self.kw,
                        2: self.site.config["COMMENTS_IN_GALLERIES"],
                        3: context,
                    })],
                }, self.kw['filters'])

                # RSS for the gallery
                rss_dst = os.path.join(
                    self.kw['output_folder'],
                    self.site.path(
                        "gallery_rss",
                        os.path.relpath(gallery, self.kw['gallery_path']), lang))
                rss_dst = os.path.normpath(rss_dst)

                yield utils.apply_filters({
                    'basename': self.name,
                    'name': rss_dst,
                    'file_dep': file_dep,
                    'targets': [rss_dst],
                    'actions': [
                        (self.gallery_rss, (
                            image_list,
                            img_titles,
                            lang,
                            self.site.link(
                                "gallery_rss", os.path.basename(gallery), lang),
                            rss_dst,
                            context['title']
                        ))],
                    'clean': True,
                    'uptodate': [utils.config_changed({
                        1: self.kw,
                    })],
                }, self.kw['filters'])

    def find_galleries(self):
        """Find all galleries to be processed according to conf.py"""

        self.gallery_list = []
        for root, dirs, files in os.walk(self.kw['gallery_path']):
            self.gallery_list.append(root)

    def create_galleries(self):
        """Given a list of galleries, create the output folders."""

        # gallery_path is "gallery/foo/name"
        for gallery_path in self.gallery_list:
            gallery_name = os.path.relpath(gallery_path, self.kw['gallery_path'])
            # have to use dirname because site.path returns .../index.html
            output_gallery = os.path.dirname(
                os.path.join(
                    self.kw["output_folder"],
                    self.site.path("gallery", gallery_name)))
            output_gallery = os.path.normpath(output_gallery)
            # Task to create gallery in output/
            yield {
                'basename': self.name,
                'name': output_gallery,
                'actions': [(utils.makedirs, (output_gallery,))],
                'targets': [output_gallery],
                'clean': True,
                'uptodate': [utils.config_changed(self.kw)],
            }

    def parse_index(self, gallery):
        """Returns a Post object if there is an index.txt."""

        index_path = os.path.join(gallery, "index.txt")
        destination = os.path.join(
            self.kw["output_folder"],
            gallery)
        if os.path.isfile(index_path):
            post = Post(
                index_path,
                self.site.config,
                destination,
                False,
                self.site.MESSAGES,
                'story.tmpl',
                self.site.get_compiler(index_path)
            )
            # If this did not exist, galleries without a title in the
            # index.txt file would be errorneously named `index`
            # (warning: galleries titled index and filenamed differently
            #  may break)
            if post.title == 'index':
                post.title = os.path.split(gallery)[1]
        else:
            post = None
        return post

    def get_excluded_images(self, gallery_path):
        exclude_path = os.path.join(gallery_path, "exclude.meta")

        try:
            f = open(exclude_path, 'r')
            excluded_image_name_list = f.read().split()
        except IOError:
            excluded_image_name_list = []

        excluded_image_list = ["{0}/{1}".format(gallery_path, i) for i in excluded_image_name_list]
        return excluded_image_list

    def get_image_list(self, gallery_path):

        # Gather image_list contains "gallery/name/image_name.jpg"
        image_list = []

        for ext in self.image_ext_list:
            image_list += glob.glob(gallery_path + '/*' + ext.lower()) +\
                glob.glob(gallery_path + '/*' + ext.upper())

        # Filter ignored images
        excluded_image_list = self.get_excluded_images(gallery_path)
        image_set = set(image_list) - set(excluded_image_list)
        image_list = list(image_set)
        return image_list

    def create_target_images(self, img):
        gallery_name = os.path.relpath(os.path.dirname(img), self.kw['gallery_path'])
        output_gallery = os.path.dirname(
            os.path.join(
                self.kw["output_folder"],
                self.site.path("gallery", gallery_name)))
        # Do thumbnails and copy originals
        # img is "galleries/name/image_name.jpg"
        # img_name is "image_name.jpg"
        # fname, ext are "image_name", ".jpg"
        # thumb_path is
        # "output/GALLERY_PATH/name/image_name.thumbnail.jpg"
        img_name = os.path.basename(img)
        fname, ext = os.path.splitext(img_name)
        thumb_path = os.path.join(
            output_gallery,
            ".thumbnail".join([fname, ext]))
        # thumb_path is "output/GALLERY_PATH/name/image_name.jpg"
        orig_dest_path = os.path.join(output_gallery, img_name)
        yield utils.apply_filters({
            'basename': self.name,
            'name': thumb_path,
            'file_dep': [img],
            'targets': [thumb_path],
            'actions': [
                (self.resize_image,
                    (img, thumb_path, self.kw['thumbnail_size']))
            ],
            'clean': True,
            'uptodate': [utils.config_changed({
                1: self.kw['thumbnail_size']
            })],
        }, self.kw['filters'])

        yield utils.apply_filters({
            'basename': self.name,
            'name': orig_dest_path,
            'file_dep': [img],
            'targets': [orig_dest_path],
            'actions': [
                (self.resize_image,
                    (img, orig_dest_path, self.kw['max_image_size']))
            ],
            'clean': True,
            'uptodate': [utils.config_changed({
                1: self.kw['max_image_size']
            })],
        }, self.kw['filters'])

    def remove_excluded_image(self, img):
        # Remove excluded images
        # img is something like galleries/demo/tesla2_lg.jpg so it's the *source* path
        # and we should remove both the large and thumbnail *destination* paths

        img = os.path.relpath(img, self.kw['gallery_path'])
        output_folder = os.path.dirname(
            os.path.join(
                self.kw["output_folder"],
                self.site.path("gallery", os.path.dirname(img))))
        img_path = os.path.join(output_folder, os.path.basename(img))
        fname, ext = os.path.splitext(img_path)
        thumb_path = fname + '.thumbnail' + ext

        yield utils.apply_filters({
            'basename': '_render_galleries_clean',
            'name': thumb_path,
            'actions': [
                (utils.remove_file, (thumb_path,))
            ],
            'clean': True,
            'uptodate': [utils.config_changed(self.kw)],
        }, self.kw['filters'])

        yield utils.apply_filters({
            'basename': '_render_galleries_clean',
            'name': img_path,
            'actions': [
                (utils.remove_file, (img_path,))
            ],
            'clean': True,
            'uptodate': [utils.config_changed(self.kw)],
        }, self.kw['filters'])

    def render_gallery_index(
            self,
            template_name,
            output_name,
            context,
            img_list,
            thumbs,
            file_dep):
        """Build the gallery index."""

        # The photo array needs to be created here, because
        # it relies on thumbnails already being created on
        # output

        def url_from_path(p):
            url = '/'.join(os.path.relpath(p, os.path.dirname(output_name) + os.sep).split(os.sep))
            return url

        photo_array = []
        for img, thumb in zip(img_list, thumbs):
            im = Image.open(thumb)
            w, h = im.size
            title = ''
            if self.kw['use_filename_as_title']:
                title = utils.unslugify(os.path.splitext(img)[0])
            # Thumbs are files in output, we need URLs
            photo_array.append({
                'url': url_from_path(img),
                'url_thumb': url_from_path(thumb),
                'title': title,
                'size': {
                    'w': w,
                    'h': h
                },
            })
        context['photo_array_json'] = json.dumps(photo_array)
        context['photo_array'] = photo_array

        self.site.render_template(template_name, output_name, context)

    def gallery_rss(self, img_list, img_titles, lang, permalink, output_path, title):
        """Create a RSS showing the latest images in the gallery.

        This doesn't use generic_rss_renderer because it
        doesn't involve Post objects.
        """

        def make_url(url):
            return urljoin(self.site.config['BASE_URL'], url.lstrip('/'))

        items = []
        for img, full_title in list(zip(img_list, img_titles))[:self.kw["feed_length"]]:
            img_size = os.stat(
                os.path.join(
                    self.site.config['OUTPUT_FOLDER'], img)).st_size
            args = {
                'title': full_title.split('"')[-2] if full_title else '',
                'link': make_url(img),
                'guid': rss.Guid(img, False),
                'pubDate': self.image_date(img),
                'enclosure': rss.Enclosure(
                    make_url(img),
                    img_size,
                    mimetypes.guess_type(img)[0]
                ),
            }
            items.append(rss.RSSItem(**args))
        rss_obj = utils.ExtendedRSS2(
            title=title,
            link=make_url(permalink),
            description='',
            lastBuildDate=datetime.datetime.now(),
            items=items,
            generator='Nikola <http://getnikola.com/>',
            language=lang
        )
        rss_obj.self_url = make_url(permalink)
        rss_obj.rss_attrs["xmlns:atom"] = "http://www.w3.org/2005/Atom"
        dst_dir = os.path.dirname(output_path)
        utils.makedirs(dst_dir)
        with codecs.open(output_path, "wb+", "utf-8") as rss_file:
            data = rss_obj.to_xml(encoding='utf-8')
            if isinstance(data, utils.bytes_str):
                data = data.decode('utf-8')
            rss_file.write(data)

    def resize_image(self, src, dst, max_size):
        """Make a copy of the image in the requested size."""
        if not Image:
            utils.copy_file(src, dst)
            return
        im = Image.open(src)
        w, h = im.size
        if w > max_size or h > max_size:
            size = max_size, max_size

            # Panoramas get larger thumbnails because they look *awful*
            if w > 2 * h:
                size = min(w, max_size * 4), min(w, max_size * 4)

            try:
                exif = im._getexif()
            except Exception:
                exif = None
            if exif is not None:
                for tag, value in list(exif.items()):
                    decoded = ExifTags.TAGS.get(tag, tag)

                    if decoded == 'Orientation':
                        if value == 3:
                            im = im.rotate(180)
                        elif value == 6:
                            im = im.rotate(270)
                        elif value == 8:
                            im = im.rotate(90)
                        break
            try:
                im.thumbnail(size, Image.ANTIALIAS)
                im.save(dst)
            except Exception as e:
                self.logger.warn("Can't thumbnail {0}, using original "
                                 "image as thumbnail ({1})".format(src, e))
                utils.copy_file(src, dst)
        else:  # Image is small
            utils.copy_file(src, dst)

    def image_date(self, src):
        """Try to figure out the date of the image."""
        if src not in self.dates:
            try:
                im = Image.open(src)
                exif = im._getexif()
            except Exception:
                exif = None
            if exif is not None:
                for tag, value in list(exif.items()):
                    decoded = ExifTags.TAGS.get(tag, tag)
                    if decoded == 'DateTimeOriginal':
                        try:
                            self.dates[src] = datetime.datetime.strptime(
                                value, r'%Y:%m:%d %H:%M:%S')
                            break
                        except ValueError:  # Invalid EXIF date.
                            pass
        if src not in self.dates:
            self.dates[src] = datetime.datetime.fromtimestamp(
                os.stat(src).st_mtime)
        return self.dates[src]
