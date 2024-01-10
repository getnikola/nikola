# -*- coding: utf-8 -*-

# Copyright © 2012-2024 Roberto Alsina and others.

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

import datetime
import gzip
import os
import re

import lxml
import piexif
from PIL import ExifTags, Image

from nikola import utils

EXIF_TAG_NAMES = {}


class ImageProcessor(object):
    """Apply image operations."""

    image_ext_list_builtin = ['.jpg', '.png', '.jpeg', '.gif', '.svg', '.svgz', '.bmp', '.tiff', '.webp']

    def _fill_exif_tag_names(self):
        """Connect EXIF tag names to numeric values."""
        if not EXIF_TAG_NAMES:
            for ifd in piexif.TAGS:
                for tag, data in piexif.TAGS[ifd].items():
                    EXIF_TAG_NAMES[tag] = data['name']

    def filter_exif(self, exif, whitelist):
        """Filter EXIF data as described in the documentation."""
        # Scenario 1: keep everything
        if whitelist == {'*': '*'}:
            return exif

        # Scenario 2: keep nothing
        if whitelist == {}:
            return None

        # Scenario 3: keep some
        self._fill_exif_tag_names()
        exif = exif.copy()  # Don't modify in-place, it's rude
        for k in list(exif.keys()):
            if not isinstance(exif[k], dict):
                pass  # At least thumbnails have no fields
            elif k not in whitelist:
                exif.pop(k)  # Not whitelisted, remove
            elif k in whitelist and whitelist[k] == '*':
                # Fully whitelisted, keep all
                pass
            else:
                # Partially whitelisted
                for tag in list(exif[k].keys()):
                    if EXIF_TAG_NAMES[tag] not in whitelist[k]:
                        exif[k].pop(tag)

        return exif or None

    def resize_image(self, src, dst=None, max_size=None, bigger_panoramas=True, preserve_exif_data=False, exif_whitelist={}, preserve_icc_profiles=False, dst_paths=None, max_sizes=None):
        """Make a copy of the image in the requested size(s).

        max_sizes should be a list of sizes, and the image would be resized to fit in a
        square of each size (preserving aspect ratio).

        dst_paths is a list of the destination paths, and should be the same length as max_sizes.

        Backwards compatibility:

        * If max_sizes is None, it's set to [max_size]
        * If dst_paths is None, it's set to [dst]
        * Either max_size or max_sizes should be set
        * Either dst or dst_paths should be set
        """
        if dst_paths is None:
            dst_paths = [dst]
        if max_sizes is None:
            max_sizes = [max_size]
        if len(max_sizes) != len(dst_paths):
            raise ValueError('resize_image called with incompatible arguments: {} / {}'.format(dst_paths, max_sizes))
        extension = os.path.splitext(src)[1].lower()
        if extension in {'.svg', '.svgz'}:
            self.resize_svg(src, dst_paths, max_sizes, bigger_panoramas)
            return

        _im = Image.open(src)

        # The jpg exclusion is Issue #3332
        is_animated = hasattr(_im, 'n_frames') and _im.n_frames > 1 and extension not in {'.jpg', '.jpeg'}

        exif = None
        if "exif" in _im.info:
            exif = piexif.load(_im.info["exif"])
            # Rotate according to EXIF
            if "0th" in exif:
                value = exif['0th'].get(piexif.ImageIFD.Orientation, 1)
                if value in (3, 4):
                    _im = _im.transpose(Image.ROTATE_180)
                elif value in (5, 6):
                    _im = _im.transpose(Image.ROTATE_270)
                elif value in (7, 8):
                    _im = _im.transpose(Image.ROTATE_90)
                if value in (2, 4, 5, 7):
                    _im = _im.transpose(Image.FLIP_LEFT_RIGHT)
                exif['0th'][piexif.ImageIFD.Orientation] = 1
            exif = self.filter_exif(exif, exif_whitelist)

        icc_profile = _im.info.get('icc_profile') if preserve_icc_profiles else None

        for dst, max_size in zip(dst_paths, max_sizes):
            if is_animated:  # Animated gif, leave as-is
                utils.copy_file(src, dst)
                continue

            im = _im.copy()

            size = w, h = im.size
            if w > max_size or h > max_size:
                size = max_size, max_size
                # Panoramas get larger thumbnails because they look *awful*
                if bigger_panoramas and w > 3 * h:
                    size = min(w, max_size * 4), min(w, max_size * 4)
            try:
                im.thumbnail(size, Image.Resampling.LANCZOS)
                save_args = {}
                if icc_profile:
                    save_args['icc_profile'] = icc_profile

                if exif is not None and preserve_exif_data:
                    # Put right size in EXIF data
                    w, h = im.size
                    if '0th' in exif:
                        exif["0th"][piexif.ImageIFD.ImageWidth] = w
                        exif["0th"][piexif.ImageIFD.ImageLength] = h
                    if 'Exif' in exif:
                        exif["Exif"][piexif.ExifIFD.PixelXDimension] = w
                        exif["Exif"][piexif.ExifIFD.PixelYDimension] = h
                    # Filter EXIF data as required
                    save_args['exif'] = piexif.dump(exif)

                im.save(dst, **save_args)
            except Exception as e:
                self.logger.warning("Can't process {0}, using original "
                                    "image! ({1})".format(src, e))
                utils.copy_file(src, dst)

    def resize_svg(self, src, dst_paths, max_sizes, bigger_panoramas):
        """Make a copy of an svg at the requested sizes."""
        # Resize svg based on viewport hacking.
        # note that this can also lead to enlarged svgs
        if src.endswith('.svgz'):
            with gzip.GzipFile(src, 'rb') as op:
                xml = op.read()
        else:
            with open(src, 'rb') as op:
                xml = op.read()

        for dst, max_size in zip(dst_paths, max_sizes):
            try:
                tree = lxml.etree.XML(xml)
                width = tree.attrib['width']
                height = tree.attrib['height']
                w = int(re.search("[0-9]+", width).group(0))
                h = int(re.search("[0-9]+", height).group(0))
                # calculate new size preserving aspect ratio.
                ratio = float(w) / h
                # Panoramas get larger thumbnails because they look *awful*
                if bigger_panoramas and w > 3 * h:
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
                    op = gzip.GzipFile(dst, 'wb')
                else:
                    op = open(dst, 'wb')
                op.write(lxml.etree.tostring(tree))
                op.close()
            except (KeyError, AttributeError) as e:
                self.logger.warning("No width/height in %s. Original exception: %s" % (src, e))
                utils.copy_file(src, dst)

    def image_date(self, src):
        """Try to figure out the date of the image."""
        if src not in self.dates:
            try:
                im = Image.open(src)
                exif = im._getexif()
                im.close()
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
