.. title: Theming Nikola
.. slug: theming
.. date: 2012-03-13 12:00:00 UTC-03:00
.. tags:
.. link:
.. description:
.. author: The Nikola Team

:Version: 8.0.3
:Author: Roberto Alsina <ralsina@netmanagers.com.ar>

.. class:: alert alert-primary float-md-right

.. contents::

.. class:: lead

This document is a reference about themes. If you want a tutorial, please read
:doc:`Creating a Theme <creating-a-theme>`. If you’re looking for a ready-made
theme for your site, check out the `Themes Index <https://themes.getnikola.com/>`_.

The Structure
-------------

Themes are located in the ``themes`` folder where Nikola is installed, and in the ``themes`` folder
of your site, one folder per theme. The folder name is the theme name.

A Nikola theme consists of the following folders (they are *all* optional):

assets
    This is where you would put your CSS, JavaScript and image files. It will be copied
    into ``output/assets`` when you build the site, and the templates will contain
    references to them. The default subdirectories are ``css``, ``js``, ``xml``
    and ``fonts`` (Bootstrap).

    The included themes use `Bootstrap <https://getbootstrap.com/>`_,
    `baguetteBox <https://feimosi.github.io/baguetteBox.js/>`_, `Justified Layout by Flickr
    <http://flickr.github.io/justified-layout/>`_ and `Moment.js
    <https://momentjs.com/>`_, so they are in assets, along with CSS files for
    syntax highlighting, reStructuredText and Jupyter, as well as a minified
    copy of jQuery.

    If you want to base your theme on other frameworks (or on no framework at all)
    just remember to put there everything you need for deployment. (Not all of
    the listed assets are used by ``base``)

templates
    This contains the templates used to generate the pages. While Nikola will use a
    certain set of template names by default, you can add others for specific parts
    of your site.

messages
    Nikola tries to be multilingual. This is where you put the strings for your theme
    so that it can be translated into other languages.

less, sass
    Files to be compiled into CSS using LESS and Sass (both require plugins)

This mandatory file:

<theme>.theme
    An INI file containing theme meta data. The file format is described in
    detail below, in the `Theme meta files`_ section.

And these optional files:

parent, engine
    One-line text files that contain the names of parent and engine themes,
    respectively.  Those are needed for older versions (Nikola v7.8.5 and
    older).

bundles
    A `config <https://docs.python.org/3/library/configparser.html>`_ file
    containing a list of files to be turned into bundles. For example:

    .. code:: ini

        assets/css/all.css=
            bootstrap.min.css,
            rst_base.css,
            nikola_rst.css,
            code.css,
            baguetteBox.min.css,
            theme.css,
            custom.css,

    This creates a file called "assets/css/all.css" in your output that is the
    combination of all the other file paths, relative to the output file.
    This makes the page much more efficient because it avoids multiple connections to the server,
    at the cost of some extra difficult debugging.

    Bundling applies to CSS and JS files.

    Templates should use either the bundle or the individual files based on the ``use_bundles``
    variable, which in turn is set by the ``USE_BUNDLES`` option.

Theme meta files
----------------

As of Nikola v7.8.6, Nikola uses meta files for themes. Those are INI files,
with the same name as your theme, and a ``.theme`` extension, eg.
``bootstrap3.theme``. Here is an example, from the bootstrap3 theme:

.. code:: ini

   [Theme]
   engine = mako
   parent = base
   author = The Nikola Contributors
   author_url = https://getnikola.com/
   based_on = Bootstrap 3 <http://getbootstrap.com/>
   license = MIT
   tags = bootstrap

   [Family]
   family = bootstrap3
   jinja_version = bootstrap3-jinja
   variants = bootstrap3-gradients, bootstrap3-gradients-jinja

   [Nikola]
   bootswatch = True

The following keys are currently supported:

* ``Theme`` — contains information about the theme.

  * ``engine`` — engine used by the theme. Should be ``mako`` or ``jinja``.
  * ``parent`` — the parent theme. Any resources missing in this theme, will be
    looked up in the parent theme (and then in the grandparent, etc).

    The parent is so you don’t have to create a full theme each time: just
    create an empty theme, set the parent, and add the bits you want modified.
    You **must** define a parent, otherwise many features won’t work due to
    missing templates, messages, and assets.

    The following settings are recommended:

    * If your theme uses Bootstrap 3, inherit the ``bootstrap3`` theme.
    * If your theme uses Jinja as a template engine, inherit ``base-jinja``
      or ``bootstrap3-jinja``
    * In any other case, inherit ``base``.

  * ``author``, ``author_url`` — used to identify theme author.
  * ``based_on`` — optional list of inspirations, frameworks, etc. used in the
    theme. Should be comma-separated, the format ``Name <URL>`` is recommended.
  * ``license`` — theme license. Pick MIT if you have no preference.
  * ``tags`` — optional list of tags (comma-separated) to describe the theme.

* ``Family`` — contains information about other related themes. All values
  optional. (Do not use unless you have related themes.)

  * ``family`` — the name of the main theme in a family, which is also used as
    the family name.
  * ``mako_version``, ``jinja_version`` — name of the mako/jinja version of the
    theme.
  * ``variants`` — comma-separated list of stylistic variants (other than the
    mako/jinja version listed above)

* ``Nikola`` — Nikola-specific information, currently optional.

  * ``bootswatch`` — whether or not theme supports Bootswatch styling (optional,
    defaults to False)
  * ``ignored_assets`` — comma-separated list of assets to ignore (relative to
    the ``assets/`` directory, eg. ``css/theme.css``)

Templates
---------

In templates there is a number of files whose name ends in ``.tmpl``. Those are the
theme’s page templates. They are done using the `Mako <http://makotemplates.org>`_
or `Jinja2 <http://jinja.pocoo.org>`_ template languages. If you want to do a theme, you
should learn one first. What engine is used by the theme is declared in the ``engine`` file.

.. Tip::

   If you are using Mako templates, and want some extra speed when building the site
   you can install Beaker and `make templates be cached <http://docs.makotemplates.org/en/latest/caching.html>`__


Both template engines have a nifty concept of template inheritance. That means that a
template can inherit from another and only change small bits of the output. For example,
``base.tmpl`` defines the whole layout for a page but has only a placeholder for content
so ``post.tmpl`` only define the content, and the layout is inherited from ``base.tmpl``.

Another concept is theme inheritance. You do not need to duplicate all the
default templates in your theme — you can just override the ones you want
changed, and the rest will come from the parent theme. (Every theme needs a
parent.)

Apart from the `built-in templates`_ listed below, you can add other templates for specific
pages, which the user can then use in his ``POSTS`` or ``PAGES`` option in
``conf.py``.  Also, you can specify a custom template to be used by a post or
page via the ``template`` metadata, and custom templates can be added in the
``templates/`` folder of your site.

If you want to modify (override) a built-in template, use ``nikola theme -c
<name>.tmpl``.  This command will copy the specified template file to the
``templates/`` directory of your currently used theme.

Keep in mind that your theme is *yours*, so you can require whatever data you
want (eg. you may depend on specific custom ``GLOBAL_CONTEXT`` variables, or
post meta attributes). You don’t need to keep the same theme structure as the
default themes do (although many of those names are hardcoded). Inheriting from
at least ``base`` (or ``base-jinja``) is heavily recommended, but not strictly
required (unless you want to share it on the Themes Index).

Built-in templates
------------------

These are the templates that come with the included themes:

``base.tmpl``
    This template defines the basic page layout for the site. It’s mostly plain HTML
    but defines a few blocks that can be re-defined by inheriting templates.

    It has some separate pieces defined in ``base_helper.tmpl``,
    ``base_header.tmpl`` and ``base_footer.tmpl`` so they can be
    easily overridden.

``index.tmpl``
    Template used to render the multipost indexes. The posts are in a ``posts`` variable.
    Some functionality is in the ``index_helper.tmpl`` helper template.

``archive_navigation_helper.tmpl`` (internal)
    Code that implements archive navigation (previous/up/next). Included by
    archive templates.

``archiveindex.tmpl``
    Used to display archives, if ``ARCHIVES_ARE_INDEXES`` is True.
    By default, it just inherits ``index.tmpl``, with added archive navigation
    and feeds.

``author.tmpl``
    Used to display author pages.

``authorindex.tmpl``
    Used to display author indexes, if ``AUTHOR_PAGES_ARE_INDEXES`` is True.
    By default, it just inherits ``index.tmpl``, with added feeds.

``comments_helper.tmpl`` (internal)
    This template handles comments. You should probably never touch it :-)
    It uses a bunch of helper templates, one for each supported comment system
    (all of which start with ``comments_helper``)

``ui_helper.tmpl``, ``pagination_helper.tmpl``
    These templates help render specific UI items, and can be tweaked as needed.

``gallery.tmpl``
    Template used for image galleries. Interesting data includes:

    * ``post``: A post object, containing descriptive ``post.text()`` for the gallery.
    * ``crumbs``: A list of ``link, crumb`` to implement breadcrumbs.
    * ``folders``: A list of folders to implement hierarchical gallery navigation.
    * ``enable_comments``: To enable/disable comments in galleries.
    * ``thumbnail_size``: The ``THUMBNAIL_SIZE`` option.
    * ``photo_array``: a list of dictionaries, each containing:

      + ``url``: URL for the full-sized image.
      + ``url_thumb``: URL for the thumbnail.
      + ``title``: The title of the image.
      + ``size``: A dict containing ``w`` and ``h``, the real size of the thumbnail.

    * ``photo_array_json``: a JSON dump of photo_array, used by the
      ``justified-layout`` script

``list.tmpl``
    Template used to display generic lists of links, which it gets in ``items``,
    a list of *(text, link, count)* elements.

``list_post.tmpl``
    Template used to display generic lists of posts, which it gets in ``posts``.

``listing.tmpl``
    Used to display code listings.

``math_helper.tmpl`` (internal)
    Used to add MathJax/KaTeX code to pages.

``post.tmpl``
    Template used by default for blog posts, gets the data in a ``post`` object
    which is an instance of the Post class. Some functionality is in the
    ``post_helper.tmpl`` and ``post_header.tmpl`` templates.

``post_list_directive.tmpl``
    Template used by the ``post_list`` reStructuredText directive.

``sectionindex.tmpl``
    Used to display section indexes, if ``POST_SECTIONS_ARE_INDEXES`` is True.
    By default, it just inherits ``index.tmpl``, with added feeds.

``page.tmpl``
    Used for pages that are not part of a blog, usually a cleaner, less
    intrusive layout than ``post.tmpl``, but same parameters.

``tag.tmpl``
    Used to show the contents of a single tag or category.

``tagindex.tmpl``
    Used to show the contents of a single tag or category, if ``TAG_PAGES_ARE_INDEXES`` is True.
    By default, it just inherits ``index.tmpl``, with added feeds and some
    extra features.

``tags.tmpl``
    Used to display the list of tags and categories.

Variables available in templates
--------------------------------

The full, complete list of variables available in templates is maintained in a separate
document: `Template variables <https://getnikola.com/template-variables.html>`_

Customizing themes to user color preference and section colors
--------------------------------------------------------------

The user’s preference for theme color is exposed in templates as
``theme_color`` set in the ``THEME_COLOR`` option.

Each section has an assigned color that is either set by the user or auto
selected by adjusting the hue of the user’s ``THEME_COLOR``. The color is
exposed in templates through ``post.section_color(lang)``. The function that
generates the colors from strings and any given color (by section name and
theme color for sections) is exposed through the
``colorize_str_from_base_color(string, hex_color)`` function

Hex color values, like that returned by the theme or section color can be
altered in the HSL colorspace through the function
``color_hsl_adjust_hex(hex_string, adjust_h, adjust_s, adjust_l)``.
Adjustments are given in values between 1.0 and -1.0. For example, the theme
color can be made lighter using this code:

.. code:: html+mako

    <!-- Mako -->
    <span style="color: ${color_hsl_adjust_hex(theme_color, adjust_l=0.05)}">

.. code:: html+jinja

    <!-- Jinja2 -->
    <span style="color: {{ color_hsl_adjust_hex(theme_color, adjust_l=0.05) }}">

Identifying and customizing different kinds of pages with a shared template
---------------------------------------------------------------------------

Nikola provides a ``pagekind`` in each template contexts that can be used to
modify shared templates based on the context it’s being used. For example,
the ``base_helper.tmpl`` is used in all pages, ``index.tmpl`` is used in
many contexts and you may want to add or remove something from only one of
these contexts.

Example of conditionally loading different resources on all index pages
(archives, author pages, and tag pages), and others again to the front page
and in every post pages:

.. code:: html+mako

    <!-- Mako -->
    <head>
        …
        % if 'index' in pagekind:
            <link href="/assets/css/multicolumn.css" rel="stylesheet">
        % endif
        % if 'front_page' in pagekind:
            <link href="/assets/css/fancy_homepage.css" rel="stylesheet">
            <script src="/assets/js/post_carousel.js"></script>
        % endif
        % if 'post_page' in pagekind:
            <link href="/assets/css/article.css" rel="stylesheet">
            <script src="/assets/js/comment_system.js"></script>
        % endif
    </head>

.. code:: html+jinja

    <!-- Jinja2 -->
    <head>
        …
        {% if 'index' in pagekind %}
            <link href="/assets/css/multicolumn.css" rel="stylesheet">
        {% endif %}
        {% if 'front_page' in pagekind %}
            <link href="/assets/css/fancy_homepage.css" rel="stylesheet">
            <script src="/assets/js/post_carousel.js"></script>
        {% endif %}
        {% if 'post_page' in pagekind %}
            <link href="/assets/css/article.css" rel="stylesheet">
            <script src="/assets/js/comment_system.js"></script>
        {% endif %}
    </head>


Promoting visits to the front page when visiting other filtered
``index.tmpl`` page variants such as author pages and tag pages. This
could have been included in ``index.tmpl`` or maybe in ``base.tmpl``
depending on what you want to achieve.

.. code:: html+mako

    <!-- Mako -->
    % if 'index' in pagekind:
        % if 'author_page' in pagekind:
            <p>These posts were written by ${author}. See posts by all
               authors on the <a href="/">front page</a>.</p>
        % elif 'tag_page' in pagekind:
            <p>This is a filtered selection of posts tagged “${tag}”, visit
               the <a href="/">front page</a> to see all posts.</p>
        % endif
    % endif

.. code:: html+jinja

    <!-- Jinja2 -->
    {% if 'index' in pagekind %}
        {% if 'author_page' in pagekind %}
            <p>These posts were written by {{ author }}. See posts by all
               authors on the <a href="/">front page</a>.</p>
        {% elif 'tag_page' in pagekind %}
            <p>This is a filtered selection of posts tagged “{{ tag }}”, visit
               the <a href="/">front page</a> to see all posts.</p>
        {% endif %}
    {% endif %}


List of page kinds provided by default plugins:

* front_page
* index
* index, archive_page
* index, author_page
* index, main_index
* index, section_page
* index, tag_page
* list
* list, archive_page
* list, author_page
* list, section_page
* list, tag_page
* list, tags_page
* post_page
* page_page
* story_page
* listing
* generic_page
* gallery_front
* gallery_page

Messages and Translations
-------------------------

The included themes are translated into a variety of languages. You can add your own translation
at https://www.transifex.com/projects/p/nikola/

If you want to create a theme that has new strings, and you want those strings to be translatable,
then your theme will need a custom ``messages`` folder.

`LESS <http://lesscss.org/>`__ and `Sass <http://sass-lang.com/>`__
-------------------------------------------------------------------

.. note::
    The LESS and Sass compilers were moved to the Plugins Index in
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
