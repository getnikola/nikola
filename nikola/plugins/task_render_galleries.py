import codecs
import datetime
import glob
import os

from nikola.plugin_categories import Task
from nikola import utils


class Galleries(Task):
    """Copy theme assets into output."""

    name = "render_galleries"

    def gen_tasks(self):
        """Render image galleries."""

        kw = {
            'thumbnail_size': self.site.config['THUMBNAIL_SIZE'],
            'max_image_size': self.site.config['MAX_IMAGE_SIZE'],
            'output_folder': self.site.config['OUTPUT_FOLDER'],
            'default_lang': self.site.config['DEFAULT_LANG'],
            'blog_description': self.site.config['BLOG_DESCRIPTION'],
            'use_filename_as_title': self.site.config['USE_FILENAME_AS_TITLE'],
        }

        # FIXME: lots of work is done even when images don't change,
        # which should be moved into the task.

        template_name = "gallery.tmpl"

        gallery_list = glob.glob("galleries/*")
        # Fail quick if we don't have galleries, so we don't
        # require PIL
        Image = None
        if not gallery_list:
            yield {
                'basename': 'render_galleries',
                'actions': [],
                }
            return
        try:
            import Image as _Image
            import ExifTags
            Image = _Image
        except ImportError:
            try:
                from PIL import Image as _Image, ExifTags  # NOQA
                Image = _Image
            except ImportError:
                pass
        if Image:
            def _resize_image(src, dst, max_size):
                im = Image.open(src)
                w, h = im.size
                if w > max_size or h > max_size:
                    size = max_size, max_size
                    try:
                        exif = im._getexif()
                    except Exception:
                        exif = None
                    if exif is not None:
                        for tag, value in exif.items():
                            decoded = ExifTags.TAGS.get(tag, tag)

                            if decoded == 'Orientation':
                                if value == 3:
                                    im = im.rotate(180)
                                elif value == 6:
                                    im = im.rotate(270)
                                elif value == 8:
                                    im = im.rotate(90)

                                break

                    im.thumbnail(size, Image.ANTIALIAS)
                    im.save(dst)

                else:
                    utils.copy_file(src, dst)

            def create_thumb(src, dst):
                return _resize_image(src, dst, kw['thumbnail_size'])

            def create_resized_image(src, dst):
                return _resize_image(src, dst, kw['max_image_size'])

            dates = {}

            def image_date(src):
                if src not in dates:
                    im = Image.open(src)
                    try:
                        exif = im._getexif()
                    except Exception:
                        exif = None
                    if exif is not None:
                        for tag, value in exif.items():
                            decoded = ExifTags.TAGS.get(tag, tag)
                            if decoded == 'DateTimeOriginal':
                                try:
                                    dates[src] = datetime.datetime.strptime(
                                        value, r'%Y:%m:%d %H:%M:%S')
                                    break
                                except ValueError:  # Invalid EXIF date.
                                    pass
                if src not in dates:
                    dates[src] = datetime.datetime.fromtimestamp(
                        os.stat(src).st_mtime)
                return dates[src]

        else:
            create_thumb = utils.copy_file
            create_resized_image = utils.copy_file

        # gallery_path is "gallery/name"
        for gallery_path in gallery_list:
            # gallery_name is "name"
            gallery_name = os.path.basename(gallery_path)
            # output_gallery is "output/GALLERY_PATH/name"
            output_gallery = os.path.dirname(os.path.join(kw["output_folder"],
                self.site.path("gallery", gallery_name, None)))
            if not os.path.isdir(output_gallery):
                yield {
                    'basename': 'render_galleries',
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

                excluded_image_list = map(add_gallery_path,
                    excluded_image_name_list)
                image_set = set(image_list) - set(excluded_image_list)
                image_list = list(image_set)
            except IOError:
                pass

            image_list = [x for x in image_list if "thumbnail" not in x]
            # Sort by date
            image_list.sort(cmp=lambda a, b: cmp(image_date(a), image_date(b)))
            image_name_list = [os.path.basename(x) for x in image_list]

            thumbs = []
            # Do thumbnails and copy originals
            for img, img_name in zip(image_list, image_name_list):
                # img is "galleries/name/image_name.jpg"
                # img_name is "image_name.jpg"
                # fname, ext are "image_name", ".jpg"
                fname, ext = os.path.splitext(img_name)
                # thumb_path is
                # "output/GALLERY_PATH/name/image_name.thumbnail.jpg"
                thumb_path = os.path.join(output_gallery,
                    fname + ".thumbnail" + ext)
                # thumb_path is "output/GALLERY_PATH/name/image_name.jpg"
                orig_dest_path = os.path.join(output_gallery, img_name)
                thumbs.append(os.path.basename(thumb_path))
                yield {
                    'basename': 'render_galleries',
                    'name': thumb_path,
                    'file_dep': [img],
                    'targets': [thumb_path],
                    'actions': [
                        (create_thumb, (img, thumb_path))
                    ],
                    'clean': True,
                    'uptodate': [utils.config_changed(kw)],
                }
                yield {
                    'basename': 'render_galleries',
                    'name': orig_dest_path,
                    'file_dep': [img],
                    'targets': [orig_dest_path],
                    'actions': [
                        (create_resized_image, (img, orig_dest_path))
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
                    excluded_thumb_dest_path = os.path.join(output_gallery,
                        fname + ".thumbnail" + ext)
                    excluded_dest_path = os.path.join(output_gallery, img_name)
                    yield {
                        'basename': 'render_galleries',
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
                        'basename': 'render_galleries',
                        'name': excluded_dest_path,
                        'file_dep': [exclude_path],
                        #'targets': [excluded_dest_path],
                        'actions': [
                            (utils.remove_file, (excluded_dest_path,))
                        ],
                        'clean': True,
                        'uptodate': [utils.config_changed(kw)],
                    }

            output_name = os.path.join(output_gallery, "index.html")
            context = {}
            context["lang"] = kw["default_lang"]
            context["title"] = os.path.basename(gallery_path)
            context["description"] = kw["blog_description"]
            if kw['use_filename_as_title']:
                img_titles = ['title="%s"' % utils.unslugify(fn[:-4])
                              for fn in image_name_list]
            else:
                img_titles = [''] * len(image_name_list)
            context["images"] = zip(image_name_list, thumbs, img_titles)
            context["permalink"] = self.site.link(
                "gallery", gallery_name, None)

            # Use galleries/name/index.txt to generate a blurb for
            # the gallery, if it exists
            index_path = os.path.join(gallery_path, "index.txt")
            index_dst_path = os.path.join(gallery_path, "index.html")
            if os.path.exists(index_path):
                compile_html = self.site.get_compiler(index_path)
                yield {
                    'basename': 'render_galleries',
                    'name': output_name.encode('utf-8'),
                    'file_dep': [index_path],
                    'targets': [index_dst_path],
                    'actions': [(compile_html,
                        [index_path, index_dst_path])],
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
                'basename': 'render_galleries',
                'name': gallery_path,
                'file_dep': file_dep,
                'targets': [gallery_name],
                'actions': [(render_gallery,
                    (output_name, context, index_dst_path))],
                'clean': True,
                'uptodate': [utils.config_changed(kw)],
            }
