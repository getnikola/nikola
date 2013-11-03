Nikola, a Static Site and Blog Generator
========================================

In goes content, out comes a website, ready to deploy.

.. image:: https://travis-ci.org/getnikola/nikola.png
   :target: https://travis-ci.org/getnikola/nikola

.. image:: https://pypip.in/v/Nikola/badge.png
        :target: https://crate.io/packages/Nikola

.. image:: https://pypip.in/d/Nikola/badge.png
        :target: https://crate.io/packages/Nikola

.. image:: https://coveralls.io/repos/getnikola/nikola/badge.png?branch=master
  :target: https://coveralls.io/r/getnikola/nikola?branch=master


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
* Flexible, extensible via plugins
* Small codebase (programmers can understand all of Nikola core in a day)
* `reStructuredText`_ or Markdown as input language (also Wiki, BBCode, Textile, and HTML)
* Easy `image galleries`_ (just drop files in a folder!)
* Syntax highlighting for almost any programming language or markup
* Multilingual sites, `translated to 18 languages.`__
* Doesn't reinvent wheels, leverages existing tools.
* Python 2.6, 2.7 and 3.3 compatible.

.. _Nikola Handbook: http://getnikola.com/handbook.html#why-static
__ http://users.getnikola.com/
.. _Themable: http://themes.getnikola.com
.. _doit: http://pydoit.org
.. _reStructuredText: http://getnikola.com/quickstart.html
.. _image galleries: http://getnikola.com/galleries/demo/
__ https://www.transifex.com/projects/p/nikola/

Installation Instructions
-------------------------

Assuming you have pip installed::

    git clone git://github.com/getnikola/nikola.git
    cd nikola
    pip install .

For optional features::

    pip install -r requirements-full.txt
    
For tests (see tests/README.rst for more details)::

    pip install -r requirements-tests.txt

For more information, see http://getnikola.com/
