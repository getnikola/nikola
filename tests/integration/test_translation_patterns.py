"""Check that the path.lang.ext TRANSLATIONS_PATTERN works too"""

import io
import os
import shutil
import sys

import lxml.html
import pytest

import nikola.plugins.command.init
from nikola.utils import LocaleBorg
from nikola import __main__

from ..base import cd

LOCALE_DEFAULT = os.environ.get('NIKOLA_LOCALE_DEFAULT', 'en')
LOCALE_OTHER = os.environ.get('NIKOLA_LOCALE_OTHER', 'pl')


def test_translated_titles(build, output_dir):
    """Check that translated title is picked up."""
    en_file = os.path.join(output_dir, "pages", "1", "index.html")
    pl_file = os.path.join(output_dir, LOCALE_OTHER, "pages", "1", "index.html")

    # Files should be created
    assert os.path.isfile(en_file)
    assert os.path.isfile(pl_file)

    # And now let's check the titles
    with io.open(en_file, 'r', encoding='utf8') as inf:
        doc = lxml.html.parse(inf)
        assert doc.find('//title').text == 'Foo | Demo Site'

    with io.open(pl_file, 'r', encoding='utf8') as inf:
        doc = lxml.html.parse(inf)
        assert doc.find('//title').text == 'Bar | Demo Site'


def test_archive_exists(build, output_dir):
    """Ensure the build did something."""
    index_path = os.path.join(output_dir, "archive.html")
    assert os.path.isfile(index_path)


@pytest.fixture
def build(target_dir):
    """
    Build the site.

    Set the TRANSLATIONS_PATTERN to the old v6 default.
    """
    init_command = nikola.plugins.command.init.CommandInit()
    init_command.create_empty_site(target_dir)
    init_command.create_configuration(target_dir)

    src = os.path.join(os.path.dirname(__file__),
                       '..', 'data', 'translated_titles')
    for root, dirs, files in os.walk(src):
        for src_name in files:
            rel_dir = os.path.relpath(root, src)
            dst_file = os.path.join(target_dir, rel_dir, src_name)
            src_file = os.path.join(root, src_name)
            shutil.copy2(src_file, dst_file)

    os.rename(os.path.join(target_dir, "pages", "1.%s.txt" % LOCALE_OTHER),
              os.path.join(target_dir, "pages", "1.txt.%s" % LOCALE_OTHER))

    conf_path = os.path.join(target_dir, "conf.py")
    with io.open(conf_path, "r", encoding="utf-8") as inf:
        data = inf.read()
        data = data.replace('TRANSLATIONS_PATTERN = "{path}.{lang}.{ext}"',
                            'TRANSLATIONS_PATTERN = "{path}.{ext}.{lang}"')
    with io.open(conf_path, "w+", encoding="utf8") as outf:
        outf.write(data)

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
