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

from __future__ import unicode_literals
import codecs
import datetime
import glob
import hashlib
import json
import os

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


from nikola.plugin_categories import Task
from nikola import utils


class Galleries(Task):
    """Render image galleries."""

    name = str("render_galleries")
    dates = {}

    def gen_tasks(self):
        """Render image galleries."""

        kw = {
            'thumbnail_size': self.site.config['THUMBNAIL_SIZE'],
            'max_image_size': self.site.config['MAX_IMAGE_SIZE'],
            'output_folder': self.site.config['OUTPUT_FOLDER'],
            'cache_folder': self.site.config['CACHE_FOLDER'],
            'default_lang': self.site.config['DEFAULT_LANG'],
            'blog_description': self.site.config['BLOG_DESCRIPTION'],
            'use_filename_as_title': self.site.config['USE_FILENAME_AS_TITLE'],
            'gallery_path': self.site.config['GALLERY_PATH'],
            'sort_by_date': self.site.config['GALLERY_SORT_BY_DATE'],
            'filters': self.site.config['FILTERS'],
            'global_context': self.site.GLOBAL_CONTEXT,
        }

        yield self.group_task()
        # FIXME: lots of work is done even when images don't change,
        # which should be moved into the task.

        template_name = "gallery.tmpl"

        gallery_list = []
        for root, dirs, files in os.walk(kw['gallery_path']):
            gallery_list.append(root)
        # gallery_path is "gallery/name"
        for gallery_path in gallery_list:
            # gallery_name is "name"
            splitted = gallery_path.split(os.sep)[1:]
            if not splitted:
                gallery_name = ''
            else:
                gallery_name = os.path.join(*splitted)

            # Task to create gallery in output/
            # output_gallery is "output/GALLERY_PATH/name"
            output_gallery = os.path.dirname(os.path.join(
                kw["output_folder"], self.site.path("gallery", gallery_name,
                                                    None)))
            output_name = os.path.join(output_gallery, self.site.config['INDEX_FILE'])
            if not os.path.isdir(output_gallery):
                yield utils.apply_filters({
                    'basename': str('render_galleries'),
                    'name': output_gallery,
                    'actions': [(utils.makedirs, (output_gallery,))],
                    'targets': [output_gallery],
                    'clean': True,
                    'uptodate': [utils.config_changed(kw)],
                }, kw['filters'])

            # Gather image_list contains "gallery/name/image_name.jpg"
            image_list = glob.glob(gallery_path + "/*jpg") +\
                glob.glob(gallery_path + "/*JPG") +\
                glob.glob(gallery_path + "/*png") +\
                glob.glob(gallery_path + "/*PNG")

            # Filter ignored images
            try:
                exclude_path = os.path.join(gallery_path, "exclude.meta")
                try:
                    f = open(exclude_path, 'r')
                    excluded_image_name_list = f.read().split()
                except IOError:
                    excluded_image_name_list = []
                excluded_image_list = ["{0}/{1}".format(gallery_path, i) for i in excluded_image_name_list]
                image_set = set(image_list) - set(excluded_image_list)
                image_list = list(image_set)
            except IOError:
                pass

            # List of sub-galleries
            folder_list = [x.split(os.sep)[-2] for x in
                           glob.glob(os.path.join(gallery_path, '*') + os.sep)]

            crumbs = utils.get_crumbs(gallery_path)

            image_list = [x for x in image_list if "thumbnail" not in x]
            # Sort by date
            if kw['sort_by_date']:
                image_list.sort(key=lambda a: self.image_date(a))
            else:  # Sort by name
                image_list.sort()
            image_name_list = [os.path.basename(x) for x in image_list]

            # List of thumbnail paths
            thumb_list = []

            # Do thumbnails and copy originals
            thumbs = []
            for img, img_name in list(zip(image_list, image_name_list)):
                # img is "galleries/name/image_name.jpg"
                # img_name is "image_name.jpg"
                # fname, ext are "image_name", ".jpg"
                fname, ext = os.path.splitext(img_name)
                # thumb_path is
                # "output/GALLERY_PATH/name/image_name.thumbnail.jpg"
                thumb_path = os.path.join(output_gallery,
                                          ".thumbnail".join([fname, ext]))
                # thumb_path is "output/GALLERY_PATH/name/image_name.jpg"
                orig_dest_path = os.path.join(output_gallery, img_name)
                thumbs.append(os.path.basename(thumb_path))
                thumb_list.append(thumb_path)
                yield utils.apply_filters({
                    'basename': str('render_galleries'),
                    'name': thumb_path,
                    'file_dep': [img],
                    'targets': [thumb_path],
                    'actions': [
                        (self.resize_image,
                            (img, thumb_path, kw['thumbnail_size']))
                    ],
                    'clean': True,
                    'uptodate': [utils.config_changed(kw)],
                }, kw['filters'])
                yield utils.apply_filters({
                    'basename': str('render_galleries'),
                    'name': orig_dest_path,
                    'file_dep': [img],
                    'targets': [orig_dest_path],
                    'actions': [
                        (self.resize_image,
                            (img, orig_dest_path, kw['max_image_size']))
                    ],
                    'clean': True,
                    'uptodate': [utils.config_changed(kw)],
                }, kw['filters'])

            # Remove excluded images
            if excluded_image_name_list:
                for img, img_name in zip(excluded_image_list,
                                         excluded_image_name_list):
                    # img_name is "image_name.jpg"
                    # fname, ext are "image_name", ".jpg"
                    fname, ext = os.path.splitext(img_name)
                    excluded_thumb_dest_path = os.path.join(
                        output_gallery, ".thumbnail".join([fname, ext]))
                    excluded_dest_path = os.path.join(output_gallery, img_name)
                    yield utils.apply_filters({
                        'basename': str('render_galleries_clean'),
                        'name': excluded_thumb_dest_path,
                        'file_dep': [exclude_path],
                        #'targets': [excluded_thumb_dest_path],
                        'actions': [
                            (utils.remove_file, (excluded_thumb_dest_path,))
                        ],
                        'clean': True,
                        'uptodate': [utils.config_changed(kw)],
                    }, kw['filters'])
                    yield utils.apply_filters({
                        'basename': str('render_galleries_clean'),
                        'name': excluded_dest_path,
                        'file_dep': [exclude_path],
                        #'targets': [excluded_dest_path],
                        'actions': [
                            (utils.remove_file, (excluded_dest_path,))
                        ],
                        'clean': True,
                        'uptodate': [utils.config_changed(kw)],
                    }, kw['filters'])

            # Use galleries/name/index.txt to generate a blurb for
            # the gallery, if it exists.

            index_path = os.path.join(gallery_path, "index.txt")
            cache_dir = os.path.join(kw["cache_folder"], 'galleries')
            utils.makedirs(cache_dir)
            index_dst_path = os.path.join(
                cache_dir,
                str(hashlib.sha224(index_path.encode('utf-8')).hexdigest() +
                    '.html'))
            if os.path.exists(index_path):
                compile_html = self.site.get_compiler(index_path).compile_html
                yield utils.apply_filters({
                    'basename': str('render_galleries'),
                    'name': index_dst_path,
                    'file_dep': [index_path],
                    'targets': [index_dst_path],
                    'actions': [(compile_html, [index_path, index_dst_path, True])],
                    'clean': True,
                    'uptodate': [utils.config_changed(kw)],
                }, kw['filters'])

            context = {}
            context["lang"] = kw["default_lang"]
            context["title"] = os.path.basename(gallery_path)
            context["description"] = kw["blog_description"]
            if kw['use_filename_as_title']:
                img_titles = ['id="{0}" alt="{1}" title="{2}"'.format(
                    fn[:-4], fn[:-4], utils.unslugify(fn[:-4])) for fn
                    in image_name_list]
            else:
                img_titles = [''] * len(image_name_list)
            # In the future, remove images from context, use photo_array
            context["images"] = list(zip(image_name_list, thumbs, img_titles))
            context["folders"] = folder_list
            context["crumbs"] = crumbs
            context["permalink"] = self.site.link(
                "gallery", gallery_name, None)
            context["enable_comments"] = (
                self.site.config["COMMENTS_IN_GALLERIES"])
            context["thumbnail_size"] = kw["thumbnail_size"]

            file_dep = self.site.template_system.template_deps(
                template_name) + image_list + thumb_list

            yield utils.apply_filters({
                'basename': str('render_galleries'),
                'name': output_name,
                'file_dep': file_dep,
                'targets': [output_name],
                'actions': [(self.render_gallery_index,
                             (template_name,
                              output_name,
                              context,
                              index_dst_path,
                              image_name_list,
                              thumbs,
                              file_dep,
                              kw))],
                'clean': True,
                'uptodate': [utils.config_changed({
                    1: kw,
                    2: self.site.config["COMMENTS_IN_GALLERIES"],
                    3: context,
                })],
            }, kw['filters'])

    def render_gallery_index(
            self,
            template_name,
            output_name,
            context,
            index_dst_path,
            img_name_list,
            thumbs,
            file_dep,
            kw):
        """Build the gallery index."""

        # The photo array needs to be created here, because
        # it relies on thumbnails already being created on
        # output

        photo_array = []
        d_name = os.path.dirname(output_name)
        for name, thumb_name in zip(img_name_list, thumbs):
            im = Image.open(os.path.join(d_name, thumb_name))
            w, h = im.size
            title = ''
            if kw['use_filename_as_title']:
                title = utils.unslugify(os.path.splitext(name)[0])
            photo_array.append({
                'url': name,
                'url_thumb': thumb_name,
                'title': title,
                'size': {
                    'w': w,
                    'h': h
                },
            })
        context['photo_array_json'] = json.dumps(photo_array)
        context['photo_array'] = photo_array

        if os.path.exists(index_dst_path):
            with codecs.open(index_dst_path, "rb", "utf8") as fd:
                context['text'] = fd.read()
            file_dep.append(index_dst_path)
        else:
            context['text'] = ''
        self.site.render_template(template_name, output_name, context)

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
            except Exception:
                utils.LOGGER.warn("Can't thumbnail {0}, using original image as thumbnail".format(src))
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
