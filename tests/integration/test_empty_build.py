import os
import sys

import pytest

import nikola
import nikola.plugins.command
import nikola.plugins.command.init
import nikola.utils
from nikola import __main__
from nikola.utils import LocaleBorg

from ..base import cd

LOCALE_DEFAULT = os.environ.get('NIKOLA_LOCALE_DEFAULT', 'en')


def test_build(build, target_dir):
    """Ensure the build did something."""
    index_path = os.path.join(target_dir, "output", "archive.html")
    assert os.path.isfile(index_path)


@pytest.fixture
def build(target_dir, fill_site):
    """Build the site."""
    with cd(target_dir):
        __main__.main(["build"])


@pytest.fixture
def target_dir(tmpdir):
    tdir = os.path.join(str(tmpdir), 'target')
    os.mkdir(tdir)
    yield tdir


@pytest.fixture
def fill_site(init_command, target_dir):
    """Add any needed initial content."""
    init_command.create_empty_site(target_dir)
    init_command.create_configuration(target_dir)


@pytest.fixture
def init_command():
    return nikola.plugins.command.init.CommandInit()


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


