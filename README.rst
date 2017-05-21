Nikola, a Static Site and Blog Generator
========================================

In goes content, out comes a website, ready to deploy.

.. image:: http://img.shields.io/pypi/v/Nikola.svg
   :target: https://pypi.python.org/pypi/Nikola

.. image:: https://img.shields.io/requires/github/getnikola/nikola.svg
   :target: https://requires.io/github/getnikola/nikola/requirements/?branch=master

.. image:: http://img.shields.io/travis/getnikola/nikola.svg
   :target: https://travis-ci.org/getnikola/nikola

.. image:: http://img.shields.io/coveralls/getnikola/nikola.png
  :target: https://coveralls.io/r/getnikola/nikola?branch=master

.. image:: http://img.shields.io/badge/license-MIT-green.svg
   :target: https://github.com/getnikola/nikola/blob/master/LICENSE.txt

.. image:: https://build.snapcraft.io/badge/getnikola/nikola.svg
   :target: https://build.snapcraft.io/user/getnikola/nikola

Why Static Websites?
--------------------

Static websites are safer, use fewer resources, and avoid vendor and platform lock-in.
You can read more about this in the `Nikola Handbook`_


What Can Nikola Do?
-------------------

It has many features, but here are some of the nicer ones:

* `Blogs, with tags, feeds, archives, comments, etc.`__
* `Themable`_
* Fast builds, thanks to `doit`_
* Flexible, extensible via the dozens of `available plugins`_
* Small codebase (programmers can understand all of Nikola core in a day)
* `reStructuredText`_ or Markdown as input language (also Wiki, BBCode, Textile, and HTML)
* Easy `image galleries`_ (just drop files in a folder!)
* Syntax highlighting for almost any programming language or markup
* Multilingual sites, `translated to 50 languages.`__
* Doesn't reinvent wheels, leverages existing tools.
* Python 2.7, 3.3, 3.4, 3.5 and 3.6 compatible.

.. _Nikola Handbook: https://getnikola.com/handbook.html#why-static
__ https://users.getnikola.com/
.. _Themable: https://themes.getnikola.com
.. _doit: http://pydoit.org
.. _available plugins: https://plugins.getnikola.com/
.. _reStructuredText: https://getnikola.com/quickstart.html
.. _image galleries: https://getnikola.com/galleries/demo/
__ https://www.transifex.com/projects/p/nikola/

Nikola Architecture
-------------------

.. image:: https://getnikola.com/images/architecture.png

Installation Instructions
-------------------------

Assuming you have pip installed::

    pip install Nikola

For optional features::

    pip install "Nikola[extras]"

For tests (see tests/README.rst for more details)::

    pip install "Nikola[extras,tests]"

For more information, see https://getnikola.com/
