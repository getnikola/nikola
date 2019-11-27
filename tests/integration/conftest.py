import os
import sys

import pytest

from nikola.utils import LocaleBorg

from ..conftest import ensure_chdir  # NOQA - autouse fixture


@pytest.fixture(scope="session")
def default_locale():
    return os.environ.get('NIKOLA_LOCALE_DEFAULT', 'en')


@pytest.fixture(scope="session")
def other_locale():
    return os.environ.get('NIKOLA_LOCALE_OTHER', 'pl')


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
def localeborg_setup(default_locale):
    """
    Reset the LocaleBorg before and after every test.
    """
    LocaleBorg.reset()
    LocaleBorg.initialize({}, default_locale)
    try:
        yield
    finally:
        LocaleBorg.reset()
