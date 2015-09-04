#!/usr/bin/env python

from nikola import nikola
n=nikola.Nikola()
n.init_plugins()

print """.. title: Path Handlers for Nikola
.. slug: path-handlers
.. tags: mathjax
.. author: The Nikola Team

Nikola supports special links with the syntax ``link://kind/name``. Here is
the description for all the supported kinds.

"""

for k, v in n.path_handlers.items():
    print k
    print '\n'.join('    '+l.strip() for l in v.__doc__.splitlines())
    print
