# -*- coding: utf-8 -*-
# As prescribed in README.rst:
import os
import tempfile
from PIL import Image, ImageDraw

from nikola.plugins.task import scale_images

from .base import FakeSite
import pytest

# These tests don't require valid profiles. They need only to verify
# that profile data is/isn't saved with images.
# It would be nice to use PIL.ImageCms to create valid profiles, but
# in many Pillow distributions ImageCms is a stub.
# ICC file data format specification:
# http://www.color.org/icc32.pdf
PROFILE = b'invalid profile data'


def test_scale_discarding_icc_profile(test_images, destination_dir):
    filename, expected_profile = test_images

    pathname = os.path.join(destination_dir, filename)
    assert os.path.exists(pathname), pathname

    img = Image.open(pathname)
    actual_profile = img.info.get('icc_profile')
    assert actual_profile == expected_profile


@pytest.fixture(params=[True, False], ids=["with icc filename", "without icc filename"])
def test_images(request, preserve_icc_profiles, source_dir, destination_dir):
    image_filename = create_src_image(source_dir, request.param)
    _run_task(preserve_icc_profiles, str(source_dir), str(destination_dir))

    if request.param:
        yield image_filename, PROFILE if preserve_icc_profiles else None
    else:
        yield image_filename, None


@pytest.fixture(params=[True, False], ids=["profiles preserved", "profiles not preserved"])
def preserve_icc_profiles(request):
    return request.param


@pytest.fixture
def source_dir(tmpdir_factory):
    return tmpdir_factory.mktemp('image_source')


@pytest.fixture
def destination_dir(tmpdir_factory):
    return tmpdir_factory.mktemp('image_output')


def _run_task(preserve_icc_profiles, image_folder, output_folder):
    task_instance = _get_task_instance(preserve_icc_profiles, image_folder, output_folder)
    for task in task_instance.gen_tasks():
        for action, args in task.get('actions', []):
            action(*args)


def _get_task_instance(preserve_icc_profiles, image_folder, output_folder):
    result = scale_images.ScaleImage()
    result.set_site(_get_site(preserve_icc_profiles, image_folder, output_folder))
    return result


def _get_site(preserve_icc_profiles, image_folder, output_folder):
    site = FakeSite()
    site.config['IMAGE_FOLDERS'] = {image_folder: ''}
    site.config['OUTPUT_FOLDER'] = output_folder
    site.config['IMAGE_THUMBNAIL_SIZE'] = 128
    site.config['IMAGE_THUMBNAIL_FORMAT'] = '{name}.thumbnail{ext}'
    site.config['MAX_IMAGE_SIZE'] = 512
    site.config['FILTERS'] = {}
    site.config['PRESERVE_EXIF_DATA'] = False
    site.config['EXIF_WHITELIST'] = {}
    site.config['PRESERVE_ICC_PROFILES'] = preserve_icc_profiles
    return site


def create_src_image(testdir, use_icc_profile):
    img = create_test_image()
    pathname = tmp_img_name(testdir)

    # Test two variants: with and without an associated icc_profile
    if use_icc_profile:
        img.save(pathname, icc_profile=PROFILE)
    else:
        img.save(pathname)

    return os.path.basename(pathname)


def create_test_image():
    # Make a white image with a red stripe on the diagonal.
    width = 64
    height = 64
    img = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.line((0, 0, width, height), fill=(255, 128, 128))
    draw.line((width, 0, 0, height), fill=(128, 128, 255))
    return img


def tmp_img_name(dirname):
    pathname = tempfile.NamedTemporaryFile(
        suffix=".jpg", dir=dirname, delete=False)
    return pathname.name
