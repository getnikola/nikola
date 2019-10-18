import os
import pytest


@pytest.fixture(autouse=True)
def ensure_chdir():
    x = os.getcwd()
    yield
    os.chdir(x)
