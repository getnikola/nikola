#!/usr/bin/env python
"""Download translations from transifex and regenerate files."""

from __future__ import unicode_literals, print_function
import codecs
from glob import glob
import os

import polib

os.system("tx pull -a")
trans_files = glob(os.path.join('translations', 'nikola.messages', '*.po'))
for fname in trans_files:
    lang = os.path.splitext(os.path.basename(fname))[0].lower()
    outf = os.path.join('nikola', 'data', 'themes', 'default',
                        'messages', 'messages_{0}.py'.format(lang))
    po = polib.pofile(fname)
    lines = """# -*- encoding:utf-8 -*-
from __future__ import unicode_literals

MESSAGES = {""".splitlines()
    lines2 = []
    for entry in po:
        lines2.append('    "{0}": "{1}",'. format(entry.msgid, entry.msgstr))
    lines.extend(sorted(lines2))
    lines.append("}\n")
    print("Generating:", outf)
    with codecs.open(outf, "wb+", "utf8") as outfile:
        outfile.write('\n'.join(lines))
