.. title: The Nikola Handbook
.. slug: handbook
.. date: 2012-03-30 23:00:00 UTC-03:00
.. link:
.. description:
.. tags:
.. has_math: true
.. author: The Nikola Team

:Version: 8.0.4

.. class:: alert alert-primary float-md-right

.. contents::


All You Need to Know
--------------------

After you have Nikola `installed <https://getnikola.com/getting-started.html>`_:

Create an empty site (with a setup wizard):
    ``nikola init mysite``

    You can create a site with demo files in it with ``nikola init --demo mysite``

    The rest of these commands have to be executed inside the new ``mysite`` folder.

Create a post:
    ``nikola new_post``

Edit the post:
    The filename should be in the output of the previous command.
    You can also use ``nikola new_post -e`` to open an editor automatically.

Build the site:
     ``nikola build``

Start the test server and open a browser:
     ``nikola serve -b``


That should get you going. If you want to know more, this manual will always be here
for you.

DON'T READ THIS MANUAL. IF YOU NEED TO READ IT I FAILED, JUST USE THE THING.

On the other hand, if anything about Nikola is not as obvious as it should be, by all
means tell me about it :-)

What's Nikola and what can you do with it?
------------------------------------------

Nikola is a static website and blog generator. The very short explanation is
that it takes some texts you wrote, and uses them to create a folder full
of HTML files. If you upload that folder to a server, you will have a
rather full-featured website, done with little effort.

Its original goal is to create blogs, but it supports most kind of sites, and
can be used as a CMS, as long as what you present to the user is your own content
instead of something the user generates.

Nikola can do:

* A blog (`example <http://ralsina.me>`__)
* Your company's site
* Your personal site
* A software project's site (`example <https://getnikola.com>`__)
* A book's site

Since Nikola-based sites don't run any code on the server, there is no way to process
user input in forms.

Nikola can't do:

* Twitter
* Facebook
* An Issue tracker
* Anything with forms, really (except for `comments`_!)

Keep in mind that "static" doesn't mean **boring**. You can have animations
or whatever fancy CSS3/HTML5 thingie you like. It only means all that HTML is
generated already before being uploaded. On the other hand, Nikola sites will
tend to be content-heavy. What Nikola is good at is at putting what you write
out there.

Getting Help
------------

.. class:: lead

`Get help here! <https://getnikola.com/contact.html>`_

TL;DR:

* You can file bugs at `the issue tracker <https://github.com/getnikola/nikola/issues>`__
* You can discuss Nikola at the `nikola-discuss google group <http://groups.google.com/group/nikola-discuss>`_
* You can subscribe to `the Nikola Blog <https://getnikola.com/blog>`_
* You can follow `Nikola on Twitter <https://twitter.com/GetNikola>`_

Why Static?
-----------

Most "modern" websites are *dynamic* in the sense that the contents of the site
live in a database, and are converted into presentation-ready HTML only when a
user wants to see the page. That's great. However, it presents some minor issues
that static site generators try to solve.

In a static site, the whole site, every page, *everything*, is created before
the first user even sees it and uploaded to the server as a simple folder full
of HTML files (and images, CSS, etc).

So, let's see some reasons for using static sites:

Security
    Dynamic sites are prone to experience security issues. The solution for that
    is constant vigilance, keeping the software behind the site updated, and
    plain old good luck. The stack of software used to provide a static site,
    like those Nikola generates, is much smaller (Just a web server).

    A smaller software stack implies less security risk.

Obsolescence
    If you create a site using (for example) WordPress, what happens when WordPress
    releases a new version? You have to update your WordPress. That is not optional,
    because of security and support issues. If I release a new version of Nikola, and
    you don't update, *nothing* happens. You can continue to use the version you
    have now forever, no problems.

    Also, in the longer term, the very foundations of dynamic sites shift. Can you
    still deploy a blog software based on Django 0.96? What happens when your
    host stops supporting the PHP version you rely on? And so on.

    You may say those are long term issues, or that they won't matter for years. Well,
    I believe things should work forever, or as close to it as we can make them.
    Nikola's static output and its input files will work as long as you can install
    Python 3.4 or newer under Linux, Windows, or OS X and can find a server
    that sends files over HTTP. That's probably 10 or 15 years at least.

    Also, static sites are easily handled by the Internet Archive.

Cost and Performance
    On dynamic sites, every time a reader wants a page, a whole lot of database
    queries are made. Then a whole pile of code chews that data, and HTML is
    produced, which is sent to the user. All that requires CPU and memory.

    On a static site, the highly optimized HTTP server reads the file from disk
    (or, if it's a popular file, from disk cache), and sends it to the user. You could
    probably serve a bazillion (technical term) page views from a phone using
    static sites.

Lock-in
    On server-side blog platforms, sometimes you can't export your own data, or
    it's in strange formats you can't use in other services. I have switched
    blogging platforms from Advogato to PyCs to two homebrew systems, to Nikola,
    and have never lost a file, a URL, or a comment. That's because I have *always*
    had my own data in a format of my choice.

    With Nikola, you own your files, and you can do anything with them.

Components
----------

Nikola provides the following features:

* Blog support, including:

  * Indexes
  * RSS and Atom feeds
  * Tags and categories, with pages and feeds
  * Author pages and feeds (not generated if ``ENABLE_AUTHOR_PAGES`` is set to ``False`` or there is only one author)
  * Archives with custom granularity (yearly or monthly)
  * `Comments`_

* Static pages (not part of the blog)
* `Math`_ rendering (via MathJax)
* Custom output paths for generated pages
* Pretty URLs (without ``.html``) that don’t need web server support
* Easy page template customization
* Internationalization support (my own blog is English and Spanish)
* Sitemap generation (for search engines)
* Custom deployment (if it’s a command, you can use it)
* GitHub Pages deployment
* Themes, easy appearance customization
* `Multiple input formats <#supported-input-formats>`_, including reStructuredText and Markdown
* Easy-to-create image galleries
* Image thumbnail generation
* Support for displaying source code listings
* Custom search
* Asset (CSS/JS) bundling
* gzip compression (for sending via your web server)
* Open Graph, Twitter Cards
* Hyphenation
* Custom `post processing filters`_ (eg. for minifying files or better typography)

Getting Started
---------------

.. class:: lead

To set Nikola up and create your first site, read the `Getting Started Guide <https://getnikola.com/getting-started.html>`_.

Creating a Blog Post
--------------------

.. sidebar:: Magic Links

   You will want to do things like "link from one post to another" or "link to an image gallery",
   etc. Sure, you can just figure out the URLs for each thing and use that. Or you can use
   Nikola's special link URLs. Those are done using the syntax ``link://kind/name`` and
   a full list of the included ones is `here <link://slug/path-handlers>`__ (BTW, I linked
   to that using ``link://slug/path-handlers``).

   Note that magic links with spaces won’t work with some input formats (eg.
   reST), so you should use slugs there (eg. ``link://tag/some-tag`` instead of
   ``link://tag/Some Tag``)


To create a new post, the easiest way is to run ``nikola new_post``. You  will
be asked for a title for your post, and it will tell you where the post's file
is located.

By default, that file will contain also some extra information about your post ("the metadata").
It can be placed in a separate file by using the ``-2`` option, but it's generally
easier to keep it in a single location.

The contents of your post have to be written (by default) in `reStructuredText <http://docutils.sf.net>`__
but you can use a lot of different markups using the ``-f`` option.

Currently, Nikola supports reStructuredText, Markdown, Jupyter Notebooks, HTML as input,
can also use Pandoc for conversion, and has support for BBCode, CreoleWiki, txt2tags, Textile
and more via plugins — for more details, read the `input format documentation
<#multiple-input-formats>`__.
You can learn reStructuredText syntax with the `reST quickstart <https://getnikola.com/quickstart.html>`__.

Please note that Nikola does not support encodings other than UTF-8. Make sure
to convert your input files to that encoding to avoid issues.  It will prevent
bugs, and Nikola will write UTF-8 output anyway.

You can control what markup compiler is used for each file extension with the ``COMPILERS``
option. The default configuration expects them to be placed in ``posts`` but that can be
changed (see below, the ``POSTS`` and ``PAGES`` options)

This is how it works:

.. code:: console

    $ nikola new_post
    Creating New Post
    -----------------

    Title: How to make money
    Scanning posts....done!
    INFO: new_post: Your post's text is at: posts/how-to-make-money.rst

The content of that file is as follows:

.. code:: restructuredtext

    .. title: How to make money
    .. slug: how-to-make-money
    .. date: 2012-09-15 19:52:05 UTC
    .. tags:
    .. link:
    .. description:
    .. type: text

    Write your post here.

You can edit these files with your favorite text editor, and once you are happy
with the contents, generate the pages using ``nikola build``.

The post page is generated by default using the ``post.tmpl`` template, which you can use
to customize the output. You can also customize paths and the template filename
itself — see `How does Nikola decide where posts should go?`

Metadata fields
~~~~~~~~~~~~~~~

Nikola supports many metadata fields in posts. All of them are
translatable and almost all are optional.

Basic
`````

title
    Title of the post. (required)

slug
    Slug of the post. Used as the last component of the page URL.  We recommend
    and default to using a restricted character set (``a-z0-9-_``) because
    other symbols may cause issues in URLs. (required)

    So, if the slug is "the-slug" the page generated would be "the-slug.html" or
    "the-slug/index.html" (if you have the pretty URLs option enabled) 

    One special case is setting the slug to "index". This means the page generated 
    would be "some_folder/index.html", which means it will be open for the URL
    that ends in "some_folder" or "some_folder/".

    This is useful in some cases, in others may cause conflicts with other pages
    Nikola generates (like blog indexes) and as a side effect it disables 
    "pretty URLs" for this page. So use with care.

date
    Date of the post, defaults to now. Multiple date formats are accepted.
    Adding a timezone is recommended. (required for posts)

tags
    Comma-separated tags of the post.

status
    Can be set to ``published`` (default), ``featured``, ``draft``, or ``private``.

has_math
    If set to ``true`` or ``yes``, MathJax resp. KaTeX support is enabled
    for this post.

category
    Like tags, except each post can have only one, and they usually have
    more descriptive names.

guid
    String used as GUID in RSS feeds and as ID in Atom feeds instead of the
    permalink.

link
    Link to original source for content. May be displayed by some themes.

description
    Description of the post. Used in ``<meta>`` tags for SEO.

type
    Type of the post. See `Post Types`_ for details.  Whatever you set here
    (prepended with ``post-``) will become a CSS class of the ``<article>``
    element for this post.  Defaults to ``text`` (resulting in a ``post-text``
    class)

Extra
`````

author
    Author of the post, will be used in the RSS feed and possibly in the post
    display (theme-dependent)

enclosure
    Add an enclosure to this post when it's used in RSS. See `more information about enclosures <http://en.wikipedia.org/wiki/RSS_enclosure>`__

data
    Path to an external data file (JSON/YAML/TOML dictionary), relative to ``conf.py``.
    Its keys are available for templates as ``post.data('key')``.

    Translated posts can have different values for this field, and the correct one will be
    used.

    See `The Global Context and Data files`_ for more details.  This is
    especially useful used in combination with `shortcodes`_.

filters
    See the `Post Processing Filters`_ section.

hidetitle
    Set "True" if you do not want to see the **page** title as a
    heading of the output html file (does not work for posts).

hyphenate
    Set "True" if you want this document to be hyphenated even if you have
    hyphenation disabled by default.

nocomments
    Set to "True" to disable comments. Example:

pretty_url
    Set to "False" to disable pretty URL for this page. Example:

previewimage
    Designate a preview or other representative image path relative to BASE_URL
    for use with Open Graph for posts. Adds the image when sharing on social
    media, feeds, and many other uses.

    .. code:: restructuredtext

       .. previewimage: /images/looks_great_on_facebook.png

    The image can be of any size and dimension (services will crop and adapt)
    but should less than 1 MB and be larger than 300x300 (ideally 600x600).

    This image is displayed by ``bootblog4`` for featured posts (see `Featured
    Posts`_ for details).

template
    Change the template used to render this page/post specific page. That
    template needs to either be part of the theme, or be placed in a
    ``templates/`` folder inside your site.

    .. code:: restructuredtext

       .. template: foobar.tmpl

updated
    The last time this post was updated, defaults to the post’s ``date``
    metadata value. It is not displayed by default in most themes, including
    the defaults — you can use ``post.formatted_updated(date_format)`` (and
    perhaps check ``if post.updated != post.date``) in your post template to
    show it.

To add these metadata fields to all new posts by default, you can set the
variable ``ADDITIONAL_METADATA`` in your configuration.  For example, you can
add the author metadata to all new posts by default, by adding the following
to your configuration:

.. code:: python

    ADDITIONAL_METADATA = {
        'author': 'John Doe'
    }

url_type
    Change the URL_TYPE setting for the given page only. Useful for eg. error
    pages which cannot use relative URLs.

    .. code:: restructuredtext

       .. url_type: full_path

Metadata formats
~~~~~~~~~~~~~~~~

Metadata can be in different formats.
Current Nikola versions experimentally supports other metadata formats that make it more compatible with
other static site generators. The currently supported metadata formats are:

* reST-style comments (``.. name: value`` — default format)
* Two-file format (reST-style, YAML, TOML)
* Jupyter Notebook metadata
* YAML, between ``---`` (Jekyll, Hugo)
* TOML, between ``+++`` (Hugo)
* reST docinfo (Pelican)
* Markdown metadata extension (Pelican)
* HTML meta tags (Pelican)

You can add arbitrary meta fields in any format.

When you create new posts, by default the metadata will be created as reST style comments.
If you prefer a different format, you can set the ``METADATA_FORMAT`` to one of these values:

* ``"Nikola"``: reST comments, wrapped in a HTML comment if needed (default)
* ``"YAML"``: YAML wrapped in "---"
* ``"TOML"``: TOML wrapped in "+++"
* ``"Pelican"``: Native markdown metadata or reST docinfo fields. Nikola style for other formats.

reST-style comments
```````````````````

The “traditional” and default meta field format is:

.. code:: text

   .. name: value

If you are not using reStructuredText, make sure the fields are in a HTML comment in output.

Also, note that this format does not support any multi-line values. Try YAML or reST docinfo if you need those.

Two-file format
```````````````

Meta information can also be specified in separate ``.meta`` files. Those support reST-style metadata, with names and custom fields. They look like the beginning of our reST files:

.. code:: text

    .. title: How to make money
    .. slug: how-to-make-money
    .. date: 2012-09-15 19:52:05 UTC

You can also use YAML or TOML metadata inside those (with the appropriate markers).

Jupyter Notebook metadata
`````````````````````````

Jupyter posts can store meta information inside ``.ipynb`` files by using the ``nikola`` key inside notebook metadata. It can be edited by using *Edit → Edit Notebook Metadata* in Jupyter. Note that values are currently only strings. Sample metadata (Jupyter-specific information omitted):

.. code:: json

    {
        "nikola": {
            "title": "How to make money",
            "slug": "how-to-make-money",
            "date": "2012-09-15 19:52:05 UTC"
        }
    }


YAML metadata
`````````````

YAML metadata should be wrapped by a ``---`` separator (three dashes) and in that case, the usual YAML syntax is used:

.. code:: yaml

   ---
   title: How to make money
   slug: how-to-make-money
   date: 2012-09-15 19:52:05 UTC
   ---

TOML metadata
`````````````

TOML metadata should be wrapped by a "+++" separator (three plus signs) and in that case, the usual TOML syntax is used:

.. code:: yaml

   +++
   title = "How to make money"
   slug =  "how-to-make-money"
   date = "2012-09-15 19:52:05 UTC"
   +++

reST docinfo
````````````

Nikola can extract metadata from reStructuredText docinfo fields and the document itself, too:

.. code:: restructuredtext

    How to make money
    =================

    :slug: how-to-make-money
    :date: 2012-09-15 19:52:05 UTC

To do this, you need  ``USE_REST_DOCINFO_METADATA = True`` in your ``conf.py``,
and Nikola will hide the docinfo fields in the output if you set
``HIDE_REST_DOCINFO = True``.

.. note::

    Keys are converted to lowercase automatically.

    This setting also means that the first heading in a post will be removed
    and considered a title. This is important if you’re mixing metadata
    styles. This can be solved by putting a reST comment before your title.

Pelican/Markdown metadata
`````````````````````````

Markdown Metadata (Pelican-style) only works in Markdown files, and requires the ``markdown.extensions.meta`` extension
(see `MARKDOWN_EXTENSIONS <#markdown>`__). The exact format is described in
the `markdown metadata extension docs. <https://python-markdown.github.io/extensions/meta_data/>`__

.. code:: text

   title: How to make money
   slug: how-to-make-money
   date: 2012-09-15 19:52:05 UTC

Note that keys are converted to lowercase automatically.

HTML meta tags
``````````````

For HTML source files, metadata will be extracted from ``meta`` tags, and the title from the ``title`` tag.
Following Pelican's behaviour, tags can be put in a "tags" meta tag or in a "keywords" meta tag. Example:

.. code:: html

    <html>
        <head>
            <title>My super title</title>
            <meta name="tags" content="thats, awesome" />
            <meta name="date" content="2012-07-09 22:28" />
            <meta name="modified" content="2012-07-10 20:14" />
            <meta name="category" content="yeah" />
            <meta name="authors" content="Conan Doyle" />
            <meta name="summary" content="Short version for index and feeds" />
        </head>
        <body>
            This is the content of my super blog post.
        </body>
    </html>


Mapping metadata from other formats
```````````````````````````````````

If you import posts from other engines, those may not work with Nikola out of the box due to differing names. However, you can create a mapping to convert meta field names from those formats into what Nikola expects.

For Pelican, use:

.. code:: python

    METADATA_MAPPING = {
        "rest_docinfo": {"summary": "description", "modified": "updated"},
        "markdown_metadata": {"summary": "description", "modified": "updated"}
        "html_metadata": {"summary": "description", "modified": "updated"}
    }

For Hugo, use:

.. code:: python

    METADATA_MAPPING = {
        "yaml": {"lastmod": "updated"},
        "toml": {"lastmod": "updated"}
    }

The following source names are supported: ``yaml``, ``toml``, ``rest_docinfo``, ``markdown_metadata``.

Additionally, you can use ``METADATA_VALUE_MAPPING`` to perform any extra conversions on metadata for **all** posts of a given format (``nikola`` metadata is also supported). A few examples:

.. code:: python

    METADATA_VALUE_MAPPING = {
        "yaml": {"keywords": lambda value: ', '.join(value)},  # yaml: 'keywords' list -> str
        "nikola": {
            "widgets": lambda value: value.split(', '),  # nikola: 'widgets' comma-separated string -> list
            "tags": str.lower  # nikola: force lowercase 'tags' (input would be string)
         }
    }

Multilingual posts
~~~~~~~~~~~~~~~~~~

If you are writing a multilingual site, you can also create a per-language
post file (for example: ``how-to-make-money.es.txt`` with the default TRANSLATIONS_PATTERN, see below).
This one can replace metadata of the default language, for example:

* The translated title for the post or page
* A translated version of the page name

The pattern used for finding translations is controlled by the
TRANSLATIONS_PATTERN variable in your configuration file.

The default is to put the language code before the file extension,
so the German translation of ``some_file.rst`` should be named
``some_file.de.rst``. This is because the TRANSLATIONS_PATTERN variable is by
default set to:

.. code:: python

    TRANSLATIONS_PATTERN = "{path}.{lang}.{ext}"

.. admonition:: Considered languages

    Nikola will only look for translation of input files for languages
    specified in the TRANSLATIONS variable.

In case you translate your posts, you might also want to adjust various
other settings so that the generated URLs match the translation. You can
find most places in `conf.py` by searching for `(translatable)`. For example,
you might want to localize `/categories/` (search for `TAG_PATH`), `/pages/`
and `/posts/` (search for `POSTS` and `PAGES`, or see the next section), or
how to adjust the URLs for subsequent pages for indexes (search for
`INDEXES_PRETTY_PAGE_URL`).

Nikola supports multiple languages for a post (we have almost 50 translations!). If you wish to
add support for more languages, check out `the Transifex page for Nikola <https://www.transifex.com/projects/p/nikola/>`_

How does Nikola decide where posts should go?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The place where the post will be placed by ``new_post`` (the first one that
matches the given format) and the final post destination (the first one that
matches a given file) is based on the ``POSTS`` and ``PAGES`` configuration
options. The exact mechanism is explained above the config options in the
``conf.py`` file, and also reproduced below:

.. code:: python

    # POSTS and PAGES contains (wildcard, destination, template) tuples.
    #
    # The wildcard is used to generate a list of post source files
    # (whatever/thing.rst, for example).
    #
    # That fragment could have an associated metadata file (whatever/thing.meta),
    # and optionally translated files (example for Spanish, with code "es"):
    #     whatever/thing.es.rst and whatever/thing.es.meta
    #
    #     This assumes you use the default TRANSLATIONS_PATTERN.
    #
    # From those files, a set of HTML fragment files will be generated:
    # cache/whatever/thing.html (and maybe cache/whatever/thing.html.es)
    #
    # These files are combined with the template to produce rendered
    # pages, which will be placed at
    # output/TRANSLATIONS[lang]/destination/pagename.html
    #
    # where "pagename" is the "slug" specified in the metadata file.
    # The page might also be placed in /destination/pagename/index.html
    # if PRETTY_URLS are enabled.
    #
    # The difference between POSTS and PAGES is that POSTS are added
    # to feeds, indexes, tag lists and archives and are considered part
    # of a blog, while PAGES are just independent HTML pages.
    #
    # Finally, note that destination can be translated, i.e. you can
    # specify a different translation folder per language. Example:
    #     PAGES = (
    #         ("pages/*.rst", {"en": "pages", "de": "seiten"}, "page.tmpl"),
    #         ("pages/*.md", {"en": "pages", "de": "seiten"}, "page.tmpl"),
    #     )

    POSTS = (
        ("posts/*.rst", "posts", "post.tmpl"),
        ("posts/*.txt", "posts", "post.tmpl"),
        ("posts/*.html", "posts", "post.tmpl"),
    )
    PAGES = (
        ("pages/*.rst", "pages", "page.tmpl"),
        ("pages/*.txt", "pages", "page.tmpl"),
        ("pages/*.html", "pages", "page.tmpl"),
    )

.. admonition:: POSTS and PAGES are not flat!

   Even if the syntax may suggest you can't, you can create any directory structure you want
   inside ``posts/`` or ``pages/`` and it will be reflected in the output. For example,
   ``posts/foo/bar.txt`` would produce  ``output/posts/foo/bar.html``, assuming the slug is also ``bar``.

   If you have ``PRETTY_URLS`` enabled, that would be ``output/posts/foo/bar/index.html``.


.. warning::

    Removing the ``.rst`` entries is not recommended. Some features (eg.
    shortcodes) may not work properly if you do that.

The ``new_post`` command
~~~~~~~~~~~~~~~~~~~~~~~~

``new_post`` will use the *first* path in ``POSTS`` (or ``PAGES`` if ``-p`` is
supplied) that ends with the extension of your desired markup format (as
defined in ``COMPILERS`` in ``conf.py``) as the directory that the new post will be
written into.  If no such entry can be found, the post won’t be created.

The ``new_post`` command supports some options:

.. code:: text

    $ nikola help new_post
    Purpose: create a new blog post or site page
    Usage:   nikola new_post [options] [path]

    Options:
      -p, --page                Create a page instead of a blog post. (see also: `nikola new_page`)
      -t ARG, --title=ARG       Title for the post.
      -a ARG, --author=ARG      Author of the post.
      --tags=ARG                Comma-separated tags for the post.
      -1                        Create the post with embedded metadata (single file format)
      -2                        Create the post with separate metadata (two file format)
      -e                        Open the post (and meta file, if any) in $EDITOR after creation.
      -f ARG, --format=ARG      Markup format for the post (use --available-formats for list)
      -F, --available-formats   List all available input formats
      -s                        Schedule the post based on recurrence rule
      -i ARG, --import=ARG      Import an existing file instead of creating a placeholder
      -d, --date-path           Create post with date path (eg. year/month/day, see NEW_POST_DATE_PATH_FORMAT in config)


The optional ``path`` parameter tells Nikola exactly where to put it instead of guessing from your config.
So, if you do ``nikola new_post posts/random/foo.txt`` you will have a post in that path, with
"foo" as its slug. You can also provide a directory name, in which case Nikola
will append the file name for you (generated from title).

The ``-d, --date-path`` option automates creation of ``year/month/day`` or
similar directory structures. It can be enabled on a per-post basis, or you can
use it for every post if you set ``NEW_POST_DATE_PATH = True`` in conf.py.

.. code:: python

   # Use date-based path when creating posts?
   # Can be enabled on a per-post basis with `nikola new_post -d`.
   # NEW_POST_DATE_PATH = False

   # What format to use when creating posts with date paths?
   # Default is '%Y/%m/%d', other possibilities include '%Y' or '%Y/%m'.
   # NEW_POST_DATE_PATH_FORMAT = '%Y/%m/%d'

Teasers
~~~~~~~

You may not want to show the complete content of your posts either on your
index page or in RSS feeds, but to display instead only the beginning of them.

If it's the case, you only need to add a "magical comment" ``TEASER_END`` or
``END_TEASER`` in your post.

In reStructuredText:

.. code:: restructuredtext

   .. TEASER_END

In Markdown (or basically, the resulting HTML of any format):

.. code:: html

   <!-- TEASER_END -->

By default all your RSS feeds will be shortened (they'll contain only teasers)
whereas your index page will still show complete posts. You can change
this behavior with your ``conf.py``: ``INDEX_TEASERS`` defines whether index
page should display the whole contents or only teasers. ``FEED_TEASERS``
works the same way for your Atom and RSS feeds.

By default, teasers will include a "read more" link at the end. If you want to
change that text, you can use a custom teaser:

.. code:: restructuredtext

    .. TEASER_END: click to read the rest of the article

You can override the default value for ``TEASER_END`` in ``conf.py`` — for
example, the following example will work for ``.. more``, and will be
compatible with both WordPress and Nikola posts:

.. code:: python

    import re
    TEASER_REGEXP = re.compile('<!--\s*(more|TEASER_END|END_TEASER)(:(.+))?\s*-->', re.IGNORECASE)

Or you can completely customize the link using the ``READ_MORE_LINK`` option.

.. code:: python

    # A HTML fragment with the Read more... link.
    # The following tags exist and are replaced for you:
    # {link}        A link to the full post page.
    # {read_more}   The string “Read more” in the current language.
    # {{            A literal { (U+007B LEFT CURLY BRACKET)
    # }}            A literal } (U+007D RIGHT CURLY BRACKET)
    # READ_MORE_LINK = '<p class="more"><a href="{link}">{read_more}…</a></p>'

Drafts
~~~~~~

If you set the ``status`` metadata field of a post to ``draft``, it will not be shown
in indexes and feeds. It *will* be compiled, and if you deploy it it *will* be made
available, so use with care. If you wish your drafts to be not available in your
deployed site, you can set ``DEPLOY_DRAFTS = False`` in your configuration. This will
not work if you include ``nikola build`` in your ``DEPLOY_COMMANDS``, as the
option removes the draft posts before any ``DEPLOY_COMMANDS`` are run.

Also if a post has a date in the future, it will not be shown in indexes until
you rebuild after that date. This behavior can be disabled by setting
``FUTURE_IS_NOW = True`` in your configuration, which will make future posts be
published immediately.  Posts dated in the future are *not* deployed by default
(when ``FUTURE_IS_NOW = False``).  To make future posts available in the
deployed site, you can set ``DEPLOY_FUTURE = True`` in your configuration.
Generally, you want FUTURE_IS_NOW and DEPLOY_FUTURE to be the same value.

Private Posts
~~~~~~~~~~~~~

If you set the ``status`` metadata field of a post to ``private``, it will not be shown
in indexes and feeds. It *will* be compiled, and if you deploy it it *will* be made
available, so it will not generate 404s for people who had linked to it.

Featured Posts
~~~~~~~~~~~~~~

Some themes, ``bootblog4`` in particular, support featured posts. To mark a
post as featured, simply set the ``status`` meta field to ``featured``. All
featured posts are available in index templates in a ``featured``
list, but only if this is the main blog index.

For bootblog4, you can display up to three posts as featured: one can be shown
in a large gray box (jumbotron), and two more can appear in small white
cards.  In order to enable this feature, you need to add ``THEME_CONFIG`` to
your configuration, and set it up properly:

.. code:: python

    THEME_CONFIG = {
        DEFAULT_LANG: {
            # Show the latest featured post in a large box, with the previewimage as its background.
            'featured_large': True,
            # Show the first (remaining) two featured posts in small boxes.
            'featured_small': True,
            # Show featured posts on mobile.
            'featured_on_mobile': True,
            # Show image in `featured_large` on mobile.
            # `featured_small` displays them only on desktop.
            'featured_large_image_on_mobile': False,
            # Strip HTML from featured post text.
            'featured_strip_html': True,
            # Contents of the sidebar, If empty, the sidebar is not displayed.
            'sidebar': ''
        }
    }

You can pick betweeen (up to) 1, 2, or 3 featured posts. You can mix
``featured_large`` and ``featured_small``, rest assured that Nikola will always
display the latest posts no matter what setup you choose. If only one posts
qualifies for the small cards, one card taking up all the width will appear.

Both featured box formats display an image to the right. You can set it by changing the ``previewimage`` meta value to the full path to the image (eg. ``.. previewimage: /images/featured1.png``). This works best with images in portrait orientation.

Note that, due to space constraints, only the large box may show the image on
mobile, below the text (this behavior can be disbled). Small boxes never
display images on mobile. In particular: ``xs`` and ``sm`` display only the
large image, and only if configured; ``md`` displays only the large image,
``lg`` displays all three images.

The boxes display only the teaser. We recommend keeping it short so
you don’t get an ugly scrollbar.

Finally, here’s an example (you’ll need to imagine a scrollbar in the right box
yourself):

.. thumbnail:: https://getnikola.com/images/bootblog4-featured2x.png
   :align: center
   :alt: An example of how featured posts look in bootblog4.

Queuing Posts
~~~~~~~~~~~~~

Some blogs tend to have new posts based on a schedule (for example,
every Mon, Wed, Fri) but the blog authors don't like to manually
schedule their posts.  You can schedule your blog posts based on a
rule, by specifying a rule in the ``SCHEDULE_RULE`` in your
configuration.  You can either post specific blog posts according to
this schedule by using the ``--schedule`` flag on the ``new_post``
command or post all new posts according to this schedule by setting
``SCHEDULE_ALL = True`` in your configuration. (Note: This feature
requires that the ``FUTURE_IS_NOW`` setting is set to ``False``)

For example, if you would like to schedule your posts to be on every
Monday, Wednesday and Friday at 7am, add the following
``SCHEDULE_RULE`` to your configuration:

.. code:: python

    SCHEDULE_RULE = 'RRULE:FREQ=WEEKLY;BYDAY=MO,WE,FR;BYHOUR=7;BYMINUTE=0;BYSECOND=0'

For more details on how to specify a recurrence rule, look at the
`iCal specification <http://www.kanzaki.com/docs/ical/rrule.html>`_.
Or if you are scared of this format, many calendaring applications (eg. Google
Calendar) offer iCal exports, so you can copy-paste the repeat rule from a
generated iCal (``.ics``) file (which is a human-readable text file).

Say, you get a free Sunday, and want to write a flurry of new posts,
or at least posts for the rest of the week, you would run the
``new_post`` command with the ``--schedule`` flag, as many times as
you want:

.. code:: console

    $ nikola new_post --schedule
    # Creates a new post to be posted on Monday, 7am.
    $ nikola new_post -s
    # Creates a new post to be posted on Wednesday, 7am.
    $ nikola new_post -s
    # Creates a new post to be posted on Friday, 7am.
    .
    .
    .

All these posts get queued up according to your schedule, but note
that you will anyway need to build and deploy your site for the posts
to appear online.  You can have a cron job that does this regularly.

Post Types
~~~~~~~~~~

Nikola supports specifying post types, just like Tumblr does.  Post
types affect the look of your posts, by adding a ``post-YOURINPUTHERE``
CSS class to the post.  Each post can have one and exactly one type.  Nikola
styles the following types in the default themes:

.. class:: table table-bordered

+-----------------+----------------------------+------------------+
| Name(s)         | Description                | Styling          |
+=================+============================+==================+
| text            | plain text — default value | standard         |
+-----------------+----------------------------+------------------+
| micro           | “small” (short) posts      | big serif font   |
+-----------------+----------------------------+------------------+

Indexes
~~~~~~~

All your posts that are not drafts, private or dated in the future, will be
shown in indexes.

Settings
````````

Indexes are put in the ``INDEX_PATH`` directory, which defaults to an empty
string (site root).  The “main” index is ``index.html``, and all the further
indexes are ``index-*.html``, respectively.

By default, 10 posts are displayed on an index page.  This can be changed with
``INDEX_DISPLAY_POST_COUNT``.  Indexes can show full posts or just the teasers,
as controlled by the ``INDEX_TEASERS`` setting (defaults to ``False``).

Titles of the pages can be controlled by using ``INDEXES_TITLES``,
``INDEXES_PAGES`` and ``INDEXES_PAGES_MAIN`` settings.

Categories and tags use simple lists by default that show only titles and
dates; however, you can switch them to full indexes by using
``CATEGORY_PAGES_ARE_INDEXES`` and ``TAG_PAGES_ARE_INDEXES``, respectively.

Something similar happens with authors. To use full indexes in authors, set
``AUTHOR_PAGES_ARE_INDEXES`` to ``True``.

Static indexes
``````````````

Nikola uses *static indexes* by default.  This means that ``index-1.html`` has
the oldest posts, and the newest posts past the first 10 are in
``index-N.html``, where ``N`` is the highest number.  Only the page with the
highest number and the main page (``index-N.html`` and ``index.html``) are
rebuilt (the others remain unchanged).  The page that appears when you click
*Older posts* on the index page, ``index-N.html``, might contain **less than 10
posts** if there are not enough posts to fill up all pages.

This can be disabled by setting ``INDEXES_STATIC`` to ``False``.  In that mode,
``index-1.html`` contains all the newest posts past the first 10 and will
always contain 10 posts (unless you have less than 20).  The last page,
``index-N.html``, contains the oldest posts, and might contain less than 10
posts.  This is how many blog engines and CMSes behave.  Note that this will
lead to rebuilding all index pages, which might be a problem for larger blogs
(with a lot of index pages).


Post taxonomy
~~~~~~~~~~~~~

There are two taxonomy systems in Nikola, or two ways to organize posts. Those are tags and categories. They are visible on the *Tags and Categories* page, by default available at ``/categories/``. Each tag/category has an index page and feeds.

Tags
````

Tags are the smallest and most basic of the taxonomy items. A post can have multiple tags, specified using the ``tags`` metadata entry (comma-separated). You should provide many tags to help your readers, and perhaps search engines, find content on your site.

Please note that tags are case-sensitive and that you cannot have two tags that differ only in case/punctuation (eg. using ``nikola`` in one post and ``Nikola`` in another will lead to a crash):

.. code:: text

   ERROR: Nikola: You have tags that are too similar: Nikola and nikola
   ERROR: Nikola: Tag Nikola is used in: posts/second-post.rst
   ERROR: Nikola: Tag nikola is used in: posts/1.rst

You can also generate a tag cloud with the `tx3_tag_cloud <https://plugins.getnikola.com/v7/tx3_tag_cloud/>`_ plugin or get a data file for a tag cloud with the `tagcloud <https://plugins.getnikola.com/v8/tagcloud/>`_ plugin.

Categories
``````````

The next unit for organizing your content are categories. A post can have only one category, specified with the ``category`` meta tag. They are displayed alongside tags. You can have categories and tags with the same name (categories’ RSS and HTML files are prefixed with ``cat_`` by default).

Categories are handy to organize different parts of your blog, parts that are about different topics. Unlike tags, which you should have tens (hundreds?) of, the list of categories should be shorter.

Nikola v7 used to support a third taxonomy, called sections. Those have been removed, but all the functionality can be recreated by using the ``CATEGORY_DESTPATH`` settings.


Configuring tags and categories
```````````````````````````````

There are multiple configuration variables dedicated to each of the two taxonomies. You can set:

* ``TAG_PATH``, ``TAGS_INDEX_PATH``, ``CATEGORY_PATH``, ``CATEGORY_PREFIX`` to configure paths used for tags and categories
* ``TAG_TITLES``, ``CATEGORY_TITLES`` to set titles and descriptions for index pages
* ``TAG_DESCRIPTIONS``, ``CATEGORY_DESCRIPTIONS`` to set descriptions for each of the items
* ``CATEGORY_ALLOW_HIERARCHIES`` and ``CATEGORY_OUTPUT_FLAT_HIERARCHIES`` to allow hierarchical categories
* ``TAG_PAGES_ARE_INDEXES`` and ``CATEGORY_PAGES_ARE_INDEXES`` to display full-size indexes instead of simple post lists
* ``HIDDEN_TAGS``. ``HIDDEN_CATEGORIES`` to make some tags/categories invisible in lists
* ``CATEGORY_DESTPATH_AS_DEFAULT`` to use the destination path as the category if none is specified in the post
* ``CATEGORY_DESTPATH_TRIM_PREFIX`` to trim the prefix that comes from ``POSTS`` for the destination path
* ``CATEGORY_DESTPATH_FIRST_DIRECTORY`` to only use the first directory name for the defaulted category
* ``CATEGORY_DESTPATH_NAMES`` to specify friendly names for defaulted categories
* ``CATEGORY_PAGES_FOLLOW_DESTPATH`` to put category pages next to their related posts (via destpath)

What if I don’t want a blog?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you want a static site that does not have any blog-related elements, see our
`Creating a Site (Not a Blog) with Nikola`__ guide.

__ https://getnikola.com/creating-a-site-not-a-blog-with-nikola.html

Creating a Page
---------------

Pages are the same as posts, except that:

* They are not added to the front page
* They don't appear on the RSS feed
* They use the ``page.tmpl`` template instead of ``post.tmpl`` by default

The default configuration expects the page's metadata and text files to be on the
``pages`` folder, but that can be changed (see ``PAGES`` option above).

You can create the page's files manually or use the ``new_post`` command
with the ``-p`` option, which will place the files in the folder that
has ``use_in_feed`` set to False.

In some places (including default directories and templates), pages are called
*stories* for historic reasons. Both are synonyms for the same thing: pages
that are not blog posts.

Supported input formats
-----------------------

Nikola supports multiple input formats.  Out of the box, we have compilers available for:

* reStructuredText (default and pre-configured)
* `Markdown`_ (pre-configured since v7.8.7)
* `Jupyter Notebook`_
* `HTML`_
* `PHP`_
* anything `Pandoc`_ supports (including Textile, DocBook, LaTeX, MediaWiki,
  TWiki, OPML, Emacs Org-Mode, txt2tags, Microsoft Word .docx, EPUB, Haddock markup)

Plus, we have specialized compilers in the Plugins Index for:

* `AsciiDoc <https://plugins.getnikola.com/#asciidoc>`_
* `BBCode <https://plugins.getnikola.com/#bbcode>`_
* `CommonMark <https://plugins.getnikola.com/#commonmark>`_
* `IRC logs <https://plugins.getnikola.com/#irclogs>`_
* `Markmin <https://plugins.getnikola.com/#markmin>`_
* `MediaWiki (smc.mw) <https://plugins.getnikola.com/#mediawiki>`_
* `Misaka <https://plugins.getnikola.com/#misaka>`_
* `ODT <https://plugins.getnikola.com/#odt>`_
* `Emacs Org-Mode <https://plugins.getnikola.com/#orgmode>`_
* `reST with HTML 5 output <https://plugins.getnikola.com/#rest_html5>`_
* `Textile <https://plugins.getnikola.com/#textile>`_
* `txt2tags <https://plugins.getnikola.com/#txt2tags>`_
* `CreoleWiki <https://plugins.getnikola.com/#wiki>`_
* `WordPress posts <https://plugins.getnikola.com/#wordpress_compiler>`_

To write posts in a different format, you need to configure the compiler and
paths. To create a post, use ``nikola new_post -f COMPILER_NAME``, eg. ``nikola
new_post -f markdown``. The default compiler used is the first entry in POSTS
or PAGES.

Configuring other input formats
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In order to use input formats other than reStructuredText, you need some extra
setup.

1. Make sure you have the compiler for the input format you want.  Some
   input formats are supported out-of-the-box, but others must be installed from
   the Plugins repository.  You may also need some extra dependencies.  You
   will get helpful errors if you try to build when missing something.
2. You must ensure the compiler and your desired input file extension is included
   in the ``COMPILERS`` dict and does not conflict with any other format.  This
   is extremely important for the pandoc compiler.
3. Finally, you must configure the ``POSTS`` and ``PAGES`` tuples.  Follow the
   instructions and the format set by pre-existing entries.  Make sure to use
   the same extension as is set in ``COMPILERS`` and configure the outputs
   properly.

Markdown
````````

To use Markdown in your posts/pages, make sure ``markdown`` is in your
``COMPILERS`` and that at least one of your desired extensions is defined in
``POSTS`` and ``PAGES``.

You can use Python-Markdown extensions by setting the ``MARKDOWN_EXTENSIONS``
config option:

.. code:: python

    MARKDOWN_EXTENSIONS = ['fenced_code', 'codehilite', 'extra']

Nikola comes with some Markdown Extensions built-in and enabled by default,
namely a gist directive, a podcast directive, and ``~~strikethrough~~`` support.

Jupyter Notebook
````````````````

To use Jupyter Notebooks as posts/pages, make sure ``ipynb`` is in your
``COMPILERS`` and that the ``.ipynb`` extension is defined in ``POSTS`` and
``PAGES``.

The ``-f`` argument to ``new_post`` should be used in the ``ipynb@KERNEL`` format.
It defaults to Python in the version used by Nikola if not specified.

Jupyter Notebooks are also supported in stand-alone listings, if Jupyter
support is enabled site-wide. You must have something for ``.ipynb`` in POSTS
or PAGES for the feature to work.

HTML
````

To use plain HTML in your posts/pages, make sure ``html`` is in your
``COMPILERS``
and that the ``.html`` extension is defined in ``POSTS`` and ``PAGES``.

PHP
```

There are two ways of using PHP within Nikola:

1. To use PHP in your posts/pages (inside your site, with the theme and
   everything), make sure ``php`` is in your ``COMPILERS`` and that the ``.php``
   extension is defined in ``POSTS`` and ``PAGES``.
2. To use PHP as standalone files (without any modifications), put them in
   ``files/`` (or whatever ``FILES_FOLDERS`` is configured to).

Pandoc
``````

To use Pandoc, you must uncomment the entry in ``COMPILERS`` and set the
extensions list to your desired extensions while also removing them from their
original compilers.  The input format is inferred from the extension by Pandoc.

Using Pandoc for reStructuredText, Markdown and other input formats that have a
standalone Nikola plugin is **not recommended** as it disables plugins and
extensions that are usually provided by Nikola.

Shortcodes
----------

This feature is "inspired" (copied wholesale) from `Hugo <https://gohugo.io/extras/shortcodes/>`__ so I will
steal part of their docs too.

A shortcode is a simple snippet inside a content file that Nikola will render using a predefined template or
custom code from a plugin.

To use them from plugins, please see `Extending Nikola <https://getnikola.com/extending.html#shortcodes>`__

Using a shortcode
~~~~~~~~~~~~~~~~~

In your content files, a shortcode can be called by using this form:

.. code:: text

    {{% raw %}}{{% name parameters %}}{{% /raw %}}

Shortcode parameters are space delimited. Parameters with spaces can be quoted (or backslash escaped).

The first word is always the name of the shortcode. Parameters follow the name. Depending upon how the shortcode is defined, the parameters may be named, positional or both. The format for named parameters models that of HTML with the format name="value".

Some shortcodes use or require closing shortcodes. Like HTML, the opening and closing shortcodes match (name only), the closing being prepended with a slash.

Example of a paired shortcode (note that we don't have a highlight shortcode yet ;-):

.. code:: text

    {{% raw %}}{{% highlight python %}} A bunch of code here {{% /highlight %}}{{% /raw %}}

.. admonition:: Shortcodes and reStructuredText

    In reStructuredText shortcodes may fail because docutils turns URL into links and everything breaks.
    For some shortcodes there are alternative docutils directives (example, you can use the media
    **directive** instead of the media shortcode.

    Also, you can use the shortcode **role**:

    .. code:: text

       :sc:`{{% raw %}}{{% shortcode here %}}{{% /raw %}}`

    That role passes text unaltered, so shortcodes behave correctly.


Built-in shortcodes
~~~~~~~~~~~~~~~~~~~

.. warning::

    Some of the shortcodes are implemented as bindings to reST directives. In
    order to use them, you need at least one entry for ``*.rst`` in
    POSTS/PAGES.

chart
    Create charts via PyGal. This is similar to the `chart directive <#chart>`__ except the syntax is adapted to
    shortcodes. This is an example:

    .. code:: text

        {{% raw %}}{{% chart Bar title='Browser usage evolution (in %)'
x_labels='["2002","2003","2004","2005","2006","2007"]' %}}
        'Firefox', [None, None, 0, 16.6, 25, 31]
        'Chrome',  [None, None, None, None, None, None]
        'IE',      [85.8, 84.6, 84.7, 74.5, 66, 58.6]
        'Others',  [14.2, 15.4, 15.3, 8.9, 9, 10.4]
        {{% /chart %}}{{% /raw %}}

    Additionally, you can use a file_data argument which can point to a JSON or YAML file, and will be used for both arguments and data.
    Example:

    .. code:: json

        {
            "x_labels": ["2002","2003","2004","2005","2006","2007"],
            "data": {
                "Firefox": [null, null, 0, 16.6, 25, 31],
                "Chrome": [null, null, null, null, null, null],
                "IE": [85.8, 84.6, 84.7, 74.5, 66, 58.6],
                "Others": [14.2, 15.4, 15.3, 8.9, 9, 10.4]
            }
        }

    Which can be used like this:

    .. code:: text

        {{% raw %}}{{% chart Bar title='Browser usage evolution (in %)' data_file="posts/browsers.json" %}}
        {{% /chart %}}
        {{% /raw %}}

    If the data or any option is available in both the ``data_file`` and the document, the document has priority.

doc
    Will link to a document in the page, see `Doc role for details
    <#doc>`__. Example:

    .. code:: restructuredtext

       {{% raw %}}Take a look at {{% doc %}}my other post <creating-a-theme>{{% /doc %}} about theme creating.{{% /raw %}}

emoji
    Insert an emoji. For example:

    .. code:: text

       {{% raw %}}{{% emoji crying_face %}}{{% /raw %}}

    This generates a ``span`` with ``emoji`` CSS class, so you can style it with a nice font if you want.

gist
    Show GitHub gists. If you know the gist's ID, this will show it in your site:

    {{% raw %}}{{% gist 2395294 %}} {{% /raw %}}

listing
    Used to show a code listing. Example::

        {{% raw %}}{{% listing hello.py python linenumbers=True %}}{{% /raw %}}

    It takes a file name or path, an optional language to highlight, and a linenumbers option to enable/disable line numbers in the output.

media
    Display media embedded from a URL, for example, this will embed a youtube video:

    .. code:: text

        {{% raw %}}{{% media url=https://www.youtube.com/watch?v=Nck6BZga7TQ %}}{{% /raw %}}

    Note that the shortcode won’t work if your compiler turns URLs into clickable links.

post-list
    Will show a list of posts, see the `Post List directive for details <#post-list>`__.

raw
    Passes the content along, mostly used so I can write this damn section and you can see the shortcodes instead
    of them being munged into shortcode **output**. I can't show an example because Inception.

thumbnail
    Display image thumbnails, with optional captions. Examples:

    .. code:: text

        {{% raw %}}{{% thumbnail "/images/foo.png" %}}{{% /thumbnail %}}{{% /raw %}}
        {{% raw %}}{{% thumbnail "/images/foo.png" alt="Foo Image" align="center" %}}{{% /thumbnail %}}{{% /raw %}}
        {{% raw %}}{{% thumbnail "/images/foo.png" imgclass="image-grayscale" figclass="figure-shadow" %}}&lt;p&gt;Image caption&lt;/p&gt;{{% /thumbnail %}}{{% /raw %}}
        {{% raw %}}{{% thumbnail "/images/foo.png" alt="Foo Image" title="Insert title-text joke here" align="right" %}}&lt;p class="caption"&gt;Foo Image (right-aligned) caption&lt;/p&gt;{{% /thumbnail %}}{{% /raw %}}

    The following keyword arguments are supported:

    * alt (alt text for image)
    * align (image alignment, left/center/right)
    * linktitle (title text for the link, shown by e.g. baguetteBox)
    * title (title text for image)
    * imgclass (class for image)
    * figclass (class for figure, used only if you provide a caption)

    Looks similar to the reST thumbnail directive. Caption should be a HTML fragment.

Community shortcodes
~~~~~~~~~~~~~~~~~~~~

Shortcodes created by the community are available in `the shortcodes repository on GitHub <https://github.com/getnikola/shortcodes>`_.

Template-based shortcodes
~~~~~~~~~~~~~~~~~~~~~~~~~

If you put a template in ``shortcodes/`` called ``mycode.tmpl`` then Nikola
will create a shortcode called ``mycode`` you can use. Any options you pass to
the shortcode will be available as variables for that template. Non-keyword
options will be passed in a tuple variable named ``_args``.

The post in which the shortcode is being used is available as the ``post``
variable, so you can access the title as ``post.title``, and data loaded
via the ``data`` field in the metadata using ``post.data(key)``.

If you use the shortcode as paired, then the contents between the paired tags
will be available in the ``data`` variable. If you want to access the Nikola
object, it will be available as ``site``. Use with care :-)

.. note:: Template-based shortcodes use the same template engine as your site’s theme.

See :doc:`extending` for detailed information.

For example, if your ``shortcodes/foo.tmpl`` contains this:

.. code:: text

    This uses the bar variable: ${bar}

And your post contains this:

.. code:: text

    {{% raw %}}{{% foo bar=bla %}}{{% /raw %}}

Then the output file will contain:

.. code:: text

    This uses the bar variable: bla

Finally, you can use a template shortcode without a file, by inserting the
template in the shortcode itself:


.. code:: html+mako

    {{% raw %}}{{% template %}}{{% /raw %}}
    <ul>
    % for foo in bar:
    <li>${foo}</li>
    % endfor
    </ul>
    {{% raw %}}{{% /template %}}{{% /raw %}}


In that case, the template engine used will be your theme's and the arguments you pass,
as well as the global context from your ``conf.py``, are available to the template you
are creating.

You can use anything defined in your configuration's ``GLOBAL_CONTEXT`` as
variables in your shortcode template, with a caveat: Because of an unfortunate
implementation detail (a name conflict), ``data`` is called ``global_data``
when used in a shortcode.

If you have some template code that you want to appear in both a template and
shortcode, you can put the shared code in a separate template and import it in both
places. Shortcodes can import any template inside ``templates/`` and themes,
and call any macros defined in those.

For example, if you define a macro ``foo(x, y)`` in
``templates/shared_sc.tmpl``, you can include ``shared_foo.tmpl`` in
``templates/special_post.tmpl`` and ``shortcodes/foo.tmpl`` and then call the
``${shared_foo.foo(x, y)}`` macro.

The Global Context and Data files
---------------------------------

There is a ``GLOBAL_CONTEXT`` field in your ``conf.py`` where you can
put things you want to make available to your templates.

It will also contain things you put in a ``data/`` directory within your
site. You can use JSON, YAML or TOML files (with the appropriate file
extensions: json/js, yaml/yml, toml/tml) that decode to Python dictionaries.
For example, if you create ``data/foo.json`` containing this:

.. code:: json

   {"bar": "baz"}

Then your templates can use things like ``${data['foo']['bar']}`` and
it will be replaced by "baz".

Individual posts can also have a data file. Those are specified using the
``data`` meta field (path relative to ``conf.py``, can be different in
different post languages). Those are accessible as eg.
``${post.data['bar']}`` in templates. `Template-based shortcodes`_ are a
good idea in this case.

Data files can be useful for eg. auto-generated sites, where users provide
JSON/YAML/TOML files and Nikola generates a large page with data from all data
files. (This is especially useful with some automatic rebuild feature, like
those documented in `Deployment`_)

Data files are also available as ``global_data``, to avoid name conflicts in
shortcodes. (``global_data`` works everywhere.)

Redirections
------------

If you need a page to be available in more than one place, you can define redirections
in your ``conf.py``:

.. code:: python

    # A list of redirection tuples, [("foo/from.html", "/bar/to.html")].
    #
    # A HTML file will be created in output/foo/from.html that redirects
    # to the "/bar/to.html" URL. notice that the "from" side MUST be a
    # relative URL.
    #
    # If you don't need any of these, just set to []

    REDIRECTIONS = [("index.html", "/weblog/index.html")]

It's better if you can do these using your web server's configuration, but if
you can't, this will work.

Configuration
-------------

The configuration file can be used to customize a lot of what Nikola does. Its
syntax is python, but if you don't know the language, it still should not be
terribly hard to grasp.

By default, the ``conf.py`` file in the root of the Nikola website will be used.
You can pass a different configuration file to by using the ``--conf`` command line switch.

The default ``conf.py`` you get with Nikola should be fairly complete, and is quite
commented.

You surely want to edit these options:

.. code:: python

    # Data about this site
    BLOG_AUTHOR = "Your Name"  # (translatable)
    BLOG_TITLE = "Demo Site"  # (translatable)
    SITE_URL = "https://getnikola.com/"
    BLOG_EMAIL = "joe@demo.site"
    BLOG_DESCRIPTION = "This is a demo site for Nikola."  # (translatable)

Some options are marked with a (translatable) comment above or right next to
them.  For those options, two types of values can be provided:

* a string, which will be used for all languages
* a dict of language-value pairs, to have different values in each language

.. note::
    As of version 8.0.3 it is possible to create configuration files which inherit values from other Python files.
    This might be useful if you're working with similar environments.

    Example:
        conf.py:
            .. code:: python

                BLOG_AUTHOR = "Your Name"
                BLOG_TITLE = "Demo Site"
                SITE_URL = "https://yourname.github.io/demo-site
                BLOG_EMAIL = "joe@demo.site"
                BLOG_DESCRIPTION = "This is a demo site for Nikola."

        debug.conf.py:
            .. code:: python

                import conf
                globals().update(vars(conf))
                SITE_URL = "http://localhost:8000/"

            or

            .. code:: python

                from conf import *
                SITE_URL = "http://localhost:8000/"

Customizing Your Site
---------------------

There are lots of things you can do to personalize your website, but let's see
the easy ones!

CSS tweaking
    Using the default configuration, you can create a ``assets/css/custom.css``
    file under ``files/`` or in your theme and then it will be loaded from the
    ``<head>`` blocks of your site pages.  Create it and put your CSS code there,
    for minimal disruption of the provided CSS files.

    If you feel tempted to touch other files in assets, you probably will be better off
    with a :doc:`custom theme <theming>`.

    If you want to use LESS_ or Sass_ for your custom CSS, or the theme you use
    contains LESS or Sass code that you want to override, you will need to install
    the `LESS plugin <https://plugins.getnikola.com/#less>`__ or
    `SASS plugin <https://plugins.getnikola.com/#sass>`__ create a ``less`` or
    ``sass`` directory in your site root, put your ``.less`` or ``.scss`` files
    there and a targets file containing the list of files you want compiled.

.. _LESS: http://lesscss.org/
.. _Sass: http://sass-lang.com/

Template tweaking and creating themes
    If you really want to change the pages radically, you will want to do a
    :doc:`custom theme <theming>`.

Navigation Links
    The ``NAVIGATION_LINKS`` option lets you define what links go in a sidebar or menu
    (depending on your theme) so you can link to important pages, or to other sites.

    The format is a language-indexed dictionary, where each element is a tuple of
    tuples which are one of:

    1. A (url, text) tuple, describing a link
    2. A (((url, text), (url, text), (url, text)), title) tuple, describing a submenu / sublist.

    Example:

    .. code:: python

        NAVIGATION_LINKS = {
            DEFAULT_LANG: (
                ('/archive.html', 'Archives'),
                ('/categories/index.html', 'Tags'),
                ('/rss.xml', 'RSS'),
                ((('/foo', 'FOO'),
                  ('/bar', 'BAR')), 'BAZ'),
            ),
        }

    .. note::

       1. Support for submenus is theme-dependent.  Only one level of
          submenus is supported.

       2. Some themes, including the default Bootstrap theme, may
          present issues if the menu is too large.  (in Bootstrap, the navbar
          can grow too large and cover contents.)

       3. If you link to directories, make sure to follow ``STRIP_INDEXES``.  If
          it’s set to ``True``, end your links with a ``/``, otherwise end them
          with ``/index.html`` — or else they won’t be highlighted when active.

    There’s also ``NAVIGATION_ALT_LINKS``. Themes may display this somewhere
    else, or not at all. Bootstrap puts it on the right side of the header.

    The ``SEARCH_FORM`` option contains the HTML code for a search form based on
    duckduckgo.com which should always work, but feel free to change it to
    something else.

Footer
    ``CONTENT_FOOTER`` is displayed, small at the bottom of all pages, I use it for
    the copyright notice. The default shows a text formed using ``BLOG_AUTHOR``,
    ``BLOG_EMAIL``, the date and ``LICENSE``.  Note you need to use
    ``CONTENT_FOOTER_FORMATS`` instead of regular str.format or %-formatting,
    for compatibility with the translatable settings feature.

BODY_END
    This option lets you define a HTML snippet that will be added at the bottom of body.
    The main usage is a Google analytics snippet or something similar, but you can really
    put anything there. Good place for JavaScript.

SOCIAL_BUTTONS_CODE
    The ``SOCIAL_BUTTONS_CODE`` option lets you define a HTML snippet that will be added
    at the bottom of body. It defaults to a snippet for AddThis, but you can
    really put anything there. See `social_buttons.html` for more details.

Fancy Dates
-----------

Nikola can use various styles for presenting dates.

DATE_FORMAT
    The date format to use if there is no JS or fancy dates are off.  `Compatible with CLDR syntax. <http://cldr.unicode.org/translation/date-time>`_

JS_DATE_FORMAT
    The date format to use if fancy dates are on.  Compatible with ``moment.js`` syntax.

DATE_FANCINESS = 0
    Fancy dates are off, and DATE_FORMAT is used.

DATE_FANCINESS = 1
    Dates are recalculated in user’s timezone.  Requires JavaScript.

DATE_FANCINESS = 2
    Dates are recalculated as relative time (eg. 2 days ago).  Requires JavaScript.

In order to use fancy dates, your theme must support them.  The built-in Bootstrap family supports it, but other themes might not by default.

For Mako:

.. code:: html

    % if date_fanciness != 0:
    <!-- required scripts -- best handled with bundles -->
    <script src="/assets/js/moment-with-locales.min.js"></script>
    <script src="/assets/js/fancydates.js"></script>

    <!-- fancy dates code -->
    <script>
    moment.locale("${momentjs_locales[lang]}");
    fancydates(${date_fanciness}, ${js_date_format});
    </script>
    <!-- end fancy dates code -->
    %endif


For Jinja2:

.. code:: html

    {% if date_fanciness != 0 %}
    <!-- required scripts -- best handled with bundles -->
    <script src="/assets/js/moment-with-locales.min.js"></script>
    <script src="/assets/js/fancydates.js"></script>

    <!-- fancy dates code -->
    <script>
    moment.locale("{{ momentjs_locales[lang] }}");
    fancydates({{ date_fanciness }}, {{ js_date_format }});
    </script>
    <!-- end fancy dates code -->
    {% endif %}


Adding Files
------------

Any files you want to be in ``output/`` but are not generated by Nikola (for
example, ``favicon.ico``) should be placed in ``files/``.  Remember that you
can't have files that collide with files Nikola generates (it will give an
error).

.. admonition:: Important

   Don't put any files manually in ``output/``. Ever. Really.
   Maybe someday Nikola will just wipe ``output/`` (when you run ``nikola check -f --clean-files``) and then you will be sorry. So, please don't do that.

If you want to copy more than one folder of static files into ``output`` you can
change the FILES_FOLDERS option:

.. code:: python

    # One or more folders containing files to be copied as-is into the output.
    # The format is a dictionary of "source" "relative destination".
    # Default is:
    # FILES_FOLDERS = {'files': '' }
    # Which means copy 'files' into 'output'

Custom Themes
-------------

If you prefer to have a custom appearance for your site, and modifying CSS
files and settings (see `Customizing Your Site`_ for details) is not enough,
you can create your own theme. See the :doc:`theming` and
:doc:`creating-a-theme` for more details. You can put them in a ``themes/``
folder and set ``THEME`` to the directory name.  You can also put them in
directories listed in the ``EXTRA_THEMES_DIRS`` configuration variable.

Getting Extra Themes
--------------------

There are a few themes for Nikola. They are available at
the `Themes Index <https://themes.getnikola.com/>`_.
Nikola has a built-in theme download/install mechanism to install those themes
— the ``theme`` command:


.. code:: console

    $ nikola theme -l
    Themes:
    -------
    blogtxt
    bootstrap3-gradients
    ⋮
    ⋮

    $ nikola theme -i blogtxt
    [2013-10-12T16:46:13Z] NOTICE: theme: Downloading:
    https://themes.getnikola.com/v6/blogtxt.zip
    [2013-10-12T16:46:15Z] NOTICE: theme: Extracting: blogtxt into themes

And there you are, you now have themes/blogtxt installed. It's very
rudimentary, but it should work in most cases.

If you create a nice theme, please share it!  You can do it as a pull
request in the  `GitHub repository <https://github.com/getnikola/nikola-themes>`__.

One other option is to tweak an existing theme using a different color scheme,
typography and CSS in general. Nikola provides a ``subtheme`` command
to create a custom theme by downloading free CSS files from http://bootswatch.com
and http://hackerthemes.com


.. code:: console

    $ nikola subtheme -n custom_theme -s flatly -p bootstrap4
    [2013-10-12T16:46:58Z] NOTICE: subtheme: Creating 'custom_theme' theme
    from 'flatly' and 'bootstrap4'
    [2013-10-12T16:46:58Z] NOTICE: subtheme: Downloading:
    http://bootswatch.com/flatly/bootstrap.min.css
    [2013-10-12T16:46:58Z] NOTICE: subtheme: Downloading:
    http://bootswatch.com/flatly/bootstrap.css
    [2013-10-12T16:46:59Z] NOTICE: subtheme: Theme created. Change the THEME setting to "custom_theme" to use it.

Play with it, there's cool stuff there. This feature was suggested by
`clodo <http://elgalpondebanquito.com.ar>`_.

Deployment
----------

If you can specify your deployment procedure as a series of commands, you can
put them in the ``DEPLOY_COMMANDS`` option, and run them with ``nikola deploy``.

You can have multiple deployment presets.  If you run ``nikola deploy``, the
``default`` preset is executed.  You can also specify the names of presets
you want to run (eg. ``nikola deploy default``, multiple presets are allowed).

One caveat is that if any command has a % in it, you should double them.

Here is an example, from my own site's deployment script:

.. code:: python

    DEPLOY_COMMANDS = {'default': [
        'rsync -rav --delete output/ ralsina@lateral.netmanagers.com.ar:/srv/www/lateral',
        'rdiff-backup output ~/blog-backup',
        "links -dump 'http://www.twingly.com/ping2?url=lateral.netmanagers.com.ar'",
    ]}

Other interesting ideas are using
`git as a deployment mechanism <http://toroid.org/ams/git-website-howto>`_ (or any other VCS
for that matter), using `lftp mirror <http://lftp.yar.ru/>`_ or unison, or Dropbox.
Any way you can think of to copy files from one place to another is good enough.

Deploying to GitHub
~~~~~~~~~~~~~~~~~~~

Nikola provides a separate command ``github_deploy`` to deploy your site to
GitHub Pages.  The command builds the site, commits the output to a gh-pages
branch and pushes the output to GitHub.  Nikola uses the `ghp-import command
<https://github.com/davisp/ghp-import>`_ for this.

In order to use this feature, you need to configure a few things first.  Make
sure you have ``nikola`` and ``git`` installed on your PATH.

1. Initialize a Nikola site, if you haven’t already.
2. Initialize a git repository in your Nikola source directory by running:

   .. code:: text

      git init .
      git remote add origin git@github.com:user/repository.git

3. Setup branches and remotes in ``conf.py``:

   * ``GITHUB_DEPLOY_BRANCH`` is the branch where Nikola-generated HTML files
     will be deployed. It should be ``gh-pages`` for project pages and
     ``master`` for user pages (user.github.io).
   * ``GITHUB_SOURCE_BRANCH`` is the branch where your Nikola site source will be
     deployed. We recommend and default to ``src``.
   * ``GITHUB_REMOTE_NAME`` is the remote to which changes are pushed.
   * ``GITHUB_COMMIT_SOURCE`` controls whether or not the source branch is
     automatically committed to and pushed. We recommend setting it to
     ``True``, unless you are automating builds with Travis CI.

4. Create a ``.gitignore`` file. We recommend adding at least the following entries:

   .. code:: text

      cache
      .doit.db
      __pycache__
      output

5. If you set ``GITHUB_COMMIT_SOURCE`` to False, you must switch to your source
   branch and commit to it.  Otherwise, this is done for you.
6. Run ``nikola github_deploy``.  This will build the site, commit the output
   folder to your deploy branch, and push to GitHub.  Your website should be up
   and running within a few minutes.

If you want to use a custom domain, create your ``CNAME`` file in
``files/CNAME`` on the source branch. Nikola will copy it to the
output directory. To add a custom commit message, use the ``-m`` option,
followed by your message.

Automated rebuilds with Travis CI
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you want automated rebuilds and GitHub Pages deployment, allowing you to
blog from anywhere in the world, follow this guide:
`Automating Nikola rebuilds with Travis CI
<https://getnikola.com/blog/automating-nikola-rebuilds-with-travis-ci.html>`_.

Automated rebuilds with GitLab
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

GitLab also offers rebuild automation if you want to use Nikola with GitLab
Pages. Check out the example `Nikola site on GitLab
<https://gitlab.com/pages/nikola>`_.

Comments
--------

While Nikola creates static sites, there is a minimum level of user interaction you
are probably expecting: comments.

Nikola supports several third party comment systems:

* `DISQUS <https://disqus.com>`_
* `IntenseDebate <https://www.intensedebate.com/>`_
* `Muut (Formerly moot) <https://muut.com/>`_
* `Facebook <https://facebook.com/>`_
* `Isso <https://posativ.org/isso/>`_
* `Commento <https://github.com/adtac/commento>`_

By default it will use DISQUS, but you can change by setting ``COMMENT_SYSTEM``
to one of "disqus", "intensedebate", "livefyre", "moot", "facebook", "isso" or "commento"

.. sidebar:: ``COMMENT_SYSTEM_ID``

   The value of ``COMMENT_SYSTEM_ID`` depends on what comment system you
   are using and you can see it in the system's admin interface.

   * For DISQUS, it's called the **shortname**
   * For IntenseDebate, it's the **IntenseDebate site acct**
   * For Muut, it's your **username**
   * For Facebook, you need to `create an app
     <https://developers.facebook.com/apps>`_ (turn off sandbox mode!)
     and get an **App ID**
   * For Isso, it's the URL of your Isso instance (must be world-accessible, encoded with
     Punycode (if using Internationalized Domain Names) and **have a trailing slash**,
     default ``http://localhost:8080/``). You can add custom config options via
     GLOBAL_CONTEXT, eg. ``GLOBAL_CONTEXT['isso_config'] = {"require-author": "true"}``
   * For Commento, it's the URL of the commento instance as required by the ``serverUrl``
     parameter in commento's documentation.

To use comments in a visible site, you should register with the service and
then set the ``COMMENT_SYSTEM_ID`` option.

I recommend 3rd party comments, and specially DISQUS because:

1) It doesn't require any server-side software on your site
2) They offer you a way to export your comments, so you can take
   them with you if you need to.
3) It's free.
4) It's damn nice.

You can disable comments for a post by adding a "nocomments" metadata field to it:

.. code:: restructuredtext

    .. nocomments: True

.. admonition:: DISQUS Support

   In some cases, when you run the test site, you won't see the comments.
   That can be fixed by adding the disqus_developer flag to the templates
   but it's probably more trouble than it's worth.

.. admonition:: Moot Support

   Moot doesn't support comment counts on index pages, and it requires adding
   this to your ``conf.py``:

   .. code-block:: python

        BODY_END = """
        <script src="//cdn.moot.it/1/moot.min.js"></script>
        """
        EXTRA_HEAD_DATA = """
        <link rel="stylesheet" type="text/css" href="//cdn.moot.it/1/moot.css">
        <meta name="viewport" content="width=device-width">
        <meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1">
        """

.. admonition:: Facebook Support

    You need jQuery, but not because Facebook wants it (see Issue
    #639).

Images and Galleries
--------------------

To create an image gallery, all you have to do is add a folder inside ``galleries``,
and put images there. Nikola will take care of creating thumbnails, index page, etc.

If you click on images on a gallery, or on images with links in post, you will
see a bigger image, thanks to the excellent `baguetteBox
<https://feimosi.github.io/baguetteBox.js/>`_.  If don’t want this behavior, add an
``.islink`` class to your link. (The behavior is caused by ``<a
class="reference">`` if you need to use it outside of galleries and reST
thumbnails.)

The gallery pages are generated using the ``gallery.tmpl`` template, and you can
customize it there (you could switch to another lightbox instead of baguetteBox, change
its settings, change the layout, etc.).

Images in galleries may be provided with captions and given a specific
ordering, by creating a file in the gallery directory called ``metadata.yml``.
This YAML file should contain a ``name`` field for each image in the gallery
for which you wish to provide either a caption or specific ordering. You can also
create localized versions (``metadata.xx.yml``).

Only one ``metadata.yml`` is needed per gallery. Here is an example, showing names,
captions and ordering. ``caption`` and ``order`` are given special treatment,
anything else is available to templates, as keys of ``photo_array`` images.

.. code:: yaml

    ---
    name: ready-for-the-acid-wash.jpg
    ---
    name: almost-full.jpg
    caption: The pool is now almost full
    ---
    name: jumping-in.jpg
    caption: We're enjoying the new pool already
    order: 4
    ---
    name: waterline-tiles.jpg
    order: 2
    custom: metadata is supported
    ---


Images to be used in normal posts can be placed in the ``images`` folder. These
images will be processed and have thumbnails created just as for galleries, but will
then be copied directly to the corresponding path in the ``output`` directory, so you
can reference it from whatever page you like, most easily using the ``thumbnail``
reST extension. If you don't want thumbnails, just use the ``files`` folder instead.

The ``conf.py`` options affecting images and gallery pages are these:

.. code:: python

    # One or more folders containing galleries. The format is a dictionary of
    # {"source": "relative_destination"}, where galleries are looked for in
    # "source/" and the results will be located in
    # "OUTPUT_PATH/relative_destination/gallery_name"
    # Default is:
    GALLERY_FOLDERS = {"galleries": "galleries"}
    # More gallery options:
    THUMBNAIL_SIZE = 180
    MAX_IMAGE_SIZE = 1280
    USE_FILENAME_AS_TITLE = True
    EXTRA_IMAGE_EXTENSIONS = []

    # If set to False, it will sort by filename instead. Defaults to True
    GALLERY_SORT_BY_DATE = True

    # Folders containing images to be used in normal posts or pages.
    # IMAGE_FOLDERS is a dictionary of the form {"source": "destination"},
    # where "source" is the folder containing the images to be published, and
    # "destination" is the folder under OUTPUT_PATH containing the images copied
    # to the site. Thumbnail images will be created there as well.
    IMAGE_FOLDERS = {'images': 'images'}

    # Images will be scaled down according to IMAGE_THUMBNAIL_SIZE and MAX_IMAGE_SIZE
    # options, but will have to be referenced manually to be visible on the site
    # (the thumbnail has ``.thumbnail`` added before the file extension by default,
    # but a different naming template can be configured with IMAGE_THUMBNAIL_FORMAT).
    IMAGE_THUMBNAIL_SIZE = 400
    IMAGE_THUMBNAIL_FORMAT = '{name}.thumbnail{ext}'

If you add a reST file in ``galleries/gallery_name/index.txt`` its contents will be
converted to HTML and inserted above the images in the gallery page. The
format is the same as for posts.

If you add some image filenames in ``galleries/gallery_name/exclude.meta``, they
will be excluded in the gallery page.

If ``USE_FILENAME_AS_TITLE`` is True the filename (parsed as a readable string)
is used as the photo caption. If the filename starts with a number, it will
be stripped. For example ``03_an_amazing_sunrise.jpg`` will be render as *An amazing sunrise*.

Here is a `demo gallery </galleries/demo>`_ of historic, public domain Nikola
Tesla pictures taken from `this site <http://kerryr.net/pioneers/gallery/tesla.htm>`_.

Embedding Images
~~~~~~~~~~~~~~~~

Assuming that you have your pictures stored in a folder called ``images`` (as configured above),
you can embed the same in your posts with the following reST directive:

.. code:: rest

    .. image:: /images/tesla.jpg

Which is equivalent to the following HTML code:

.. code:: html

   <img src="/images/tesla.jpg">

Please take note of the leading forward-slash ``/`` which refers to the root
output directory. (Make sure to use this even if you’re not deploying to
web server root.)

You can also use thumbnails with the ``.. thumbnail::`` reST directive. For
more details, and equivalent HTML code, see `Thumbnails`_.

Handling EXIF Data
------------------

Your images contain a certain amount of extra data besides the image itself,
called the `EXIF metadata. <https://en.wikipedia.org/wiki/Exchangeable_image_file_format>`__
It contains information about the camera you used to take the picture, when it was taken,
and maybe even the location where it was taken.

This is both useful, because you can use it in some apps to locate all the pictures taken
in a certain place, or with a certain camera, but also, since the pictures Nikola
publishes are visible to anyone on the Internet, a privacy risk worth considering
(Imagine if you post pictures taken at home with GPS info, you are publishing your
home address!)

Nikola has some support for managing it, so let's go through a few scenarios to
see which one you prefer.

Strip all EXIF data
~~~~~~~~~~~~~~~~~~~

Do this if you want to be absolutely sure that no sensitive information should ever leak:

.. code:: python

    PRESERVE_EXIF_DATA = False
    EXIF_WHITELIST = {}

Preserve all EXIF data
~~~~~~~~~~~~~~~~~~~~~~

Do this if you really don't mind people knowing where pictures were taken, or camera settings:

.. code:: python

    PRESERVE_EXIF_DATA = True
    EXIF_WHITELIST = {'*': '*'}

Preserve some EXIF data
~~~~~~~~~~~~~~~~~~~~~~~

Do this if you really know what you are doing. EXIF data comes separated in a few IFD blocks.
The most common ones are:

0th
   Information about the image itself

Exif
   Information about the camera and the image

1st
   Information about embedded thumbnails (usually nothing)

thumbnail
   An embedded thumbnail, in JPEG format (usually nothing)

GPS
   Geolocation information about the image

Interop
   Not too interesting at this point.

Each IFD in turn contains a number of tags. For example, 0th contains a ImageWidth tag.
You can tell Nikola exactly which IFDs to keep, and within each IFD, which tags to keep,
using the EXIF_WHITELIST option.

Let's see an example:

.. code:: python

    PRESERVE_EXIF_DATA = True
    EXIF_WHITELIST = {
        "0th": ["Orientation", "ImageWidth", "ImageLength"],
        "Interop": "*",
    }

So, we preserve EXIF data, and the whitelisted IFDs are "0th" and "Interop". That means
GPS, for example, will be totally deleted.

Then, for the Interop IFD, we keep everything, and for the 0th IFD we only keep three tags,
listed there.

There is a huge number of EXIF tags, described in `the standard <http://www.cipa.jp/std/documents/e/DC-008-2012_E.pdf>`__


Handling ICC Profiles
---------------------

Your images may contain `ICC profiles. <https://en.wikipedia.org/wiki/ICC_profile>`__  These describe the color space in which the images were created or captured.

Most desktop web browsers can use embedded ICC profiles to display images accurately.  As of early 2018 few mobile browsers consider ICC profiles when displaying images.  A notable exception is Safari on iOS.

By default Nikola strips out ICC profiles when preparing images for your posts and galleries.  If you want Nikola to preserve ICC profiles, add this in your ``conf.py``:

.. code:: python

  PRESERVE_ICC_PROFILES = True

You may wish to do this if, for example, your site contains JPEG images that use a wide-gamut profile such as "Display P3".


Post Processing Filters
-----------------------

You can apply post processing to the files in your site, in order to optimize them
or change them in arbitrary ways. For example, you may want to compress all CSS
and JS files using yui-compressor.

To do that, you can use the provided helper adding this in your ``conf.py``:

.. code:: python

  FILTERS = {
    ".css": ["filters.yui_compressor"],
    ".js": ["filters.yui_compressor"],
  }

Where ``"filters.yui_compressor"`` points to a helper function provided by Nikola in the
``filters`` module. You can replace that with strings describing command lines, or
arbitrary python functions.

If there's any specific thing you expect to be generally useful as a filter, contact
me and I will add it to the filters library so that more people use it.

The currently available filters are:

.. sidebar:: Creating your own filters

   You can use any program name that works in place as a filter, like ``sed -i``
   and you can use arbitrary Python functions as filters, too.

   If your program doesn't run in-place, then you can use Nikola's ``runinplace`` function (from the ``filters`` module).
   For example, this is how the yui_compressor filter is implemented:

   .. code-block:: python

      from nikola.filters import runinplace
      def yui_compressor(infile):
          return runinplace(r'yui-compressor --nomunge %1 -o %2', infile)

   You can turn any function into a filter using ``apply_to_text_file`` (for
   text files to be read in UTF-8) and ``apply_to_binary_file`` (for files to
   be read in binary mode).

   As a silly example, this would make everything uppercase and totally break
   your website:

   .. code-block:: python

      import string
      from nikola.filters import apply_to_text_file
      FILTERS = {
        ".html": [apply_to_text_file(string.upper)]
      }

filters.html_tidy_nowrap
   Prettify HTML 5 documents with `tidy5 <http://www.html-tidy.org/>`_

filters.html_tidy_wrap
   Prettify HTML 5 documents wrapped at 80 characters with `tidy5 <http://www.html-tidy.org/>`_

filters.html_tidy_wrap_attr
   Prettify HTML 5 documents and wrap lines and attributes with `tidy5 <http://www.html-tidy.org/>`_

filters.html_tidy_mini
   Minify HTML 5 into smaller documents with `tidy5 <http://www.html-tidy.org/>`_

filters.html_tidy_withconfig
   Run `tidy5 <http://www.html-tidy.org/>`_ with ``tidy5.conf`` as the config file (supplied by user)

filters.html5lib_minify
   Minify HTML5 using html5lib_minify

filters.html5lib_xmllike
   Format using html5lib

filters.typogrify
   Improve typography using `typogrify <http://static.mintchaos.com/projects/typogrify/>`__

filters.typogrify_sans_widont
   Same as typogrify without the widont filter

filters.minify_lines
   **THIS FILTER HAS BEEN TURNED INTO A NOOP** and currently does nothing.

filters.normalize_html
   Pass HTML through LXML to normalize it. For example, it will resolve ``&quot;`` to actual
   quotes. Usually not needed.

filters.yui_compressor
   Compress CSS/JavaScript using `YUI compressor <http://yui.github.io/yuicompressor/>`_

filters.closure_compiler
   Compile, compress, and optimize JavaScript `Google Closure Compiler <https://developers.google.com/closure/compiler/>`_

filters.optipng
   Compress PNG files using `optipng <http://optipng.sourceforge.net/>`_

filters.jpegoptim
   Compress JPEG files using `jpegoptim <http://www.kokkonen.net/tjko/projects.html>`_

filters.cssminify
   Minify CSS using http://cssminifier.com/ (requires Internet access)

filters.jsminify
   Minify JS using http://javascript-minifier.com/ (requires Internet access)

filters.jsonminify
   Minify JSON files (strip whitespace and use minimal separators).

filters.xmlminify
   Minify XML files. Suitable for Nikola’s sitemaps and Atom feeds.

filters.add_header_permalinks
   Add links next to every header, Sphinx-style. You will need to add styling for the `headerlink` class,
   in `custom.css`, for example:

   .. code:: css

      /* Header permalinks */
      h1:hover .headerlink, h2:hover .headerlink,
      h3:hover .headerlink, h4:hover .headerlink,
      h5:hover .headerlink, h6:hover .headerlink {
          display: inline;
      }

      .headerlink {
          display: none;
          color: #ddd;
          margin-left: 0.2em;
          padding: 0 0.2em;
      }

      .headerlink:hover {
          opacity: 1;
          background: #ddd;
          color: #000;
          text-decoration: none;
      }

   Additionally, you can provide a custom list of XPath expressions which should be used for finding headers (``{hx}`` is replaced by headers h1 through h6).
   This is required if you use a custom theme that does not use ``"e-content entry-content"`` as a class for post and page contents.

   .. code:: python

      # Default value:
      HEADER_PERMALINKS_XPATH_LIST = ['*//div[@class="e-content entry-content"]//{hx}']
      # Include *every* header (not recommended):
      # HEADER_PERMALINKS_XPATH_LIST = ['*//{hx}']


filters.deduplicate_ids
   Prevent duplicated IDs in HTML output. An incrementing counter is added to
   offending IDs. If used alongside ``add_header_permalinks``, it will fix
   those links (it must run **after** that filter)

   IDs are numbered from the bottom up, which is useful for indexes (updates
   appear at the top). There are exceptions, which may be configured using
   ``DEDUPLICATE_IDS_TOP_CLASSES`` — if any of those classes appears sin the
   document, the IDs are rewritten top-down, which is useful for posts/pages
   (updates appear at the bottom).

   Note that in rare cases, permalinks might not always be *permanent* in case
   of edits.

   .. code:: python

      DEDUPLICATE_IDS_TOP_CLASSES = ('postpage', 'storypage')

    You can also use a file blacklist (``HEADER_PERMALINKS_FILE_BLACKLIST``),
    useful for some index pages. Paths include the output directory (eg.
    ``output/index.html``)


You can apply filters to specific posts or pages by using the ``filters`` metadata field:

.. code:: restructuredtext

    .. filters: filters.html_tidy_nowrap, "sed s/foo/bar"

Optimizing Your Website
-----------------------

One of the main goals of Nikola is to make your site fast and light. So here are a few
tips we have found when setting up Nikola with Apache. If you have more, or
different ones, or about other web servers, please share!

1. Use a speed testing tool. I used Yahoo's YSlow but you can use any of them, and
   it's probably a good idea to use more than one.

2. Enable compression in Apache:

   .. code:: apache

      AddOutputFilterByType DEFLATE text/html text/plain text/xml text/css text/javascript

3. If even after you did the previous step the CSS files are not sent compressed:

   .. code:: apache

      AddType text/css .css

4. Optionally you can create static compressed copies and save some CPU on your server
   with the GZIP_FILES option in Nikola.

5. The bundles Nikola plugin can drastically decrease the number of CSS and JS files your site fetches.

6. Through the filters feature, you can run your files through arbitrary commands, so that images
   are recompressed, JavaScript is minimized, etc.

7. The USE_CDN option offloads standard JavaScript and CSS files to a CDN so they are not
   downloaded from your server.

Math
----

Nikola supports math input via MathJax (by default) or KaTeX.  It is activated
via the math roles and directives of reStructuredText and the usual LaTeX
delimiters for other input formats.

Configuration
~~~~~~~~~~~~~

Nikola uses MathJax by default. If you want to use KaTeX (faster and prettier,
but may not support every feature yet), set ``USE_KATEX = True`` in
``conf.py``.

To use mathematics in a post, you **must** set the ``has_math`` metadata field
to ``true``. (Exception: posts that are Jupyter Notebooks are automatically
marked as math)

.. Note to editors: the paragraph below uses U+200B, zero-width space. Don’t break it.

By default, Nikola will accept ``\​(...\​)`` for inline math; ``\​[...\​]`` and
``$​$...$​$`` for display math. If you want to use the old ``$...$`` syntax as well
(which may conflict with running text!), you need to use special config for
your renderer:

.. code:: python

   MATHJAX_CONFIG = """
   <script type="text/x-mathjax-config">
   MathJax.Hub.Config({
       tex2jax: {
           inlineMath: [ ['$','$'], ["\\\(","\\\)"] ],
           displayMath: [ ['$$','$$'], ["\\\[","\\\]"] ],
           processEscapes: true
       },
       displayAlign: 'center', // Change this to 'left' if you want left-aligned equations.
       "HTML-CSS": {
           styles: {'.MathJax_Display': {"margin": 0}}
       }
   });
   </script>
   """

   KATEX_AUTO_RENDER = """
   delimiters: [
       {left: "$$", right: "$$", display: true},
       {left: "\\\[", right: "\\\]", display: true},
       {left: "$", right: "$", display: false},
       {left: "\\\(", right: "\\\)", display: false}
   ]
   """

*(Note: the previous paragraph uses invisible characters to prevent rendering
TeX for display, so don’t copy the examples with three dots to your posts)*

Inline usage
~~~~~~~~~~~~

Inline mathematics are produced using the reST `math` **role** or the LaTeX
backslash-parentheses delimiters:

Euler’s formula: :math:`e^{ix} = \cos x + i\sin x`

In reST:

.. code:: restructuredtext

    Euler’s formula: :math:`e^{ix} = \cos x + i\sin x`

In HTML and other input formats:

.. code:: text

    Euler’s formula: \(e^{ix} = \cos x + i\sin x\)

Note that some input formats (including Markdown) require using **double
backslashes** in the delimiters (``\\(inline math\\)``). Please check your
output first before reporting bugs.

Display usage
~~~~~~~~~~~~~

Display mathematics are produced using the reST `math` **directive** or the
LaTeX backslash-brackets delimiters:

.. math::

   \int \frac{dx}{1+ax}=\frac{1}{a}\ln(1+ax)+C


In reST:

.. code:: restructuredtext

   .. math::

      \int \frac{dx}{1+ax}=\frac{1}{a}\ln(1+ax)+C

In HTML and other input formats:

.. code:: text

    \[\int \frac{dx}{1+ax}=\frac{1}{a}\ln(1+ax)+C\]

Note that some input formats (including Markdown) require using **double
backslashes** in the delimiters (``\\[display math\\]``). Please check your
output first before reporting bugs.


reStructuredText Extensions
---------------------------

Nikola includes support for a few directives and roles that are not part of docutils, but which
we think are handy for website development.

Includes
~~~~~~~~

Nikola supports the standard reStructuredText ``include`` directive, but with a
catch: filenames are relative to **Nikola site root** (directory with ``conf.py``)
instead of the post location (eg. ``posts/`` directory)!

Media
~~~~~

This directive lets you embed media from a variety of sites automatically by just passing the
URL of the page.  For example here are two random videos:

.. code:: restructuredtext

    .. media:: http://vimeo.com/72425090

    .. media:: http://www.youtube.com/watch?v=wyRpAat5oz0

It supports Instagram, Flickr, Github gists, Funny or Die, and dozens more, thanks to `Micawber <https://github.com/coleifer/micawber>`_

YouTube
~~~~~~~

To link to a YouTube video, you need the id of the video. For example, if the
URL of the video is http://www.youtube.com/watch?v=8N_tupPBtWQ what you need is
**8N_tupPBtWQ**

Once you have that, all you need to do is:

.. code:: restructuredtext

    .. youtube:: 8N_tupPBtWQ

Supported options: ``height``, ``width``, ``align`` (one of ``left``,
``center``, ``right``) — all are optional. Example:

.. code:: restructuredtext

    .. youtube:: 8N_tupPBtWQ
       :align: center

Vimeo
~~~~~

To link to a Vimeo video, you need the id of the video. For example, if the
URL of the video is http://www.vimeo.com/20241459 then the id is **20241459**

Once you have that, all you need to do is:

.. code:: restructuredtext

    .. vimeo:: 20241459

If you have internet connectivity when generating your site, the height and width of
the embedded player will be set to the native height and width of the video.
You can override this if you wish:

.. code:: restructuredtext

    .. vimeo:: 20241459
       :height: 240
       :width: 320

Supported options: ``height``, ``width``, ``align`` (one of ``left``,
``center``, ``right``) — all are optional.

Soundcloud
~~~~~~~~~~

This directive lets you share music from http://soundcloud.com You first need to get the
ID for the piece, which you can find in the "share" link. For example, if the
WordPress code starts like this:

.. code:: text

    [soundcloud url="http://api.soundcloud.com/tracks/78131362" …/]

The ID is 78131362 and you can embed the audio with this:

.. code:: restructuredtext

    .. soundcloud:: 78131362

You can also embed playlists, via the `soundcloud_playlist` directive which works the same way.

    .. soundcloud_playlist:: 9411706

Supported options: ``height``, ``width``, ``align`` (one of ``left``,
``center``, ``right``) — all are optional.

Code
~~~~

The ``code`` directive has been included in docutils since version 0.9 and now
replaces Nikola's ``code-block`` directive. To ease the transition, two aliases
for ``code`` directive are provided: ``code-block`` and ``sourcecode``:

.. code:: restructuredtext

    .. code-block:: python
       :number-lines:

       print("Our virtues and our failings are inseparable")

Listing
~~~~~~~

To use this, you have to put your source code files inside ``listings`` or whatever folders
your ``LISTINGS_FOLDERS`` variable is set to fetch files from. Assuming you have a ``foo.py``
inside one of these folders:

.. code:: restructuredtext

    .. listing:: foo.py python

Will include the source code from ``foo.py``, highlight its syntax in python mode,
and also create a ``listings/foo.py.html`` page (or in another directory, depending on
``LISTINGS_FOLDER``) and the listing will have a title linking to it.

The stand-alone ``listings/`` pages also support Jupyter notebooks, if they are
supported site-wide. You must have something for ``.ipynb`` in POSTS or PAGES
for the feature to work.

Listings support the same options `reST includes`__ support (including
various options for controlling which parts of the file are included), and also
a ``linenos`` option for Sphinx compatibility.

The ``LISTINGS_FOLDER`` configuration variable allows to specify a list of folders where
to fetch listings from together with subfolder of the ``output`` folder where the
processed listings should be put in. The default is, ``LISTINGS_FOLDERS = {'listings': 'listings'}``,
which means that all source code files in ``listings`` will be taken and stored in ``output/listings``.
Extending ``LISTINGS_FOLDERS`` to ``{'listings': 'listings', 'code': 'formatted-code'}``
will additionally process all source code files in ``code`` and put the results into
``output/formatted-code``.

__ http://docutils.sourceforge.net/docs/ref/rst/directives.html#including-an-external-document-fragment

.. note::

   Formerly, ``start-at`` and ``end-at`` options were supported; however,
   they do not work anymore (since v6.1.0) and you should now use ``start-after``
   and ``end-before``, respectively.  You can also use ``start-line`` and
   ``end-line``.

Gist
~~~~

You can easily embed GitHub gists with this directive, like this:

.. code:: restructuredtext

    .. gist:: 2395294

Producing this:

.. gist:: 2395294

This degrades gracefully if the browser doesn't support JavaScript.

Thumbnails
~~~~~~~~~~

To include an image placed in the ``images`` folder (or other folders defined in ``IMAGE_FOLDERS``), use the
``thumbnail`` directive, like this:

.. code:: restructuredtext

    .. thumbnail:: /images/tesla.jpg
       :alt: Nikola Tesla

The small thumbnail will be placed in the page, and it will be linked to the bigger
version of the image when clicked, using
`baguetteBox <https://feimosi.github.io/baguetteBox.js/>`_ by default. All options supported by
the reST `image <http://docutils.sourceforge.net/docs/ref/rst/directives.html#image>`_
directive are supported (except ``target``). Providing ``alt`` is recommended,
as this is the image caption. If a body element is provided, the thumbnail will
mimic the behavior of the `figure
<http://docutils.sourceforge.net/docs/ref/rst/directives.html#figure>`_
directive instead:

.. code:: restructuredtext

    .. thumbnail:: /images/tesla.jpg
       :alt: Nikola Tesla

       Nikola Tesla, the man that invented the 20th century.

If you want to include a thumbnail in a non-reST post, you need to produce at
least this basic HTML:

.. code:: html

   <a class="reference" href="images/tesla.jpg" alt="Nikola Tesla"><img src="images/tesla.thumbnail.jpg"></a>

Chart
~~~~~

This directive is a thin wrapper around `Pygal <http://pygal.org/>`_ and will produce charts
as SVG files embedded directly in your pages.

Here's an example of how it works:

.. code:: restructuredtext

            .. chart:: Bar
               :title: 'Browser usage evolution (in %)'
               :x_labels: ["2002", "2003", "2004", "2005", "2006", "2007"]

               'Firefox', [None, None, 0, 16.6, 25, 31]
               'Chrome',  [None, None, None, None, None, None]
               'IE',      [85.8, 84.6, 84.7, 74.5, 66, 58.6]
               'Others',  [14.2, 15.4, 15.3, 8.9, 9, 10.4]

The argument passed next to the directive (Bar in that example) is the type of chart, and can be one of
Line, StackedLine, Bar, StackedBar, HorizontalBar, XY, DateY, Pie, Radar, Dot, Funnel, Gauge, Pyramid. For
examples of what each kind of graph is, `check here <http://pygal.org/en/stable/documentation/types/index.html>`_

It can take *a lot* of options to let you customize the charts (in the example, title and x_labels).
You can use any option described in `the pygal docs <http://pygal.org/en/stable/documentation/configuration/chart.html>`_

Finally, the content of the directive is the actual data, in the form of a label and
a list of values, one series per line.

You can also specify a ``:data_file:`` option as described in the documentation for the chart shortcut.

Doc
~~~

This role is useful to make links to other post or page inside the same site.

Here's an example:

.. code:: restructuredtext

    Take a look at :doc:`my other post <creating-a-theme>` about theme creating.

In this case we are giving the portion of text we want to link. So, the result will be:

    Take a look at :doc:`my other post <creating-a-theme>` about theme creating.

If we want to use the post's title as the link's text, just do:

.. code:: restructuredtext

    Take a look at :doc:`creating-a-theme` to know how to do it.

and it will produce:

    Take a look at :doc:`creating-a-theme` to know how to do it.

The reference in angular brackets should be the `slug` for the target page. It supports a fragment, so
things like ``<creating-a-theme#starting-from-somewhere>`` should work. You can also use the title, and
Nikola will slugify it for you, so ``Creating a theme`` is also supported.

Keep in mind that the important thing is the slug. No attempt is made to check if the fragment points to
an existing location in the page, and references that don't match any page's slugs will cause warnings.

Post List
~~~~~~~~~

.. WARNING::

   Any post or page that uses this directive will be considered out of date,
   every time a post is added or deleted, causing maybe unnecessary rebuilds.

   On the other hand, it will sometimes **not** be considered out of date if
   a post content changes, so it can sometimes be shown outdated, in those
   cases, use ``nikola build -a`` to force a total rebuild.


This directive can be used to generate a list of posts. You could use it, for
example, to make a list of the latest 5 blog posts, or a list of all blog posts
with the tag ``nikola``:

.. code:: restructuredtext

   Here are my 5 latest and greatest blog posts:

   .. post-list::
      :stop: 5

   These are all my posts about Nikola:

   .. post-list::
      :tags: nikola

Using shortcode syntax (for other compilers):

.. code:: text

   {{% raw %}}{{% post-list stop=5 %}}{{% /post-list %}}{{% /raw %}}

The following options are recognized:

* ``start`` : integer
      The index of the first post to show.
      A negative value like ``-3`` will show the *last* three posts in the
      post-list.
      Defaults to None.

* ``stop`` : integer
      The index of the last post to show.
      A value negative value like ``-1`` will show every post, but not the
      *last* in the post-list.
      Defaults to None.

* ``reverse`` : flag
      Reverse the order of the post-list.
      Defaults is to not reverse the order of posts.

* ``sort``: string
      Sort post list by one of each post's attributes, usually ``title`` or a
      custom ``priority``.  Defaults to None (chronological sorting).

* ``date``: string
      Show posts that match date range specified by this option. Format:

      * comma-separated clauses (AND)
      * clause: attribute comparison_operator value (spaces optional)
          * attribute: year, month, day, hour, month, second, weekday, isoweekday; or empty for full datetime
          * comparison_operator: == != <= >= < >
          * value: integer, 'now' or dateutil-compatible date input

* ``tags`` : string [, string...]
      Filter posts to show only posts having at least one of the ``tags``.
      Defaults to None.

* ``require_all_tags`` : flag
    Change tag filter behaviour to show only posts that have all specified ``tags``.
    Defaults to False.

* ``categories`` : string [, string...]
      Filter posts to show only posts having one of the ``categories``.
      Defaults to None.

* ``slugs`` : string [, string...]
      Filter posts to show only posts having at least one of the ``slugs``.
      Defaults to None.

* ``post_type`` (or ``type``) : string
      Show only ``posts``, ``pages`` or ``all``.
      Replaces ``all``. Defaults to ``posts``.

* ``all`` : flag
      (deprecated, use ``post_type`` instead)
      Shows all posts and pages in the post list.  Defaults to show only posts.

* ``lang`` : string
      The language of post *titles* and *links*.
      Defaults to default language.

* ``template`` : string
      The name of an alternative template to render the post-list.
      Defaults to ``post_list_directive.tmpl``

* ``id`` : string
      A manual id for the post list.
      Defaults to a random name composed by ``'post_list_' + uuid.uuid4().hex``.

The post list directive uses the ``post_list_directive.tmpl`` template file (or
another one, if you use the ``template`` option) to generate the list's HTML. By
default, this is an unordered list with dates and clickable post titles. See
the template file in Nikola's base theme for an example of how this works.

The list may fail to update in some cases, please run ``nikola build -a`` with
the appropriate path if this happens.

We recommend using pages with dates in the past (1970-01-01) to avoid
dependency issues.

If you are using this as a shortcode, flags (``reverse``, ``all``) are meant to be used
with a ``True`` argument, eg. ``all=True``.

.. sidebar:: Docutils Configuration

   ReStructured Text is "compiled" by docutils, which supports a number of
   configuration options. It would be difficult to integrate them all into
   Nikola's configuration, so you can just put a ``docutils.conf`` next
   to your ``conf.py`` and any settings in its ``[nikola]`` section will be used.

   More information in the `docutils configuration reference <http://docutils.sourceforge.net/docs/user/config.html>`__


Importing your WordPress site into Nikola
-----------------------------------------

If you like Nikola, and want to start using it, but you have a WordPress blog, Nikola
supports importing it. Here are the steps to do it:

1. Get an XML dump of your site [#]_
2. ``nikola import_wordpress mysite.wordpress.2012-12-20.xml``

After some time, this will create a ``new_site`` folder with all your data. It currently supports
the following:

* All your posts and pages
* Keeps “draft” status
* Your tags and categories
* Imports your attachments and fixes links to point to the right places
* Will try to add redirects that send the old post URLs to the new ones
* Will give you a URL map so you know where each old post was

  This is also useful for DISQUS thread migration, or server-based 301
  redirects!

* Allows you to export your comments with each post
* Exports information on attachments per post
* There are different methods to transfer the content of your posts:

  - You can convert them to HTML with the WordPress page compiler plugin
    for Nikola. This will format the posts including supported shortcodes
    the same way as WordPress does. Use the ``--transform-to-html`` option
    to convert your posts to HTML.

    If you use this option, you do not need to install the plugin
    permanently. You can ask Nikola to install the plugin into the subdirectory
    ``plugins`` of the current working directory by specifying
    the ``--install-wordpress-compiler`` option.

  - You can leave the posts the way they are and use the WordPress page
    compiler plugin to render them when building your new blog. This also
    allows you to create new posts using the WordPress syntax, or to manually
    add more shortcode plugins later. Use the ``--use-wordpress-compiler``
    option to not touch your posts.

    If you want to use this option, you have to install the plugin permanently.
    You can ask Nikola to install the plugin into your new site by specifying
    the ``--install-wordpress-compiler`` option.

  - You can let Nikola convert your posts to Markdown. This is *not* error
    free, because WordPress uses some unholy mix of HTML and strange things.
    This is the default option and requires no plugins.

  You will find your old posts in ``new_site/posts/post-title.html`` in the first case,
  ``new_site/posts/post-title.wp`` in the second case or ``new_site/posts/post-title.md``
  in the last case if you need to edit or fix any of them.

  Please note that the page compiler currently only supports the ``[code]`` shortcode,
  but other shortcodes can be supported via plugins.

  Also note that the WordPress page compiler is licensed under GPL v2 since
  it uses code from WordPress itself, while Nikola is licensed under the more
  liberal MIT license.

This feature is a work in progress, and the only way to improve it is to have it used for
as many sites as possible and make it work better each time, so we are happy to get requests
about it.

.. [#] The dump needs to be in 1.2 format. You can check by reading it, it should say
       ``xmlns:excerpt="http://wordpress.org/export/1.2/excerpt/"`` near the top of the
       file. If it says ``1.1`` instead of ``1.2`` you will have to update your
       WordPress before dumping.

       Other versions may or may not work.

Importing to a custom location or into an existing site
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It is possible to either import into a location you desire or into an already existing Nikola site.
To do so you can specify a location after the dump:

.. code:: console

    $ nikola import_wordpress mysite.wordpress.2012-12-20.xml -o import_location

With this command Nikola will import into the folder ``import_location``.

If the folder already exists Nikola will not overwrite an existing ``conf.py``.
Instead a new file with a timestamp at the end of the filename will be created.

Using Twitter Cards
-------------------

Nikola supports Twitter Card summaries, but they are disabled by default.

Twitter Cards enable you to show additional information in Tweets that link
to your content.
Nikola supports `Twitter Cards <https://dev.twitter.com/docs/cards>`_.
They are implemented to use *Open Graph* tags whenever possible.

Images displayed come from the `previewimage` meta tag.

You can specify the card type by using the `card` parameter in TWITTER_CARD.

To enable and configure your use of Twitter Cards, please modify the
corresponding lines in your ``conf.py``:

.. code-block:: python

    TWITTER_CARD = {
        'use_twitter_cards': True,  # enable Twitter Cards
        'card': 'summary',          # Card type, you can also use 'summary_large_image',
                                    # see https://dev.twitter.com/cards/types
        'site': '@website',         # twitter nick for the website
        'creator': '@username',     # Username for the content creator / author.
    }

Custom Plugins
--------------

You can create your own plugins (see :doc:`extending`) and use them in your own
site by putting them in a ``plugins/`` folder.  You can also put them in
directories listed in the ``EXTRA_PLUGINS_DIRS`` configuration variable.


Getting Extra Plugins
---------------------

If you want extra plugins, there is also the `Plugins Index <https://plugins.getnikola.com/>`_.

Similarly to themes, there is a nice, built-in command to manage them —
``plugin``:

.. code:: console

    $ nikola plugin -l
    Plugins:
    --------
    helloworld
    tags
    ⋮
    ⋮

    $ nikola plugin --install helloworld
    [2013-10-12T16:51:56Z] NOTICE: install_plugin: Downloading: https://plugins.getnikola.com/v6/helloworld.zip
    [2013-10-12T16:51:58Z] NOTICE: install_plugin: Extracting: helloworld into plugins
    plugins/helloworld/requirements.txt
    [2013-10-12T16:51:58Z] NOTICE: install_plugin: This plugin has Python dependencies.
    [2013-10-12T16:51:58Z] NOTICE: install_plugin: Installing dependencies with pip...
    ⋮
    ⋮
    [2013-10-12T16:51:59Z] NOTICE: install_plugin: Dependency installation succeeded.
    [2013-10-12T16:51:59Z] NOTICE: install_plugin: This plugin has a sample config file.
    Contents of the conf.py.sample file:

        # Should the Hello World plugin say “BYE” instead?
        BYE_WORLD = False

Then you also can uninstall your plugins:

.. code:: console

    $ nikola plugin --uninstall tags
    [2014-04-15T08:59:24Z] WARNING: plugin: About to uninstall plugin: tags
    [2014-04-15T08:59:24Z] WARNING: plugin: This will delete /home/ralsina/foo/plugins/tags
    Are you sure? [y/n] y
    [2014-04-15T08:59:26Z] WARNING: plugin: Removing /home/ralsina/foo/plugins/tags

And upgrade them:

.. code:: console

    $ nikola plugin --upgrade
    [2014-04-15T09:00:18Z] WARNING: plugin: This is not very smart, it just reinstalls some plugins and hopes for the best
    Will upgrade 1 plugins: graphviz
    Upgrading graphviz
    [2014-04-15T09:00:20Z] INFO: plugin: Downloading: https://plugins.getnikola.com/v7/graphviz.zip
    [2014-04-15T09:00:20Z] INFO: plugin: Extracting: graphviz into /home/ralsina/.nikola/plugins/
    [2014-04-15T09:00:20Z] NOTICE: plugin: This plugin has third-party dependencies you need to install manually.
    Contents of the requirements-nonpy.txt file:

        Graphviz
            http://www.graphviz.org/

    You have to install those yourself or through a package manager.

You can also share plugins you created with the community!  Visit the
`GitHub repository <https://github.com/getnikola/plugins>`__ to find out more.

You can use the plugins in this repository without installing them into your
site, by cloning the repository and adding the path of the plugins directory to
the ``EXTRA_PLUGINS_DIRS`` list in your configuration.

Advanced Features
-----------------

Debugging
~~~~~~~~~

For pdb debugging in Nikola, you should use ``doit.tools.set_trace()`` instead
of the usual pdb call.  By default, doit (and thus Nikola) redirects stdout and
stderr.  Thus, you must use the different call.  (Alternatively, you could run
with ``nikola build -v 2``, which disables the redirections.)

To show more logging messages, as well as full tracebacks, you need to set an
environment variable: ``NIKOLA_DEBUG=1``. If you want to only see tracebacks,
set ``NIKOLA_SHOW_TRACEBACKS=1``.

Shell Tab Completion
~~~~~~~~~~~~~~~~~~~~

Since Nikola is a command line tool, and this is the 21st century, it's handy to have smart tab-completion
so that you don't have to type the full commands.

To enable this, you can use the ``nikola tabcompletion`` command like this,
depending on your shell:

.. code:: console

    $ nikola tabcompletion --shell bash --hardcode-tasks > _nikola_bash
    $ nikola tabcompletion --shell zsh --hardcode-tasks > _nikola_zsh

The ``--hardcode-tasks`` adds tasks to the completion and may need updating periodically.

Please refer to your shell’s documentation for help on how to use those files.

License
-------

Nikola is released under the `MIT license <https://getnikola.com/license.html>`_, which is a free software license. Some
components shipped along with Nikola, or required by it are released under
other licenses.

If you are not familiar with free software licensing, here is a brief
explanation (this is NOT legal advice): In general, you can do pretty much
anything you want — including modifying Nikola, using and redistributing the
original version or the your modified version. However, if you redistribute
Nikola to someone else, either a modified version or the original version, the
full copyright notice and license text must be included in your distribution.
Nikola is provided “as is”, and the Nikola contributors are not liable for any
damage caused by the software. Read the `full license text
<https://getnikola.com/license.html>`_ for details.
