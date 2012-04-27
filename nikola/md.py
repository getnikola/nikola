"""Implementation of compile_html based on markdown."""

__all__ = ['compile_html']

import codecs

from markdown import markdown


def compile_html(source, dest):
    with codecs.open(source, "r", "utf8") as in_file:
        data = in_file.read()
        output = markdown(data)
    with codecs.open(dest, "w+", "utf8") as out_file:
        out_file.write(output)
