import io
import os
import shutil

from ..helper import cd

__all__ = ["add_post_without_text", "append_config", "cd", "create_simple_post", "patch_config"]


def add_post_without_text(directory):
    """Add a post without text."""
    # File for Issue #374 (empty post text)
    create_simple_post(directory, "empty.txt", "foobar")


def create_simple_post(directory, filename, title_slug, text='', date='2013-03-06 19:08:15'):
    """Create a simple post in a given directory."""
    path = os.path.join(directory, filename)
    text_processed = '\n' + text if text else ''
    with io.open(path, "w+", encoding="utf8") as outf:
        outf.write(
            """
.. title: {0}
.. slug: {0}
.. date: {1}
{2}""".format(title_slug, date, text_processed)
        )


def copy_example_post(destination_dir):
    """Copy a modified version of the example post into the site."""
    test_dir = os.path.abspath(os.path.dirname(__file__))
    source_file = os.path.join(test_dir, "..", "data", "1-nolinks.rst")
    destination = os.path.join(destination_dir, "1.rst")
    shutil.copy(source_file, destination)


def append_config(config_dir, appendix):
    """Append text to the config file."""
    config_path = os.path.join(config_dir, "conf.py")
    with io.open(config_path, "a", encoding="utf8") as outf:
        outf.write(appendix)


def patch_config(config_dir, *replacements):
    """Patch the config file with new values (find and replace)."""
    config_path = os.path.join(config_dir, "conf.py")
    with io.open(config_path, "r", encoding="utf-8") as inf:
        data = inf.read()

    for old, new in replacements:
        data = data.replace(old, new)

    with io.open(config_path, "w+", encoding="utf8") as outf:
        outf.write(data)
        outf.flush()
