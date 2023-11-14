import os

from .helper import cd


class SomeTestError(Exception):
    """An arbitrary error to be thrown by the test."""
    pass


def test_test_helper():
    """Check that the cd test helper duly resets the directory even in spite of an error."""
    old_dir = os.getcwd()
    exception_seen = False
    try:
        with cd(".."):
            raise SomeTestError("Just raising an exception, as failing tests sometimes do.")
    except SomeTestError:
        now_dir = os.getcwd()
        assert old_dir == now_dir
        exception_seen = True
    assert exception_seen
