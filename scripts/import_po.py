#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Download translations from transifex and regenerate files."""

from __future__ import unicode_literals, print_function
import io
from glob import glob
import os
import sys
import polib

if 'nopull' not in sys.argv:
    os.system("tx pull -a")

trans_files = glob(os.path.join('translations', 'nikola.messages', '*.po'))
for fname in trans_files:
    lang = os.path.splitext(os.path.basename(fname))[0].lower()
    lang = lang.replace('@', '_')
    outf = os.path.join('nikola', 'data', 'themes', 'base',
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
    with io.open(outf, "w+", encoding="utf8") as outfile:
        outfile.write('\n'.join(lines))
