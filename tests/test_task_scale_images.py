# -*- coding: utf-8 -*-
# As prescribed in README.rst:
import os
import unittest
import tempfile
from PIL import Image, ImageDraw

from nikola.plugins.task import scale_images
# Import test - should perhaps be moved to a separate module
import nikola.plugins.task.galleries  # NOQA
from .base import FakeSite


class TestCase(unittest.TestCase):
    def setUp(self):
        # These tests don't require valid profiles.  They need only to verify
        # that profile data is/isn't saved with images.
        # It would be nice to use PIL.ImageCms to create valid profiles, but
        # in many Pillow distributions ImageCms is a stub.
        # ICC file data format specification:
        # http://www.color.org/icc32.pdf

        self._profile = b'invalid profile data'

        # Make a white image with a red stripe on the diagonal.
        w = 64
        h = 64
        img = Image.new("RGB", (w, h), (255, 255, 255))
        draw = ImageDraw.Draw(img)
        draw.line((0, 0, w, h), fill=(255, 128, 128))
        draw.line((w, 0, 0, h), fill=(128, 128, 255))
        self._img = img

        self._src_dir = tempfile.TemporaryDirectory()
        self._dest_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        pass

    def _tmp_img_name(self, dirname):
        pathname = tempfile.NamedTemporaryFile(
            suffix=".jpg", dir=dirname, delete=False)
        return pathname.name

    def _get_site(self, preserve_icc_profiles):
        site = FakeSite()
        site.config['IMAGE_FOLDERS'] = {self._src_dir.name: ''}
        site.config['OUTPUT_FOLDER'] = self._dest_dir.name
        site.config['IMAGE_THUMBNAIL_SIZE'] = 128
        site.config['IMAGE_THUMBNAIL_FORMAT'] = '{name}.thumbnail{ext}'
        site.config['MAX_IMAGE_SIZE'] = 512
        site.config['FILTERS'] = {}
        site.config['PRESERVE_EXIF_DATA'] = False
        site.config['EXIF_WHITELIST'] = {}
        site.config['PRESERVE_ICC_PROFILES'] = preserve_icc_profiles
        return site

    def _get_task_instance(self, preserve_icc_profiles):
        result = scale_images.ScaleImage()
        result.set_site(self._get_site(preserve_icc_profiles))
        return result

    def _create_src_images(self):
        img = self._img
        # Test two variants: with and without an associated icc_profile
        pathname = self._tmp_img_name(self._src_dir.name)
        img.save(pathname)
        sans_icc_filename = os.path.basename(pathname)

        pathname = self._tmp_img_name(self._src_dir.name)
        img.save(pathname, icc_profile=self._profile)
        with_icc_filename = os.path.basename(pathname)
        return [sans_icc_filename, with_icc_filename]

    def _run_task(self, preserve_icc_profiles):
        task_instance = self._get_task_instance(preserve_icc_profiles)
        for task in task_instance.gen_tasks():
            for action, args in task.get('actions', []):
                action(*args)

    def test_scale_preserving_icc_profile(self):
        sans_icc_filename, with_icc_filename = self._create_src_images()
        self._run_task(True)
        cases = [
            (sans_icc_filename, None),
            (with_icc_filename, self._profile),
        ]
        for (filename, expected_profile) in cases:
            pathname = os.path.join(self._dest_dir.name, filename)
            self.assertTrue(os.path.exists(pathname), pathname)
            img = Image.open(pathname)
            actual_profile = img.info.get('icc_profile')
            self.assertEqual(actual_profile, expected_profile)

    def test_scale_discarding_icc_profile(self):
        sans_icc_filename, with_icc_filename = self._create_src_images()
        self._run_task(False)
        cases = [
            (sans_icc_filename, None),
            (with_icc_filename, None),
        ]
        for (filename, expected_profile) in cases:
            pathname = os.path.join(self._dest_dir.name, filename)
            self.assertTrue(os.path.exists(pathname), pathname)
            img = Image.open(pathname)
            actual_profile = img.info.get('icc_profile')
            self.assertEqual(actual_profile, expected_profile)


main = unittest.main

if __name__ == '__main__':
    main()
