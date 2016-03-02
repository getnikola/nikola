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

"""Process images."""

from __future__ import unicode_literals
import datetime
import os
import lxml
import re
import gzip

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

    def resize_image(self, src, dst, max_size, bigger_panoramas=True, preserve_exif_data=False):
        """Make a copy of the image in the requested size."""
        if not Image or os.path.splitext(src)[1] in ['.svg', '.svgz']:
            self.resize_svg(src, dst, max_size, bigger_panoramas)
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
            _exif = im.info.get('exif')
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
                if _exif is not None and preserve_exif_data:
                    im.save(dst, exif=_exif)
                else:
                    im.save(dst)
            except Exception as e:
                self.logger.warn("Can't thumbnail {0}, using original "
                                 "image as thumbnail ({1})".format(src, e))
                utils.copy_file(src, dst)
        else:  # Image is small
            utils.copy_file(src, dst)

    def resize_svg(self, src, dst, max_size, bigger_panoramas):
        """Make a copy of an svg at the requested size."""
        try:
            # Resize svg based on viewport hacking.
            # note that this can also lead to enlarged svgs
            if src.endswith('.svgz'):
                with gzip.GzipFile(src) as op:
                    xml = op.read()
            else:
                with open(src) as op:
                    xml = op.read()
            tree = lxml.etree.XML(xml)
            width = tree.attrib['width']
            height = tree.attrib['height']
            w = int(re.search("[0-9]+", width).group(0))
            h = int(re.search("[0-9]+", height).group(0))
            # calculate new size preserving aspect ratio.
            ratio = float(w) / h
            # Panoramas get larger thumbnails because they look *awful*
            if bigger_panoramas and w > 2 * h:
                max_size = max_size * 4
            if w > h:
                w = max_size
                h = max_size / ratio
            else:
                w = max_size * ratio
                h = max_size
            w = int(w)
            h = int(h)
            tree.attrib.pop("width")
            tree.attrib.pop("height")
            tree.attrib['viewport'] = "0 0 %ipx %ipx" % (w, h)
            if dst.endswith('.svgz'):
                op = gzip.GzipFile(dst, 'w')
            else:
                op = open(dst, 'w')
            op.write(lxml.etree.tostring(tree))
            op.close()
        except (KeyError, AttributeError) as e:
            self.logger.warn("No width/height in %s. Original exception: %s" % (src, e))
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
                            if isinstance(value, tuple):
                                value = value[0]
                            self.dates[src] = datetime.datetime.strptime(
                                value, '%Y:%m:%d %H:%M:%S')
                            break
                        except ValueError:  # Invalid EXIF date.
                            pass
        if src not in self.dates:
            self.dates[src] = datetime.datetime.fromtimestamp(
                os.stat(src).st_mtime)
        return self.dates[src]
