import os
import pytest


@pytest.fixture(autouse=True)
def ensure_chdir():
    old_dir = os.getcwd()
    try:
        yield
    finally:
        os.chdir(old_dir)


@pytest.fixture(scope="module")
def test_dir():
    """
    Absolute path to the directory with the tests.
    """
    return os.path.abspath(os.path.dirname(__file__))


@pytest.fixture(scope="session")
def default_locale() -> str:
    return os.environ.get("NIKOLA_LOCALE_DEFAULT", "en")
