"""Make sure posts only in secondary languages work."""

import os
import shutil
import sys

import pytest

import nikola.plugins.command.init
from nikola.utils import LocaleBorg
from nikola import __main__

from ..base import cd

LOCALE_DEFAULT = os.environ.get('NIKOLA_LOCALE_DEFAULT', 'en')
LOCALE_OTHER = os.environ.get('NIKOLA_LOCALE_OTHER', 'pl')


def test_archive_exists(build, output_dir):
    """Ensure the build did something."""
    index_path = os.path.join(output_dir, "archive.html")
    assert os.path.isfile(index_path)


@pytest.fixture
def build(target_dir):
    """Build the site."""
    init_command = nikola.plugins.command.init.CommandInit()
    init_command.create_empty_site(target_dir)
    init_command.create_configuration(target_dir)

    src = os.path.join(os.path.dirname(__file__),
                       '..', 'data', 'translated_titles')
    for root, dirs, files in os.walk(src):
        for src_name in files:
            if src_name == '1.txt':  # English post
                continue

            rel_dir = os.path.relpath(root, src)
            dst_file = os.path.join(target_dir, rel_dir, src_name)
            src_file = os.path.join(root, src_name)
            shutil.copy2(src_file, dst_file)

    with cd(target_dir):
        __main__.main(["build"])


@pytest.fixture
def output_dir(target_dir):
    return os.path.join(target_dir, "output")


@pytest.fixture
def target_dir(tmpdir):
    tdir = os.path.join(str(tmpdir), 'target')
    os.mkdir(tdir)
    yield tdir


@pytest.fixture(autouse=True)
def fixIssue438():
    try:
        yield
    finally:
        try:
            del sys.modules['conf']
        except KeyError:
            pass


@pytest.fixture(autouse=True)
def localeborg_setup():
    """
    Reset the LocaleBorg before and after every test.
    """
    LocaleBorg.reset()
    LocaleBorg.initialize({}, LOCALE_DEFAULT)
    try:
        yield
    finally:
        LocaleBorg.reset()
