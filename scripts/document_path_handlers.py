#!/usr/bin/env python

from __future__ import print_function, unicode_literals
from nikola import nikola
n = nikola.Nikola()
n.init_plugins()

print(""".. title: Path Handlers for Nikola
.. slug: path-handlers
.. author: The Nikola Team

Nikola supports special links with the syntax ``link://kind/name``. In the templates you can also use ``_link(kind, name)``.
You can also add query strings (``?key=value``) for extra arguments, or pass keyword arguments to ``_link`` in templates (support and behavior depends on path handlers themselves)

Here are the descriptions for all the supported kinds.

.. class:: dl-horizontal
""")

for k in sorted(n.path_handlers.keys()):
    v = n.path_handlers[k]
    print(k)
    print('\n'.join('    ' + l.strip() for l in v.__doc__.splitlines()))
    print()
