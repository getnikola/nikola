# Copyright (c) 2012 Roberto Alsina y otros.

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
import os

Image = None
try:
    import Image as _Image
    import ExifTags
    Image = _Image
except ImportError:
    try:
        from PIL import Image, ExifTags  # NOQA
    except ImportError:
        pass


from nikola.plugin_categories import Task
from nikola import utils


class Galleries(Task):
    """Copy theme assets into output."""

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
            'gallery_path': self.site.config['GALLERY_PATH']
        }

        # FIXME: lots of work is done even when images don't change,
        # which should be moved into the task.

        template_name = "gallery.tmpl"

        gallery_list = []
        for root, dirs, files in os.walk(kw['gallery_path']):
            gallery_list.append(root)
        if not gallery_list:
            yield {
                'basename': str('render_galleries'),
                'actions': [],
            }
            return

        # gallery_path is "gallery/name"
        for gallery_path in gallery_list:
            # gallery_name is "name"
            splitted = gallery_path.split(os.sep)[1:]
            if not splitted:
                gallery_name = ''
            else:
                gallery_name = os.path.join(*splitted)
            # output_gallery is "output/GALLERY_PATH/name"
            output_gallery = os.path.dirname(os.path.join(
                kw["output_folder"], self.site.path("gallery", gallery_name,
                                                    None)))
            output_name = os.path.join(output_gallery, self.site.config['INDEX_FILE'])
            if not os.path.isdir(output_gallery):
                yield {
                    'basename': str('render_galleries'),
                    'name': output_gallery,
                    'actions': [(os.makedirs, (output_gallery,))],
                    'targets': [output_gallery],
                    'clean': True,
                    'uptodate': [utils.config_changed(kw)],
                }
            # image_list contains "gallery/name/image_name.jpg"
            image_list = glob.glob(gallery_path + "/*jpg") +\
                glob.glob(gallery_path + "/*JPG") +\
                glob.glob(gallery_path + "/*PNG") +\
                glob.glob(gallery_path + "/*png")

            # Filter ignore images
            try:
                def add_gallery_path(index):
                    return "{0}/{1}".format(gallery_path, index)

                exclude_path = os.path.join(gallery_path, "exclude.meta")
                try:
                    f = open(exclude_path, 'r')
                    excluded_image_name_list = f.read().split()
                except IOError:
                    excluded_image_name_list = []

                excluded_image_list = list(map(add_gallery_path,
                                               excluded_image_name_list))
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
            image_list.sort(key=lambda a: self.image_date(a))
            image_name_list = [os.path.basename(x) for x in image_list]
            thumbs = []
            # Do thumbnails and copy originals
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
                yield {
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
                }
                yield {
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
                }

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
                    yield {
                        'basename': str('render_galleries_clean'),
                        'name': excluded_thumb_dest_path,
                        'file_dep': [exclude_path],
                        #'targets': [excluded_thumb_dest_path],
                        'actions': [
                            (utils.remove_file, (excluded_thumb_dest_path,))
                        ],
                        'clean': True,
                        'uptodate': [utils.config_changed(kw)],
                    }
                    yield {
                        'basename': str('render_galleries_clean'),
                        'name': excluded_dest_path,
                        'file_dep': [exclude_path],
                        #'targets': [excluded_dest_path],
                        'actions': [
                            (utils.remove_file, (excluded_dest_path,))
                        ],
                        'clean': True,
                        'uptodate': [utils.config_changed(kw)],
                    }

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
            context["images"] = list(zip(image_name_list, thumbs, img_titles))
            context["folders"] = folder_list
            context["crumbs"] = crumbs
            context["permalink"] = self.site.link(
                "gallery", gallery_name, None)
            context["enable_comments"] = (
                self.site.config["COMMENTS_IN_GALLERIES"])

            # Use galleries/name/index.txt to generate a blurb for
            # the gallery, if it exists
            index_path = os.path.join(gallery_path, "index.txt")
            cache_dir = os.path.join(kw["cache_folder"], 'galleries')
            if not os.path.isdir(cache_dir):
                os.makedirs(cache_dir)
            index_dst_path = os.path.join(
                cache_dir,
                str(hashlib.sha224(index_path.encode('utf-8')).hexdigest() +
                    '.html'))
            if os.path.exists(index_path):
                compile_html = self.site.get_compiler(index_path).compile_html
                yield {
                    'basename': str('render_galleries'),
                    'name': index_dst_path,
                    'file_dep': [index_path],
                    'targets': [index_dst_path],
                    'actions': [(compile_html, [index_path, index_dst_path, True])],
                    'clean': True,
                    'uptodate': [utils.config_changed(kw)],
                }

            file_dep = self.site.template_system.template_deps(
                template_name) + image_list

            def render_gallery(output_name, context, index_dst_path):
                if os.path.exists(index_dst_path):
                    with codecs.open(index_dst_path, "rb", "utf8") as fd:
                        context['text'] = fd.read()
                    file_dep.append(index_dst_path)
                else:
                    context['text'] = ''
                self.site.render_template(template_name, output_name, context)

            yield {
                'basename': str('render_galleries'),
                'name': output_name,
                'file_dep': file_dep,
                'targets': [output_name],
                'actions': [(render_gallery, (output_name, context,
                                              index_dst_path))],
                'clean': True,
                'uptodate': [utils.config_changed({
                    1: kw,
                    2: self.site.config['GLOBAL_CONTEXT'],
                    3: self.site.config["COMMENTS_IN_GALLERIES"],
                })],
            }

    def resize_image(self, src, dst, max_size):
        """Make a copy of the image in the requested size."""
        if not Image:
            utils.copy_file(src, dst)
            return
        im = Image.open(src)
        w, h = im.size
        if w > max_size or h > max_size:
            size = max_size, max_size
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
            except Exception:
                # TODO: inform the user, but do not fail
                pass
            else:
                im.save(dst)

        else:
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
