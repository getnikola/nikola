Nikola, a Static Site and Blog Generator
========================================

In goes content, out comes a website, ready to deploy.

[![Build Status](https://travis-ci.org/ralsina/nikola.png)](https://travis-ci.org/ralsina/nikola)

Why Static Websites?
--------------------

Static websites are safer, use fewer resources, and avoid vendor and platform lock-in.
You can read more about this in the [Nikola Handbook.](http://nikola.ralsina.com.ar/handbook.html#why-static)

What Can Nikola Do?
-------------------

It has many features, but here are some of the nicer ones:

* [Blogs, with tags, feeds, archives, comments, etc.](http://nikola.ralsina.com.ar/some-sites-using-nikola.html)
* [Themable](http://themes.nikola.ralsina.com.ar)
* Fast builds, thanks to [doit](http://python-doit.sf.net)
* Flexible, extensible via plugins
* Small codebase (programmers can understand all of Nikola core in a day)
* [reStructuredText](http://nikola.ralsina.com.ar/quickstart.html) or Markdown as input language (also Wiki, BBCode, Textile, and HTML)
* Easy `image galleries </galleries/demo/>`_ (just drop files in a folder!)
* Syntax highlighting for almost any programming language or markup
* Multilingual sites, [translated to 13 languages.](https://www.transifex.com/projects/p/nikola/)
* Doesn't reinvent wheels, leverages existing tools.
* Python 2 and 3 compatible.

Installation Instructions
-------------------------

Assuming you have pip installed::

    git clone git://github.com/ralsina/nikola.git
    cd nikola
    pip install .

Optionally (for markdown and lots of other features):

    pip install -r requirements.txt

For more information, see http://nikola.ralsina.com.ar
