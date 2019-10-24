import os
import pytest


@pytest.fixture(autouse=True)
def ensure_chdir():
    old_dir = os.getcwd()
    try:
        yield
    finally:
        os.chdir(old_dir)


@pytest.fixture
def test_dir():
    return os.path.abspath(os.path.dirname(__file__))
