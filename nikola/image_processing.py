from __future__ import unicode_literals
import io
import datetime
import glob
import json
import mimetypes
import os
try:
    from urlparse import urljoin
except ImportError:
    from urllib.parse import urljoin  # NOQA

import natsort
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

#from nikola import utils
#from nikola.post import Post
#from nikola.utils import req_missing

_image_size_cache = {}


class ImageProcessor(object):
    """Apply image operations."""

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
                    if decoded in ('DateTimeOriginal', 'DateTimeDigitized'):
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
