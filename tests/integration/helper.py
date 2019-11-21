"""Test that a default build of --demo works."""

import os
import sys

import pytest

from nikola.utils import LocaleBorg

LOCALE_DEFAULT = os.environ.get('NIKOLA_LOCALE_DEFAULT', 'en')
LOCALE_OTHER = os.environ.get('NIKOLA_LOCALE_OTHER', 'pl')


@pytest.fixture
def output_dir(target_dir):
    return os.path.join(target_dir, "output")


@pytest.fixture
def target_dir(tmpdir):
    tdir = os.path.join(str(tmpdir), 'target')
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
