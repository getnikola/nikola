How To make This Work
---------------------

The full manual is in stories/manual.txt, but here is the very short version:

1. Install docutils (http://docutils.sourceforge.net)
2. Install Mako (http://makotemplates.org)
3. Install doit (http://python-doit.sourceforge.net)
4. Install PIL (http://www.pythonware.com/products/pil/)
5. Install Pygments (http://pygments.org/)

To build or update the demo site run this command in the nikola's folder::

    doit

To see it::

    doit serve -p 8000

And point your browser to http://localhost:8000

Notes on Requirements
---------------------

If you don't have PIL, then image galleries will be inefficient because Nikola
will not generate thumbnails. Alternatively, you may install pillow instead of
PIL.

If you don't have pygments, the code-block directive will not highlight syntax.
