import os
import pytest


@pytest.fixture(autouse=True)
def ensure_chdir():
    old_dir = os.getcwd()
    try:
        yield
    finally:
        os.chdir(old_dir)
