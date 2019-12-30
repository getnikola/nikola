import io
import os
import shutil

from ..helper import cd

__all__ = ["add_post_without_text", "append_config", "cd", "patch_config"]


def add_post_without_text(directory):
    # File for Issue #374 (empty post text)
    path = os.path.join(directory, "empty.txt")
    with io.open(path, "w+", encoding="utf8") as outf:
        outf.write(
            """
.. title: foobar
.. slug: foobar
.. date: 2013-03-06 19:08:15
"""
        )


def copy_example_post(destination_dir):
    test_dir = os.path.abspath(os.path.dirname(__file__))
    source_file = os.path.join(test_dir, "..", "data", "1-nolinks.rst")
    destination = os.path.join(destination_dir, "1.rst")
    shutil.copy(source_file, destination)


def append_config(config_dir, appendix):
    config_path = os.path.join(config_dir, "conf.py")
    with io.open(config_path, "a", encoding="utf8") as outf:
        outf.write(appendix)


def patch_config(config_dir, *replacements):
    config_path = os.path.join(config_dir, "conf.py")
    with io.open(config_path, "r", encoding="utf-8") as inf:
        data = inf.read()

    for old, new in replacements:
        data = data.replace(old, new)

    with io.open(config_path, "w+", encoding="utf8") as outf:
        outf.write(data)
        outf.flush()
