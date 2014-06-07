.. title: The Nikola Handbook
.. slug: handbook
.. date: 2012-03-30 23:00:00 UTC-03:00
.. tags:
.. link:
.. description:

The Nikola Handbook
===================

:Version: 7.0.1

.. class:: alert alert-info pull-right

.. contents::


All You Need to Know
--------------------

After you have Nikola `installed <#installing-nikola>`_:

Create a empty site (with a setup wizard):
    ``nikola init mysite``

You can create a site with demo files in it with ``nikola init --demo mysite``

The rest of these commands have to be executed inside the new ``mysite`` folder.

Create a post:
    ``nikola new_post``

Edit the post:
    The filename should be in the output of the previous command.

Build the site:
     ``nikola build``

Start the test server:
     ``nikola serve``

See the site:
     http://127.0.0.1:8000

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

It's original goal is to create blogs, but it supports most kind of sites, and
can be used as a CMS, as long as what you present to the user is your own content
instead of something the user generates.

Nikola can do:

* A blog (`example <http://ralsina.me>`__)
* Your company's site
* Your personal site
* A software project's site (`example <http://getnikola.com>`__)
* A book's site

Since Nikola-based sites don't run any code on the server, there is no way to process
user input in forms.

Nikola can't do:

* Twitter
* Facebook
* An Issue tracker
* Anything with forms, really (except for `comments <#comments-and-annotations>`_!)

Keep in mind that "static" doesn't mean **boring**. You can have animations, slides
or whatever fancy CSS/HTML5 thingie you like. It only means all that HTML is
generated already before being uploaded. On the other hand, Nikola sites will
tend to be content-heavy. What Nikola is good at is at putting what you write
out there.

Getting Help
------------

.. class:: lead

`Get help here! <http://getnikola.com/contact.html>`_

TL;DR:

* You can file bugs at `the issue tracker <https://github.com/getnikola/nikola/issues>`__
* You can discuss Nikola at the `nikola-discuss google group <http://groups.google.com/group/nikola-discuss>`_
* You can subscribe to `the Nikola Blog <http://getnikola.com/blog>`_
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

Obsolescense
    If you create a site using (for example) WordPress, what happens when WordPress
    releases a new version? You have to update your WordPress. That is not optional,
    because of security and support issues. If I release a new version of Nikola, and
    you don't update, *nothing* happens. You can continue to use the version you
    have now forever, no problems.

    Also, in the longer term, the very foundations of dynamic sites shift. Can you
    still deploy a blog software based on Django 0.96? What happens when your
    host stops supporting the php version you rely on? And so on.

    You may say those are long term issues, or that they won't matter for years. Well,
    I believe things should work forever, or as close to it as we can make them.
    Nikola's static output and its input files will work as long as you can install
    a Python > 2.6 in a Linux, Windows, or Mac and can find a server
    that sends files over HTTP. That's probably 10 or 15 years at least.

    Also, static sites are easily handled by the Internet Archive.

Cost and Performance
    On dynamic sites, every time a reader wants a page, a whole lot of database
    queries are made. Then a whole pile of code chews that data, and HTML is
    produced, which is sent to the user. All that requires CPU and memory.

    On a static site, the highly optimized HTTP server reads the file from disk
    (or, if it's a popular file, from disk cache), and sends it to the user. You could
    probably serve a bazillion (technical term) pageviews from a phone using
    static sites.

Lock-in
    On server-side blog platforms, sometimes you can't export your own data, or
    it's in strange formats you can't use in other services. I have switched
    blogging platforms from Advogato to PyCs to two homebrew systems, to Nikola,
    and have never lost a file, a URL, or a comment. That's because I have *always*
    had my own data in a format of my choice.

    With Nikola, you own your files, and you can do anything with them.

Features
--------

Nikola has a very defined feature set: it has every feature I needed for my own sites.
Hopefully, it will be enough for others, and anyway, I am open to suggestions.

If you want to create a blog or a site, Nikola provides:

* Front page (and older posts pages)
* RSS Feeds
* Pages and feeds for each tag you used
* Custom search
* Full yearly archives
* Custom output paths for generated pages
* Easy page template customization
* Static pages (not part of the blog)
* Internationalization support (my own blog is English/Spanish)
* Google sitemap generation
* Custom deployment (if it's a command, you can use it)
* A (very) basic look and feel you can customize, and is even text-mode friendly
* The input format is light markup (`reStructuredText <quickstart.html>`__ or
  `Markdown <http://daringfireball.net/projects/markdown/>`_)
* Easy-to-create image galleries
* Support for displaying source code
* Image slideshows
* Client-side cloud tags

Also:

* A preview web server
* "Live" re-rendering while you edit
* "Smart" builds: only what changed gets rebuilt (usually in seconds)
* Easy to extend with minimal Python knowledge.

Installing Nikola
-----------------

This is currently lacking on detail. Considering the niche Nikola is aimed at,
I suspect that's not a problem yet. So, when I say "get", the specific details
of how to "get" something for your specific operating system are left to you.

The short version is::

    pip install nikola

Note that you need Python v2.6 or newer OR v3.3 or newer.

Some features require **extra dependencies**.  You can install them all in bulk
by doing::

    pip install nikola[extras]

Alternatively, you can install those packages one-by-one, when required (Nikola
will tell you what packages are needed)

After that, run ``nikola init --demo sitename`` and that will run the setup
wizard, which will create a folder called ``sitename`` containing a functional
demo site.

Nikola is packaged for some Linux distributions, you may get that instead. e.g.
If you are running Arch Linux, there are AUR packages, available in Python 2/3
and stable/git master flavors: `python-nikola`__ / `python2-nikola`__ for the
latest stable release or `python-nikola-git`__ / `python2-nikola-git`__ for the
GitHub master.  (only one package may be installed at the same time.)

__ https://aur.archlinux.org/packages/python-nikola/
__ https://aur.archlinux.org/packages/python2-nikola/
__ https://aur.archlinux.org/packages/python-nikola-git/
__ https://aur.archlinux.org/packages/python2-nikola-git/

libxml/libxslt errors
~~~~~~~~~~~~~~~~~~~~~

If you get a ``ERROR: /bin/sh: 1: xslt-config: not found`` or ``fatal error:
libxml/xmlversion.h: No such file or directory`` when running ``pip install -r requirements.txt``, install *libxml* and *libxslt* libraries, like so:

Debian systems::

    sudo apt-get install libxml2-dev
    sudo apt-get install libxslt1-dev

Red Hat/RPM-based systems::

    sudo yum install libxslt-devel libxml2-devel

Python.h not found
~~~~~~~~~~~~~~~~~~

If you get an error to the effect of ``Python.h not found``, you need to
install development packages for Python.

Debian systems::

    sudo apt-get install python-dev

Red Hat/RPM-based systems::

    sudo yum install python-devel

Note that many other distros/operating systems (including Arch Linux,
\*BSD and OS X) do not require such packages, as C headers are included
with the base distribution of Python.

Installation on Linux, Mac OS X, \*BSD, and any other POSIX-compatible OS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

(we obviously support all.)

Using ``pip`` should suffice.  You may also want to use distribution- or
system-specific packages for our dependencies.

There are **no known issues or caveats** on those OSes.  Keep in mind that most
of our developers run Linux on a daily basis and may not have the full
knowledge required to resolve issues relating to your operating system.

Installation on Windows and Windows support
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Nikola supports Windows!  Keep in mind, though, that there are some
caveats:

#. ``lxml`` and ``Pillow`` require compiled extensions.  Compiling them on
   Windows is hard for most people.  Fortunately, compiled packages exist.
   Check their `PyPI <https://pypi.python.org/>`_ pages to find official packages,
   `the unofficial Gohlke binaries <http://www.lfd.uci.edu/~gohlke/pythonlibs/>`_
   site, or get them somewhere else.  If you are using virtualenvs, using those
   pre-built packages is possible through ``virtualenv --system-site-packages``.
#. Windows has some differences over POSIX, which may cause some features to
   work incorrectly under Windows.  If any problems occur, please do not
   hesitate to report them.  Some of the differeces include:

   * ``\`` as path separator (instead of ``/``)
   * the concept of HDD partitions and letters (instead of
     seamless mounting under one root)
   * some characters in paths are disallowed (although this shouldn’t cause
     problems)
   * CR+LF (aka ``\r\n``) as the line separator (instead of LF ``\n``)

#. Most of our developers run Linux on a daily basis and may not have the full
   knowledge required to resolve issues relating to Windows.

Getting Started
---------------

To create posts and pages in Nikola, you write them in one of the supported input formats.
Those source files are later converted to HTML
The recommended formats are reStructuredText and Markdown, but there is also support
for textile and WikiCreole and even for just writing HTML.

.. note:: There is a great `quick tutorial to learn reStructuredText. <quickstart.html>`__

First, let's see how you "build" your site. Nikola comes with a minimal site to get you started.

The tool used to do builds is called `doit <http://pydoit.org>`__, and it rebuilds the
files that are not up to date, so your site always reflects your latest content. To do our
first build, just run "nikola build"::

    $ nikola build
    Scanning posts....done!
    .  render_posts:stories/manual.html
    .  render_posts:posts/1.html
    .  render_posts:stories/1.html
    .  render_archive:output/2012/index.html
    .  render_archive:output/archive.html
    .  render_indexes:output/index.html
    .  render_pages:output/posts/welcome-to-nikola.html
    .  render_pages:output/stories/about-nikola.html
    .  render_pages:output/stories/handbook.html
    .  render_rss:output/rss.xml
    .  render_sources:output/stories/about-nikola.txt
    ⋮
    ⋮
    ⋮

Nikola will print a line for every output file it generates. If we do it again, that
will be much much shorter::

    $ nikola build
    Scanning posts....done!

That is because `doit <http://pydoit.org>`__ is smart enough not to generate
all the pages again, unless you changed something that the page requires. So, if you change
the text of a post, or its title, that post page, and all index pages where it is mentioned,
will be recreated. If you change the post page template, then all the post pages will be rebuilt.

Nikola is mostly a series of doit *tasks*, and you can see them by doing ``nikola list``::

    $ nikola list
    Scanning posts....done!
    build_bundles
    copy_assets
    copy_files
    deploy
    redirect
    render_archive
    render_galleries
    render_indexes
    render_listings
    render_pages
    render_posts
    render_rss
    render_site
    render_sources
    render_tags
    sitemap

You can make Nikola redo everything by calling ``nikola forget`` and then ``nikola build`` (or ``nikola build -a``,
you can make it do just a specific part of the site using task names, for example ``nikola build render_pages``,
and even individual files like ``nikola build output/index.html``

Nikola also has other commands besides ``build``::

    $ nikola help
    Nikola is a tool to create static websites and blogs. For full documentation and more information, please visit http://getnikola.com/


    Available commands:
      nikola auto                 automatically detect site changes, rebuild and optionally refresh a browser
      nikola bootswatch_theme     given a swatch name from bootswatch.com and a parent theme, creates a custom theme
      nikola build                run tasks
      nikola check                check links and files in the generated site
      nikola clean                clean action / remove targets
      nikola console              start an interactive Python console with access to your site
      nikola deploy               deploy the site
      nikola doit_auto            automatically execute tasks when a dependency changes
      nikola dumpdb               dump dependency DB
      nikola forget               clear successful run status from internal DB
      nikola github_deploy        deploy the site to GitHub pages
      nikola help                 show help
      nikola ignore               ignore task (skip) on subsequent runs
      nikola import_wordpress     import a WordPress dump
      nikola init                 create a Nikola site in the specified folder
      nikola install_theme        install theme into current site
      nikola list                 list tasks from dodo file
      nikola new_page             create a new page in the site
      nikola new_post             create a new blog post or site page
      nikola orphans              list all orphans
      nikola plugin               manage plugins
      nikola serve                start the test webserver
      nikola strace               use strace to list file_deps and targets
      nikola tabcompletion        generate script for tab-complention
      nikola version              print the Nikola version number

      nikola help                 show help / reference
      nikola help <command>       show command usage
      nikola help <task-name>     show task usage

The ``serve`` command starts a web server so you can see the site you are creating::

    $ nikola serve -b
    Serving HTTP on 127.0.0.1 port 8000 ...


After you do this, a web browser opens at http://127.0.0.1:8000/ and you should see
the sample site. This is useful as a "preview" of your work.

By default, the ``serve`` command runs the web server on port 8000 on the IP address 127.0.0.1.
You can pass in an IP address and port number explicitly using ``-a IP_ADDRESS``
(short version of ``--address``) or ``-p PORT_NUMBER`` (short version of ``--port``)
Example usage::

    $ nikola serve --address 0.0.0.0 --port 8080
    Serving HTTP on 0.0.0.0 port 8080 ...

Creating a Blog Post
--------------------

To create a new post, the easiest way is to run ``nikola new_post``. You  will
be asked for a title for your post, and it will tell you where the post's file
is located.

By default, that file will contain also some extra information about your post ("the metadata").
It can be placed in a separate file by using the ``-2`` option, but it's generally
easier to keep it in a single location.

The contents of your post have to be written (by default) in `reStructuredText <http://docutils.sf.net>`__
but you can use a lot of different markups using the ``-f`` option.

Currently Nikola supports reStructuredText, Markdown, IPython Notebooks, HTML as input,
can also use Pandoc for conversion, and has support for BBCode, CreoleWiki, txt2tags, Textile
and more via `plugins <http://plugins.getnikola.com>`__.

You can control what markup compiler is used for each file extension with the ``COMPILERS``
option. The default configuration expects them to be placed in ``posts`` but that can be
changed (see below, the ``POSTS`` and ``PAGES`` options)

This is how it works::

    $ nikola new_post
    Creating New Post
    -----------------

    Enter title: How to make money
    Your post's text is at:  posts/how-to-make-money.txt

The content of that file is as follows::

    .. title: How to make money
    .. slug: how-to-make-money
    .. date: 2012-09-15 19:52:05 UTC
    .. tags:
    .. link:
    .. description:
    .. type: text

    Write your post here.

The ``slug`` is the page name. Since often titles will have
characters that look bad on URLs, it's generated as a "clean" version of the title.
The third line is the post's date, and is set to "now".

The other lines are optional. Tags are comma-separated. The ``link`` is an original
source for the content, and ``description`` is mostly useful for SEO.
``type`` is the post type, whatever you set here (prepended with ``post-``)
will become a CSS class of the ``<article>`` element for this post.  Defaults to
``text`` (resulting in a ``post-text`` class)

You can add your own metadata fields in the same manner, if you use a theme that
supports them (for example: ``.. author: John Doe``)

To add these metadata fields to all new posts by default, you can set the
variable ``ADDITIONAL_METADATA`` in your configuration.  For example, you can
add the author metadata to all new posts by default, by adding the following
to your configuration::

    ADDITIONAL_METADATA = {
        'author': 'John Doe'
    }

.. sidebar:: Other Metadata Fields

   Nikola will also use other metadata fields:

   nocomments
       Set to "True" to disable comments. Example::

           .. nocomments: True

   template
       Will change the template used to render this page/post specific page. Example::

           .. template: story.tmpl

       That template needs to either be part of the theme, or be placed in a ``templates/``
       folder inside your site.

   password
       The post will be encrypted and invisible until the reader enters the password.
       Also, the post's sourcecode will not be available.

   category
       Like tags, except each post can have only one, and they usually have
       more descriptive names.

   annotations / noannotations
       Override the value of the ``ANNOTATIONS`` option for this specific post or page.

   author
       Author of the post, will be used in the RSS feed and possibly in the post
       display (theme-dependent)

   hidetitle
       Set "True" if you do not want to see the **story** title as a
       heading of the page (does not work for posts).

.. note:: The Two-File Format

   Nikola originally used a separate ``.meta`` file. That will still work!
   The format of the meta files is the same as shown above (i.e. only
   the 7 base fields, in the order listed above), but without the
   explanations::

        How to make money
        how-to-make-money
        2012-09-15 19:52:05 UTC

   However, starting with Nikola v7, you can now use ``.meta`` files and put
   all metadata you want, complete with the explanations — they look just like
   the beginning of our reST files.

        .. title: How to make money
        .. slug: how-to-make-money
        .. date: 2012-09-15 19:52:05 UTC

   Both file formats are supported; however, the new format is preferred, if
   possible.

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
default set to::

    TRANSLATIONS_PATTERN = "{path}.{lang}.{ext}"

.. note:: Considered languages

    nikola will only look for translation of input files for languages
    specified in the TRANSLATIONS variable.

You can edit these files with your favourite text editor, and once you are happy
with the contents, generate the pages as explained in `Getting Started`_

Currently supported languages are:

* Basque
* Bulgarian
* Catalan
* Chinese (Simplified)
* Croatian
* Czech
* Dutch
* English
* Esperanto
* Estonian
* Finnish
* French
* German
* Greek
* Hindi
* Italian
* Japanese
* Norwegian Bokmål
* Persian
* Polish
* Portuguese (Brasil)
* Russian
* Slovak
* Slovene
* Spanish
* Turkish
* Urdu

If you wish to add support for more languages, check out the instructions
at the `theming guide <http://getnikola.com/theming.html>`_.

The post page is generated using the ``post.tmpl`` template, which you can use
to customize the output.

The place where the post will be placed by ``new_post`` is based on the ``POSTS``
and ``PAGES`` configuration options::

    # POSTS and PAGES contains (wildcard, destination, template) tuples.
    #
    # The wildcard is used to generate a list of reSt source files
    # (whatever/thing.txt).
    #
    # That fragment could have an associated metadata file (whatever/thing.meta),
    # and optionally translated files (example for Spanish, with code "es"):
    #     whatever/thing.es.txt and whatever/thing.es.meta
    #
    #     This assumes you use the default TRANSLATIONS_PATTERN.
    #
    # From those files, a set of HTML fragment files will be generated:
    # cache/whatever/thing.html (and maybe cache/whatever/thing.html.es)
    #
    # These files are combinated with the template to produce rendered
    # pages, which will be placed at
    # output / TRANSLATIONS[lang] / destination / pagename.html
    #
    # where "pagename" is the "slug" specified in the metadata file.
    #
    # The difference between POSTS and PAGES is that POSTS are added
    # to feeds and are considered part of a blog, while PAGES are
    # just independent HTML pages.
    #

    POSTS = (
        ("posts/*.txt", "posts", "post.tmpl"),
        ("posts/*.rst", "posts", "post.tmpl"),
    )
    PAGES = (
        ("stories/*.txt", "stories", "story.tmpl"),
        ("stories/*.rst", "stories", "story.tmpl"),
    )

``new_post`` will use the *first* path in ``POSTS`` (or ``PAGES`` if ``-p`` is
supplied) that ends with the extension of your desired markup format (as
defined in ``COMPILERS`` in conf.py) as the directory that the new post will be
written into.  If no such entry can be found, the post won’t be created.

The ``new_post`` command supports some options::

    $ nikola help new_post
    Purpose: Create a new blog post or site page.
    Usage:   nikola new_post [options] [path]

    Options:
      -p, --page                Create a page instead of a blog post.
      -t ARG, --title=ARG       Title for the page/post.
      --tags=ARG                Comma-separated tags for the page/post.
      -1                        Create post with embedded metadata (single file format)
      -2                        Create post with separate metadata (two file format)
      -f ARG, --format=ARG      Markup format for post, one of rest, markdown, wiki, bbcode, html, textile, txt2tags

The optional ``path`` parameter tells nikola exactly where to put it instead of guessing from your config.
So, if you do ``nikola new_post posts/random/foo.txt`` you will have a post in that path, with
"foo" as its slug.

Teasers
~~~~~~~

You may not want to show the complete content of your posts either on your
index page or in RSS feeds, but to display instead only the beginning of them.

If it's the case, you only need to add a "magical comment" in your post.

In reStructuredText::

   .. TEASER_END

In Markdown::

   <!-- TEASER_END -->

By default all your RSS feeds will be shortened (they'll contain only teasers)
whereas your index page will still show complete posts. You can change
this behaviour with your ``conf.py``: ``INDEX_TEASERS`` defines whether index
page should display the whole contents or only teasers. ``RSS_TEASERS``
works the same way for your RSS feeds.

By default, teasers will include a "read more" link at the end. If you want to
change that text, you can use a custom teaser::

    .. TEASER_END: click to read the rest of the article

Or you can completely customize the link using the ``READ_MORE_LINK`` option::

    # A HTML fragment with the Read more... link.
    # The following tags exist and are replaced for you:
    # {link}        A link to the full post page.
    # {read_more}   The string “Read more” in the current language.
    # {{            A literal { (U+007B LEFT CURLY BRACKET)
    # }}            A literal } (U+007D RIGHT CURLY BRACKET)
    # READ_MORE_LINK = '<p class="more"><a href="{link}">{read_more}…</a></p>'


Drafts
~~~~~~

If you add a "draft" tag to a post, then it will not be shown in indexes and feeds.
It *will* be compiled, and if you deploy it it *will* be made available, so use
with care. If you wish your drafts to be not available in your deployed site, you
can set ``DEPLOY_DRAFTS = False`` in your configuration.

Also if a post has a date in the future, it will not be shown in indexes until
you rebuild after that date. This behaviour can be disabled by setting
``FUTURE_IS_NOW = True`` in your configuration, which will make future posts be
published immediately.  Posts dated in the future are *not* deployed by default
(when ``FUTURE_IS_NOW = False``).  To make future posts available in the
deployed site, you can set ``DEPLOY_FUTURE = True`` in your configuration.
Generally, you want FUTURE_IS_NOW and DEPLOY_FUTURE to be the same value.

Private (formerly retired) Posts
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you add a "private" tag to a post, then it will not be shown in indexes and feeds.
It *will* be compiled, and if you deploy it it *will* be made available, so it will
not generate 404s for people who had linked to it.

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
``SCHEDULE_RULE`` to your configuration ::

    SCHEDULE_RULE = 'RRULE:FREQ=WEEKLY;BYDAY=MO,WE,FR;BYHOUR=7;BYMINUTE=0;BYSECOND=0'

For more details on how to specify a recurrence rule, look at the
`iCal specification <http://www.kanzaki.com/docs/ical/rrule.html>`_.

Say, you get a free Sunday, and want to write a flurry of new posts,
or at least posts for the rest of the week, you would run the
``new_post`` command with the ``--schedule`` flag, as many times as
you want::

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

+-----------------+----------------------------+------------------+
| Name(s)         | Description                | Styling          |
+=================+============================+==================+
| text            | plain text — default value | standard         |
+-----------------+----------------------------+------------------+
| micro           | “small” (short) posts      | big serif font   |
+-----------------+----------------------------+------------------+

Creating a Page
---------------

Pages are the same as posts, except that:

* They are not added to the front page
* They don't appear on the RSS feed
* They use the ``story.tmpl`` template instead of ``post.tmpl`` by default

The default configuration expects the page's metadata and text files to be on the
``stories`` folder, but that can be changed (see ``PAGES`` option above).

You can create the page's files manually or use the ``new_post`` command
with the ``-p`` option, which will place the files in the folder that
has ``use_in_feed`` set to False.

Redirections
------------

If you need a page to be available in more than one place, you can define redirections
in your ``conf.py``::

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

The configuration file is called ``conf.py`` and can be used to customize a lot of
what Nikola does. Its syntax is python, but if you don't know the language, it
still should not be terribly hard to grasp.

The default ``conf.py`` you get with Nikola should be fairly complete, and is quite
commented.

You surely want to edit these options::

    # Data about this site
    BLOG_AUTHOR = "Your Name"  # (translatable)
    BLOG_TITLE = "Demo Site"  # (translatable)
    SITE_URL = "http://getnikola.com/"
    BLOG_EMAIL = "joe@demo.site"
    BLOG_DESCRIPTION = "This is a demo site for Nikola."  # (translatable)

Some options are demarked with a (translatable) comment above or right next to
them.  For those options, two types of values can be provided:

 * a string, which will be used for all languages
 * a dict of language-value pairs, to have different values in each language

Customizing Your Site
---------------------

There are lots of things you can do to personalize your website, but let's see
the easy ones!

CSS tweaking
    Using the default configuration, you can create a ``assets/css/custom.css``
    file and then it will be loaded from the ``<head>`` blocks of your site
    pages.  Create it and put your CSS code there, for minimal disruption of the
    provided CSS files.

    If you feel tempted to touch other files in assets, you probably will be better off
    with a `custom theme <theming.html>`__.

    If you want to use LESS_ or Sass_ for your custom CSS, or the theme you use
    contains LESS or Sass code that you want to override, you will need to install
    the `LESS plugin <http://plugins.getnikola.com/#less>`__ or
    `SASS plugin <http://plugins.getnikola.com/#sass>`__ create a ``less`` or
    ``sass`` directory in your site root, put your ``.less`` or ``.scss`` files
    there and a targets file containing the list of files you want compiled.

.. _LESS: http://lesscss.org/
.. _Sass: http://sass-lang.com/

Template tweaking
    If you really want to change the pages radically, you will want to do a
    `custom theme <theming.html>`__.


Navigation Links
    The ``NAVIGATION_LINKS`` option lets you define what links go in a sidebar or menu
    (depending on your theme) so you can link to important pages, or to other sites.

    The format is a language-indexed dictionary, where each element is a tuple of
    tuples which are one of:

    1. A (url, text) tuple, describing a link
    2. A (((url, text), (url, text), (url, text)), title) tuple, describing a submenu / sublist.

    Example::

        NAVIGATION_LINKS = {
            DEFAULT_LANG: (
                ('/archive.html', 'Archives'),
                ('/categories/index.html', 'Tags'),
                ('/rss.xml', 'RSS'),
                ((('/foo', 'FOO'),
                  ('/bar', 'BAR')), 'BAZ'),
            ),
        }


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

Adding Files
------------

Any files you want to be in ``output/`` but are not generated by Nikola (for example,
``favicon.ico``) just put it in ``files/``. Everything there is copied into
``output`` by the ``copy_files`` task. Remember that you can't have files that collide
with files Nikola generates (it will give an error).

.. admonition:: Important

   Don't put any files manually in ``output/``. Ever. Really. Maybe someday Nikola
   will just wipe ``output/`` and then you will be sorry. So, please don't do that.

If you want to copy more than one folder of static files into ``output`` you can
change the FILES_FOLDERS option::

    # One or more folders containing files to be copied as-is into the output.
    # The format is a dictionary of "source" "relative destination".
    # Default is:
    # FILES_FOLDERS = {'files': '' }
    # Which means copy 'files' into 'output'

Getting More Themes
-------------------

There are a few themes for Nikola. They are available at
the `Themes Index <http://themes.getnikola.com/>`_.
Nikola has a built-in theme download/install mechanism to install those themes — the ``install_theme`` command::

    $ nikola install_theme -l
    Themes:
    -------
    blogtxt
    bootstrap3-gradients
    ⋮
    ⋮

    $ nikola install_theme blogtxt
    [2013-10-12T16:46:13Z] NOTICE: install_theme: Downloading:
    http://themes.getnikola.com/v6/blogtxt.zip
    [2013-10-12T16:46:15Z] NOTICE: install_theme: Extracting: blogtxt into themes

And there you are, you now have themes/blogtxt installed. It's very
rudimentary, but it should work in most cases.

If you create a nice theme, please share it!  You can do it as a pull
request in the  `GitHub repository <https://github.com/getnikola/nikola-themes>`__.

One other option is to tweak an existing theme using a different color scheme,
typography and CSS in general. Nikola provides a ``bootswatch_theme`` option
to create a custom theme by downloading free CSS files from http://bootswatch.com::

    $ nikola bootswatch_theme -n custom_theme -s spruce -p bootstrap3
    [2013-10-12T16:46:58Z] NOTICE: bootswatch_theme: Creating 'custom_theme' theme
    from 'spruce' and 'bootstrap3'
    [2013-10-12T16:46:58Z] NOTICE: bootswatch_theme: Downloading:
    http://bootswatch.com//spruce/bootstrap.min.css
    [2013-10-12T16:46:58Z] NOTICE: bootswatch_theme: Downloading:
    http://bootswatch.com//spruce/bootstrap.css
    [2013-10-12T16:46:59Z] NOTICE: bootswatch_theme: Theme created. Change the THEME setting to "custom_theme" to use it.

You can even try what different swatches do on an existing site using
their handy `bootswatchlet <http://news.bootswatch.com/post/29555952123/a-bookmarklet-for-bootswatch>`_

Play with it, there's cool stuff there. This feature was suggested by
`clodo <http://elgalpondebanquito.com.ar>`_.

Deployment
----------

Nikola doesn't really have a concept of deployment. However, if you can specify your
deployment procedure as a series of commands, you can put them in the ``DEPLOY_COMMANDS``
option, and run them with ``nikola deploy``.

One caveat is that if any command has a % in it, you should double them.

Here is an example, from my own site's deployment script::

    DEPLOY_COMMANDS = [
        'rsync -rav --delete output/ ralsina@lateral.netmanagers.com.ar:/srv/www/lateral',
        'rdiff-backup output ~/blog-backup',
        "links -dump 'http://www.twingly.com/ping2?url=lateral.netmanagers.com.ar'",
    ]

Other interesting ideas are using
`git as a deployment mechanism <http://toroid.org/ams/git-website-howto>`_ (or any other VCS
for that matter), using `lftp mirror <http://lftp.yar.ru/>`_ or unison, or Dropbox, or
Ubuntu One. Any way you can think of to copy files from one place to another is good enough.

Deploying to GitHub
~~~~~~~~~~~~~~~~~~~

Nikola provides a separate command ``github_deploy`` to deploy your
site to GitHub pages.  The command builds the site, commits the
output to a gh-pages branch and pushes the output to GitHub.

The branch to use for committing the sources can be changed using the
``GITHUB_DEPLOY_BRANCH`` option in your config.  For a
user.github.io/organization.github.io, this MUST be set to ``master``,
and the branch containing the sources must be changed to something
else, like ``deploy``, using the ``GITHUB_SOURCE_BRANCH`` option.  The
remote name to which the changes are pushed is ``origin`` by default,
and can be changed using the ``GITHUB_REMOTE_NAME`` option.  You also,
obviously, need to have ``git`` on your PATH, and should be able to
push to the repository specified as the remote.

This command performs the following actions, when it is run:

1. Ensure that your site is a git repository, and git is on the PATH.
2. Check for changes, and prompt the user to continue, if required.
3. Build the site
4. Clean any files that are "unknown" to Nikola.
5. Create a deploy branch, if one doesn't exist.
6. Commit the output to this branch.  (NOTE: Any untracked source
   files, may get committed at this stage, on the wrong branch!)
7. Push and deploy!

Comments and Annotations
------------------------

While Nikola creates static sites, there is a minimum level of user interaction you
are probably expecting: comments.

Nikola supports several third party comment systems:

* `DISQUS <http://disqus.com>`_
* `IntenseDebate <http://www.intensedebate.com/>`_
* `LiveFyre <http://www.livefyre.com/>`_
* `Moot <http://moot.it>`_
* `Google+ <http://plus.google.com>`_
* `Facebook <http://facebook.com/>`_
* `isso <http://posativ.org/isso/>`_

By default it will use DISQUS, but you can change by setting ``COMMENT_SYSTEM``
to one of "disqus", "intensedebate", "livefyre", "moot", "googleplus" or
"facebook"

.. sidebar:: ``COMMENT_SYSTEM_ID``

   The value of ``COMMENT_SYSTEM_ID`` depends on what comment system you
   are using and you can see it in the system's admin interface.

   * For DISQUS it's called the **shortname**
   * In IntenseDebate it's the **IntenseDebate site acct**
   * In LiveFyre it's the **siteId**
   * In Moot it's your **username**
   * For Google Plus, ``COMMENT_SYSTEM_ID`` need not be set, but you must
     `verify your authorship <https://plus.google.com/authorship>`_
   * For Facebook, you need to `create an app
     <https://developers.facebook.com/apps>` (turn off sandbox mode!)
     and get an **App ID**
   * For isso, it is the URL of isso (must be world-accessible and **have a trailing slash**,
     default ``http://localhost:8080/``)

To use comments in a visible site, you should register with the service and
then set the ``COMMENT_SYSTEM_ID`` option.

I recommend 3rd party comments, and specially DISQUS because:

1) It doesn't require any server-side software on your site
2) They offer you a way to export your comments, so you can take
   them with you if you need to.
3) It's free.
4) It's damn nice.

You can disable comments for a post by adding a "nocomments" metadata field to it::

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

An alternative or complement to comments are annotations. Nikola integrates
the annotation service provided by `AnnotateIt. <annotateit.org>`_
To use it, set the ``ANNOTATIONS`` option to True. This is specially useful
if you want feedback on specific parts of your writing.

You can enable or disable annotations for specific posts or pages using the
``annotations`` and ``noannotations`` metadata.

Annotations require JQuery and are therefore not supported in the base theme.
You can check bootstrap theme's ``base.html`` for details on how to handle them in
custom themes.

Image Galleries
---------------

To create an image gallery, all you have to do is add a folder inside ``galleries``,
and put images there. Nikola will take care of creating thumbnails, index page, etc.

If you click on images on a gallery, you should see a bigger image, thanks to
the excellent `colorbox <http://www.jacklmoore.com/colorbox>`_

The gallery pages are generated using the ``gallery.tmpl`` template, and you can
customize it there (you could switch to another lightbox instead of colorbox, change
its settings, change the layout, etc.).

The ``conf.py`` options affecting gallery pages are these::

    # Galleries are folders in galleries/
    # Final location of galleries will be output / GALLERY_PATH / gallery_name
    GALLERY_PATH = "galleries"
    THUMBNAIL_SIZE = 180
    MAX_IMAGE_SIZE = 1280
    USE_FILENAME_AS_TITLE = True
    GALLERY_SORT_BY_DATE = False
    EXTRA_IMAGE_EXTENSIONS = []

If you add a file in ``galleries/gallery_name/index.txt`` its contents will be
converted to HTML and inserted above the images in the gallery page. The
format is the same as for posts.

If you add some image filenames in ``galleries/gallery_name/exclude.meta``, they
will be excluded in the gallery page.

If ``USE_FILENAME_AS_TITLE`` is True the filename (parsed as a readable string)
is used as the photo caption. If the filename starts with a number, it will
be stripped. For example ``03_an_amazing_sunrise.jpg`` will be render as *An amazing sunrise*.

Here is a `demo gallery </galleries/demo>`_ of historic, public domain Nikola
Tesla pictures taken from `this site <http://kerryr.net/pioneers/gallery/tesla.htm>`_.

Post Processing Filters
-----------------------

You can apply post processing to the files in your site, in order to optimize them
or change them in arbitrary ways. For example, you may want to compress all CSS
and JS files using yui-compressor.

To do that, you can use the provided helper adding this in your ``conf.py``::

  from nikola import filters

  FILTERS = {
    ".css": [filters.yui_compressor],
    ".js": [filters.yui_compressor],
  }

Where ``filters.yui_compressor`` is a helper function provided by Nikola. You can
replace that with strings describing command lines, or arbitrary python functions.

If there's any specific thing you expect to be generally useful as a filter, contact
me and I will add it to the filters library so that more people use it.

The currently available filters are:

.. sidebar:: Creating your own filters

   You can use any program name that works in place as a filter, like ``sed -i``
   and you can use arbitrary python functions as filters, too.

   If your program doesn't run in-place, then you can use Nikola's runinplace function.
   For example, this is how the yui_compressor filter is implemented:

   .. code-block:: python

      def yui_compressor(infile):
          return runinplace(r'yui-compressor --nomunge %1 -o %2', infile)

   You can turn any function into a filter using ``apply_to_file``.
   As a silly example, this would make everything uppercase and totally break
   your website:

   .. code-block:: python

      import string
      from nikola.filters import apply_to_file
      FILTERS = {
        ".html": [apply_to_file(string.upper)]
      }

yui_compressor
   Compress files using `YUI compressor <http://yui.github.io/yuicompressor/>`_

optipng
   Compress PNG files using `optipng <http://optipng.sourceforge.net/>`_

jpegoptim
   Compress JPEG files using `jpegoptim <http://www.kokkonen.net/tjko/projects.html>`_

typogrify
   Improve typography using `typogrify <https://github.com/mintchaos/typogrify>`_


Optimizing Your Website
-----------------------

One of the main goals of Nikola is to make your site fast and light. So here are a few
tips we have found when setting up Nikola with Apache. If you have more, or
different ones, or about other web servers, please share!

#. Use a speed testing tool. I used Yahoo's YSlow but you can use any of them, and
   it's probably a good idea to use more than one.

#. Enable compression in Apache::

      AddOutputFilterByType DEFLATE text/html text/plain text/xml text/css text/javascript

#. If even after you did the previous step the CSS files are not sent compressed::

      AddType text/css .css

#. Optionally you can greate static compressed copies and save some CPU on your server
   with the GZIP_FILES option in Nikola.

#. The webassets Nikola plugin can drastically decrease the number of CSS and JS files your site fetches.

#. Through the filters feature, you can run your files through arbitrary commands, so that images
   are recompressed, JavaScript is minimized, etc.

#. The USE_CDN option offloads standard JavaScript and CSS files to a CDN so they are not
   downloaded from your server.

reStructuredText Extensions
---------------------------

Nikola includes support for a few directives and roles that are not part of docutils, but which
we think are handy for website development.

Media
~~~~~

This directive lets you embed media from a variety of sites automatically by just passing the
URL of the page.  For example here are two random videos::

    .. media:: http://vimeo.com/72425090

    .. youtube:: http://www.youtube.com/watch?v=wyRpAat5oz0

It supports Instagram, Flickr, Github gists, Funny or Die, and dozens more, thanks to `Micawber <https://github.com/coleifer/micawber>`_

YouTube
~~~~~~~

To link to a YouTube video, you need the id of the video. For example, if the
URL of the video is http://www.youtube.com/watch?v=8N_tupPBtWQ what you need is
**8N_tupPBtWQ**

Once you have that, all you need to do is::

    .. youtube:: 8N_tupPBtWQ

Vimeo
~~~~~

To link to a Vimeo video, you need the id of the video. For example, if the
URL of the video is http://www.vimeo.com/20241459 then the id is **20241459**

Once you have that, all you need to do is::

    .. vimeo:: 20241459

If you have internet connectivity when generating your site, the height and width of
the embedded player will be set to the native height and width of the video.
You can override this if you wish::

    .. vimeo:: 20241459
       :height: 240
       :width: 320

Soundcloud
~~~~~~~~~~

This directive lets you share music from http://soundcloud.com You first need to get the
ID for the piece, which you can find in the "share" link. For example, if the
WordPress code starts like this::

    [soundcloud url="http://api.soundcloud.com/tracks/78131362"

The ID is 78131362 and you can embed the audio with this::

    .. soundcloud:: 78131362

You can also embed playlists, via the `soundcloud_playlist` directive which works the same way.

    .. soundcloud_playlist:: 9411706

Code
~~~~

The ``code`` directive has been included in docutils since version 0.9 and now
replaces Nikola's ``code-block`` directive. To ease the transition, two aliases
for ``code`` directive are provided: ``code-block`` and ``sourcecode``::

    .. code-block:: python
       :number-lines:

       print("Our virtues and our failings are inseparable")

Listing
~~~~~~~

To use this, you have to put your source code files inside ``listings`` or whatever your
``LISTINGS_FOLDER`` variable is set to. Assuming you have a ``foo.py`` inside that folder::

    .. listing:: foo.py python

Will include the source code from ``foo.py``, highlight its syntax in python mode,
and also create a ``listings/foo.py.html`` page and the listing will have a title linking to it.

Listings support a few extra options so that you can display a fragment instead of the whole
file in a document:

start-at
    Takes a string, and starts displaying the code at the first line that matches it.
start-before
    Takes a string, and starts displaying the code right before the first line that matches it.
end-at
    Takes a string, and stops displaying the code at the first line that matches it.
end-before
    Takes a string, and stops displaying the code right before the first line that matches it.

If you set start-at and start-before, start-at wins. If you set end-at and end-before, end-at wins.
If you make it so your listing ends before it starts, it's frowned upon and nothing will be shown.

Gist
~~~~

You can easily embed GitHub gists with this directive, like this::

    .. gist:: 2395294

Producing this:

.. gist:: 2395294

This degrades gracefully if the browser doesn't support JavaScript.

Slideshows
~~~~~~~~~~

To create an image slideshow, you can use the ``slides`` directive. For example::

    .. slides::

       /galleries/demo/tesla_conducts_lg.jpg
       /galleries/demo/tesla_lightning2_lg.jpg
       /galleries/demo/tesla4_lg.jpg
       /galleries/demo/tesla_lightning1_lg.jpg
       /galleries/demo/tesla_tower1_lg.jpg

Chart
~~~~~

This directive is a thin wrapper around `Pygal <http://pygal.org/>`_ and will produce charts
as SVG files embedded directly in your pages.

Here's an example of how it works::

            .. chart:: Bar
               :title: 'Browser usage evolution (in %)'
               :x_labels: ["2002", "2003", "2004", "2005", "2006", "2007"]

               'Firefox', [None, None, 0, 16.6, 25, 31]
               'Chrome',  [None, None, None, None, None, None]
               'IE',      [85.8, 84.6, 84.7, 74.5, 66, 58.6]
               'Others',  [14.2, 15.4, 15.3, 8.9, 9, 10.4]

The argument passed next to the directive (Bar in that example) is the type of chart, and can be one of
Line, StackedLine, Bar, StackedBar, HorizontalBar, XY, DateY, Pie, Radar, Dot, Funnel, Gauge, Pyramid. For
examples of what each kind of graph is, `check here <http://pygal.org/chart_types/>`_

It can take *a lot* of options to let you customize the charts (in the example, title and x_labels).
You can use any option described in `the pygal docs <http://pygal.org/basic_customizations/>`_

Finally, the content of the directive is the actual data, in the form of a label and
a list of values, one series per line.

Doc
~~~

This role is useful to make links to other post or page inside the same site.

Here's an example::

    Take a look at :doc:`my other post <creating-a-theme>` about theme creating.

In this case we are giving the portion of text we want to link. So, the result will be:

    Take a look at :doc:`my other post <creating-a-theme>` about theme creating.

If we want to use the post's title as the link's text, just do::

    Take a look at :doc:`creating-a-theme` to know how to do it.

and it will produce:

    Take a look at :doc:`creating-a-theme` to know how to do it.


Importing Your WordPress Site Into Nikola
-----------------------------------------

If you like Nikola, and want to start using it, but you have a WordPress blog, Nikola
supports importing it. Here's the steps to do it:

1) Get a XML dump of your site [#]_
2) nikola import_wordpress mysite.wordpress.2012-12-20.xml

After some time, this will create a ``new_site`` folder with all your data. It currently supports
the following:

* All your posts and pages
* Keeps "draft" status
* Your tags and categories
* Imports your attachments and fixes links to point to the right places
* Will try to add redirects that send the old post URLs to the new ones
* Will give you a url_map so you know where each old post was

  This is also useful for DISQUS thread migration!

* Will try to convert the content of your posts. This is *not* error free, because
  WordPress uses some unholy mix of HTML and strange things. Currently we are treating it
  as markdown, which does a reasonable job of it.

  You will find your old posts in ``new_site/posts/post-title.wp`` in case you need to fix
  any of them.

This feature is a work in progress, and the only way to improve it is to have it used for
as many sites as possible and make it work better each time, so I am happy to get requests
about it.

.. [#] The dump needs to be in 1.2 format. You can check by reading it, it should say
       ``xmlns:excerpt="http://wordpress.org/export/1.2/excerpt/"`` near the top of the
       file. If it says ``1.1`` instead of ``1.2`` you will have to update your
       WordPress before dumping.

       Other versions may or may not work.

Importing To A Custom Location Or Into An Existing Site
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It is possible to either import into a location you desire or into an already existing Nikola site.
To do so you can specify a location after the dump.::

    $ nikola import_wordpress  mysite.wordpress.2012-12-20.xml -o import_location

With this command Nikola will import into the folder ``import_location``.

If the folder already exists Nikola will not overwrite an existing ``conf.py``.
Instead a new file with a timestamp at the end of the filename will be created.

Using Twitter Cards
-------------------

Twitter Cards enable you to show additional information in Tweets that link
to you content.
Nikola supports `Twitter Cards <https://dev.twitter.com/docs/cards>`_.
They are implemented to use *Open Graph* tags whenever possible.

.. admonition:: Important

    To use Twitter Cards you need to opt-in on Twitter.
    To do so please use the form that can be found at https://dev.twitter.com/form/participate-twitter-cards

To enable and configure your use of Twitter Cards please modify the
corresponding lines in your ``conf.py``.
An example configuration that uses the Twitter nickname of the website
and the authors Twitter user ID is found below.

.. code-block:: python

    TWITTER_CARD = {
        'use_twitter_cards': True,  # enable Twitter Cards / Open Graph
        'site': '@website',  # twitter nick for the website
        # 'site:id': 123456,  # Same as site, but the website's Twitter user ID instead.
        # 'creator': '@username',  # Username for the content creator / author.
        'creator:id': 654321,  # Same as creator, but the Twitter user's ID.
    }


Custom Plugins
--------------

You can create your own plugins (see :doc:`extending`) and use them in your own
site by putting them in a ``plugins/`` folder.  You can also put them in
directories listed in the ``EXTRA_PLUGINS_DIRS`` configuration variable.


Getting Extra Plugins
---------------------

If you want extra plugins, there is also the `Plugins Index <http://plugins.getnikola.com/>`_.

Similarly to themes, there is a nice, built-in command to manage them —
``plugin``::

    $ nikola plugin -l
    Plugins:
    --------
    helloworld
    tags
    ⋮
    ⋮

    $ nikola plugin --install helloworld
    [2013-10-12T16:51:56Z] NOTICE: install_plugin: Downloading: http://plugins.getnikola.com/v6/helloworld.zip
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

Then you also can uninstall your plugins::

    $ nikola plugin --uninstall tags
    [2014-04-15T08:59:24Z] WARNING: plugin: About to uninstall plugin: tags
    [2014-04-15T08:59:24Z] WARNING: plugin: This will delete /home/ralsina/foo/plugins/tags
    Are you sure? [y/n] y
    [2014-04-15T08:59:26Z] WARNING: plugin: Removing /home/ralsina/foo/plugins/tags

And upgrade them::

    $ nikola plugin --upgrade
    [2014-04-15T09:00:18Z] WARNING: plugin: This is not very smart, it just reinstalls some plugins and hopes for the best
    Will upgrade 1 plugins: graphviz
    Upgrading graphviz
    [2014-04-15T09:00:20Z] INFO: plugin: Downloading: http://plugins.getnikola.com/v7/graphviz.zip
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

Shell Tab Completion
--------------------

Since Nikola is a command line tool, and this is the 21st century, it's handy to have smart tab-completion
so that you don't have to type the full commands.

To enable this, you can use the ``nikola tabcompletion`` command like this, depending on your shell::

    $ nikola tabcompletion --shell bash --hardcode-tasks > _nikola_bash
    $ nikola tabcompletion --shell zsh --hardcode-tasks > _nikola_zsh

The ``--hardcode-tasks`` adds tasks to the completion and may need updating periodically.

License
-------

Nikola is released under a `MIT license <https://github.com/getnikola/nikola/blob/master/LICENSE.txt>`_ which
is a free software license. Some components shipped along with Nikola, or required by it are
released under other licenses.

If you are not familiar with free software licensing: In general, you should be able to
do pretty much anything you want, unless you modify Nikola. If you modify it, and share
it with someone else, that someone else should get all your modifications under the same
license you got it.
