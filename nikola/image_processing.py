# -*- coding: utf-8 -*-

# Copyright © 2014 Roberto Alsina and others.

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
import datetime
import os

from nikola import utils

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


class ImageProcessor(object):
    """Apply image operations."""

    image_ext_list_builtin = ['.jpg', '.png', '.jpeg', '.gif', '.svg', '.bmp', '.tiff']

    def resize_image(self, src, dst, max_size, bigger_panoramas=True):
        """Make a copy of the image in the requested size."""
        if not Image:
            utils.copy_file(src, dst)
            return
        im = Image.open(src)
        w, h = im.size
        if w > max_size or h > max_size:
            size = max_size, max_size

            # Panoramas get larger thumbnails because they look *awful*
            if bigger_panoramas and w > 2 * h:
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
