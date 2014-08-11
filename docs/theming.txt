.. title: Theming Nikola
.. slug: theming
.. date: 2012-03-13 12:00:00 UTC-03:00
.. tags:
.. link:
.. description:

Theming Nikola
==============

:Version: 7.0.1
:Author: Roberto Alsina <ralsina@netmanagers.com.ar>

.. class:: alert alert-info pull-right

.. contents::

.. class:: lead

This document is a reference about themes. If you want a tutorial, please read
`Creating a Theme <creating-a-theme.html>`_

The Structure
-------------

Themes are located in the ``themes`` folder where Nikola is installed, and in the ``themes`` folder
of your site, one folder per theme. The folder name is the theme name.

A Nikola theme consists of the following folders (they are *all* optional):

assets
    This is where you would put your CSS, Javascript and image files. It will be copied
    into ``output/assets`` when you build the site, and the templates will contain
    references to them.

    The included themes use `Bootstrap <http://twitter.github.com/bootstrap/>`_
    and `Colorbox <http://www.jacklmoore.com/colorbox>`_ so they are in assets,
    along with CSS files for syntax highligting and reStructuredText, and a
    minified copy of jQuery.

    If you want to base your theme on other frameworks (or on no framework at all)
    just remember to put there everything you need for deployment.

templates
    This contains the templates used to generate the pages. While Nikola will use a
    certain set of template names by default, you can add others for specific parts
    of your site.

messages
    Nikola tries to be multilingual. This is where you put the strings for your theme
    so that it can be translated into other languages.

less
    Files to be compiled into CSS using `LESS <http://lesscss.org/>`__

sass
    Files to be compiled into CSS using `Sass <http://sass-lang.com/>`__

This mandatory file:

parent
    A text file that, on its first line, contains the name of the **parent theme**.
    Any resources missing on this theme, will be looked up in the parent theme
    (and then in the grandparent, etc).

    The ``parent`` is so you don't have to create a full theme each time: just create an
    empty theme, set the parent, and add the bits you want modified.

    I recommend this:

    * If your theme uses bootstrap, inherit the ``bootstrap`` theme.
    * If your theme uses bootstrap3, inherit the ``bootstrap3`` theme.
    * If your theme uses Jinja as a template engine, inherit ``base-jinja``
      or ``bootstrap-jinja`` (available at http://themes.nikola.ralsina.com.ar)
    * In any other case, inherit ``base``.

And these optional files:

engine
    A text file which, on the first line, contains the name of the template engine
    this theme needs. Currently supported values are "mako" and "jinja".

bundles
    A text file containing a list of files to be turned into bundles using WebAssets.
    For example::

        assets/css/all.css=bootstrap.css,bootstrap-responsive.css,rst.css,code.css,colorbox.css,custom.css

    This creates a file called "assets/css/all.css" in your output that is the
    combination of all the other file paths, relative to the output file.
    This makes the page much more efficient because it avoids multiple connections to the server,
    at the cost of some extra difficult debugging.

    WebAssets supports bundling CSS and JS files.

    Templates should use either the bundle or the individual files based on the ``use_bundles``
    variable, which in turn is set by the ``USE_BUNDLES`` option.

Templates
---------

In templates there is a number of files whose name ends in ``.tmpl``. Those are the
theme's page templates. They are done using the `Mako <http://makotemplates.org>`_
or `Jinja2 <http://jinja.pocoo.org>`_ template languages. If you want to do a theme, you
should learn one first. What engine is used by the theme is declared in the ``engine`` file.

The rest of this document explains Mako templates, but Jinja2 is fairly similar.

Mako has a nifty concept of template inheritance. That means that, a
template can inherit from another and only change small bits of the output. For example,
``base.tmpl`` defines the whole layout for a page but has only a placeholder for content
so ``post.tmpl`` only define the content, and the layout is inherited from ``base.tmpl``.

These are the templates that come with the included themes:

``base.tmpl``
    This template defines the basic page layout for the site. It's mostly plain HTML
    but defines a few blocks that can be re-defined by inheriting templates.

    It has some separate pieces defined in ``base_helper.tmpl`` so they can be
    easily overriden. For example, the Bootstrap theme adds a ``bootstrap_helper.tmpl``
    and then uses it to override things defined in base theme's ``base_helper.tmpl``

``index.tmpl``
    Template used to render the multipost indexes. The posts are in a ``posts`` variable.
    Some functionality is in the ``index_helper.tmpl`` helper template.

``comments_helper.tmpl``
    This template handles comments. You should probably never touch it :-)
    It uses a bunch of helper templates, one for each supported comment system:
    ``disqus_helper.tmpl`` ``facebook_helper.tmpl`` ``googleplus_helper.tmpl``
    ``intensedebate_helper.tmpl`` ``isso_helper.tmpl`` ``livefyre_helper.tmpl``
    ``moot_helper.tmpl``

``crumbs.tmpl`` ``slides.tmpl``
    These templates help render specific UI items, and can be tweaked as needed.

``gallery.tmpl``
    Template used for image galleries. Interesting data includes:

    * ``text``: A descriptive text for the gallery.
    * ``crumbs``: A list of ``link, crumb`` to implement a crumbbar.
    * ``folders``: A list of folders to implement hierarchical gallery navigation.
    * ``enable_comments``: To enable/disable comments in galleries.
    * ``thumbnail_size``: The ``THUMBNAIL_SIZE`` option.
    * ``photo_array``: a list of dictionaries, each containing:

      + ``url``: URL for the full-sized image.
      + ``url_thumb``: URL for the thumbnail.
      + ``title``: The title of the image.
      + ``size``: A dict containing ``w`` and ``h``, the real size of the thumbnail.

   * ``photo_array_json``: a JSON dump of photo_array, used in the bootstrap theme by flowr.js

``list.tmpl``
    Template used to display generic lists of links, which it gets in ``items``,
    a list of (text, link) elements.

``list_post.tmpl``
    Template used to display generic lists of posts, which it gets in ``posts``.

``post.tmpl``
    Template used by default for blog posts, gets the data in a ``post`` object
    which is an instance of the Post class. Some functionality is in the
    ``post_helper.tmpl`` template.

``story.tmpl``
    Used for pages that are not part of a blog, usually a cleaner, less
    intrusive layout than ``post.tmpl``, but same parameters.

``listing.tmpl``
    Used to display code listings.

``tags.tmpl``
    Used to display the list of tags and categories. ``tag.tmpl`` is used to show the contents
    of a single tag or category.

``tagindex.tmpl``
    Used to display tag indexes, if ``TAG_PAGES_ARE_INDEXES`` is True.
    By default, it just inherits ``index.tmpl``.

You can add other templates for specific pages, which the user can then use in his ``POSTS``
or ``PAGES`` option in ``conf.py``. Also, keep in mind that your theme is yours,
there is no reason why you would need to maintain the inheritance as it is, or not
require whatever data you want.

Also, you can specify a custom template to be used by a post or page via the ``template`` metadata,
and custom templates can be added in the ``templates/`` folder of your site.

Messages and Translations
-------------------------

The included themes are translated into a variety of languages. You can add your own translation
at https://www.transifex.com/projects/p/nikola/

If you want to create a theme that has new strings, and you want those strings to be translatable,
then your theme will need a custom ``messages`` folder.

`LESS <http://lesscss.org/>`__ and `Sass <http://sass-lang.com/>`__
-------------------------------------------------------------------

.. note::
    The LESS and Sass compilers will be moved to the Plugins Index in
    Nikola v7.0.0.

If you want to use those CSS extensions, you can — just store your files
in the ``less`` or ``sass`` directory of your theme.

In order to have them work, you need to create a list of ``.less`` or
``.scss/.sass`` files to compile — the list should be in a file named
``targets`` in the respective directory (``less``/``sass``).

The files listed in the ``targets`` file will be passed to the respective
compiler, which you have to install manually (``lessc`` which comes from
the Node.js package named ``less`` or ``sass`` from a Ruby package aptly
named ``sass``).  Whatever the compiler outputs will be saved as a CSS
file in your rendered site, with the ``.css`` extension.

.. note::
    Conflicts may occur if you have two files with the same base name
    but a different extension.  Pay attention to how you name your files
    or your site won’t build!  (Nikola will tell you what’s wrong when
    this happens)
