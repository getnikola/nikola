"""Implementation of compile_html based on markdown."""

__all__ = ['compile_html']

import codecs
import re

from markdown import markdown


def compile_html(source, dest):
    try:
        os.makedirs(os.path.dirname(dest))
    except:
        pass
    with codecs.open(dest, "w+", "utf8") as out_file:
        with codecs.open(source, "r", "utf8") as in_file:
            data = in_file.read()

        output = markdown(data, ['fenced_code', 'codehilite'])
        # remove the H1 because there is "title" h1.
        output = re.sub(r'<h1>.*</h1>', '', output)
        # python-markdown's highlighter uses the class 'codehilite' to wrap code,
        # instead of the standard 'code'. None of the standard pygments
        # stylesheets use this class, so swap it to be 'code'
        output = re.sub(r'(<div[^>]+class="[^"]*)codehilite([^>]+)', r'\1code\2',
                        output)
        out_file.write(output)
