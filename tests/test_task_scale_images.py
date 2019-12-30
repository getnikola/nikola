import os
from tempfile import NamedTemporaryFile

import pytest
from PIL import Image, ImageDraw

from nikola.plugins.task import scale_images

# These tests don't require valid profiles. They need only to verify
# that profile data is/isn't saved with images.
# It would be nice to use PIL.ImageCms to create valid profiles, but
# in many Pillow distributions ImageCms is a stub.
# ICC file data format specification:
# http://www.color.org/icc32.pdf
PROFILE = b"invalid profile data"


def test_handling_icc_profiles(test_images, destination_dir):
    filename, expected_profile = test_images

    pathname = os.path.join(str(destination_dir), filename)
    assert os.path.exists(pathname), pathname

    img = Image.open(pathname)
    actual_profile = img.info.get("icc_profile")
    assert actual_profile == expected_profile


@pytest.fixture(
    params=[
        pytest.param(True, id="with icc filename"),
        pytest.param(False, id="without icc filename"),
    ]
)
def test_images(request, preserve_icc_profiles, source_dir, site):
    image_filename = create_src_image(str(source_dir), request.param)
    run_task(site)

    if request.param:
        yield image_filename, PROFILE if preserve_icc_profiles else None
    else:
        yield image_filename, None


@pytest.fixture(
    params=[
        pytest.param(True, id="profiles preserved"),
        pytest.param(False, id="profiles not preserved"),
    ]
)
def preserve_icc_profiles(request):
    return request.param


@pytest.fixture
def source_dir(tmpdir_factory):
    return tmpdir_factory.mktemp("image_source")


@pytest.fixture
def site(preserve_icc_profiles, source_dir, destination_dir):
    config = {
        "IMAGE_FOLDERS": {str(source_dir): ""},
        "OUTPUT_FOLDER": str(destination_dir),
        "IMAGE_THUMBNAIL_SIZE": 128,
        "IMAGE_THUMBNAIL_FORMAT": "{name}.thumbnail{ext}",
        "MAX_IMAGE_SIZE": 512,
        "FILTERS": {},
        "PRESERVE_EXIF_DATA": False,
        "EXIF_WHITELIST": {},
        "PRESERVE_ICC_PROFILES": preserve_icc_profiles,
    }
    return FakeSite(config)


class FakeSite:
    def __init__(self, config):
        self.config = config
        self.debug = True


@pytest.fixture
def destination_dir(tmpdir_factory):
    return tmpdir_factory.mktemp("image_output")


def run_task(site):
    task_instance = get_task_instance(site)
    for task in task_instance.gen_tasks():
        for action, args in task.get("actions", []):
            action(*args)


def get_task_instance(site):
    result = scale_images.ScaleImage()
    result.set_site(site)
    return result


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
    pathname = NamedTemporaryFile(suffix=".jpg", dir=dirname, delete=False)
    return pathname.name
