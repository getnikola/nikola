import os
import pytest


@pytest.yield_fixture(autouse=True)
def ensure_chdir():
    x = os.getcwd()
    yield
    os.chdir(x)
