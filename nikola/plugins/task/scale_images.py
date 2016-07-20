# -*- coding: utf-8 -*-

# Copyright © 2014-2016 Pelle Nilsson and others.

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

"""Resize images and create thumbnails for them."""

import os

from nikola.plugin_categories import Task
from nikola.image_processing import ImageProcessor
from nikola import utils


class ScaleImage(Task, ImageProcessor):
    """Resize images and create thumbnails for them."""

    name = "scale_images"

    def set_site(self, site):
        """Set Nikola site."""
        self.logger = utils.get_logger('scale_images', utils.STDERR_HANDLER)
        return super(ScaleImage, self).set_site(site)

    def process_tree(self, src, dst):
        """Process all images in a src tree and put the (possibly) rescaled images in the dst folder."""
        ignore = set(['.svn'])
        base_len = len(src.split(os.sep))
        for root, dirs, files in os.walk(src, followlinks=True):
            root_parts = root.split(os.sep)
            if set(root_parts) & ignore:
                continue
            dst_dir = os.path.join(dst, *root_parts[base_len:])
            utils.makedirs(dst_dir)
            for src_name in files:
                if src_name in ('.DS_Store', 'Thumbs.db'):
                    continue
                if (not src_name.lower().endswith(tuple(self.image_ext_list)) and not src_name.upper().endswith(tuple(self.image_ext_list))):
                    continue
                dst_file = os.path.join(dst_dir, src_name)
                src_file = os.path.join(root, src_name)
                thumb_file = '.thumbnail'.join(os.path.splitext(dst_file))
                yield {
                    'name': dst_file,
                    'file_dep': [src_file],
                    'targets': [dst_file, thumb_file],
                    'actions': [(self.process_image, (src_file, dst_file, thumb_file))],
                    'clean': True,
                }

    def process_image(self, src, dst, thumb):
        """Resize an image."""
        self.resize_image(src, dst, self.kw['max_image_size'], False, preserve_exif_data=self.kw['preserve_exif_data'], exif_whitelist=self.kw['exif_whitelist'])
        self.resize_image(src, thumb, self.kw['image_thumbnail_size'], False, preserve_exif_data=self.kw['preserve_exif_data'], exif_whitelist=self.kw['exif_whitelist'])

    def gen_tasks(self):
        """Copy static files into the output folder."""
        self.kw = {
            'image_thumbnail_size': self.site.config['IMAGE_THUMBNAIL_SIZE'],
            'max_image_size': self.site.config['MAX_IMAGE_SIZE'],
            'image_folders': self.site.config['IMAGE_FOLDERS'],
            'output_folder': self.site.config['OUTPUT_FOLDER'],
            'filters': self.site.config['FILTERS'],
            'preserve_exif_data': self.site.config['PRESERVE_EXIF_DATA'],
            'exif_whitelist': self.site.config['EXIF_WHITELIST'],
        }

        self.image_ext_list = self.image_ext_list_builtin
        self.image_ext_list.extend(self.site.config.get('EXTRA_IMAGE_EXTENSIONS', []))

        yield self.group_task()
        for src in self.kw['image_folders']:
            dst = self.kw['output_folder']
            filters = self.kw['filters']
            real_dst = os.path.join(dst, self.kw['image_folders'][src])
            for task in self.process_tree(src, real_dst):
                task['basename'] = self.name
                task['uptodate'] = [utils.config_changed(self.kw)]
                yield utils.apply_filters(task, filters)
