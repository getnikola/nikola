.. slug: creating-a-site-not-a-blog-with-nikola
.. date: 2015-01-10 10:00:00 UTC
.. tags: nikola, python
.. link:
.. description:
.. title: Creating a Site (Not a Blog) with Nikola
.. author: The Nikola Team

Creating a Site (Not a Blog) with Nikola
========================================

.. class:: lead

One of the most frequent questions I get about Nikola is “but how do
I create a site that’s not a blog?”. And of course, that’s because the
documentation is heavily blog–oriented. This document will change that ;-)

Since it started, Nikola has had the capabilities to create generic sites. For example,
Nikola’s `own site <https://getnikola.com/>`_ is a fairly generic one. Let’s go
step by step on how you can do something like that.

As usual when starting a nikola site, you start with ``nikola init`` which creates a
empty (mostly) configured site:

.. code:: console

    $ nikola init mysite
    Creating Nikola Site
    ====================
    ⋮
    [1970-01-01T00:00:00Z] INFO: init: Created empty site at mysite.

Then we go into the new ``mysite`` folder, and make the needed changes in the ``conf.py``
configuration file:

.. code:: python

    # Data about this site
    BLOG_AUTHOR = "Roberto Alsina"
    BLOG_TITLE = "Not a Blog"
    # This is the main URL for your site. It will be used
    # in a prominent link
    SITE_URL = "https://getnikola.com/"
    BLOG_EMAIL = "ralsina@example.com"
    BLOG_DESCRIPTION = "This is a demo site (not a blog) for Nikola."

    #
    # Some things in the middle you don't really need to change...
    #

    # you can also keep the current content of POSTS if you want a blog with your site
    POSTS = ()
    # remove destination directory to generate pages in the root directory
    PAGES = (
        ("pages/*.rst", "", "story.tmpl"),
        ("pages/*.txt", "", "story.tmpl"),
        ("pages/*.html", "", "story.tmpl"),
    )

    # And to avoid a conflict because blogs try to generate /index.html
    INDEX_PATH = "blog"

    # Or you can disable blog indexes altogether:
    # DISABLE_INDEXES_PLUGIN_INDEX_AND_ATOM_FEED = True


And now we are ready to create our first page:

.. code:: console

    $ nikola new_page
    Creating New Page
    -----------------

    Title: index
    Scanning posts....done!
    [1970-01-01T00:00:00Z] INFO: new_page: Your page's text is at: pages/index.rst

We can now build and preview our site:

.. code:: console

    $ nikola build
    Scanning posts.done!
    .  render_site:output/categories/index.html
    .  render_sources:output/index.txt
    .  render_rss:output/rss.xml
    ⋮
    $ nikola serve
    [1970-01-01T00:00:00Z] INFO: serve: Serving HTTP on 0.0.0.0 port 8000...


And you can see your (very empty) site in http://localhost:8000/

So, what’s in that ``pages/index.txt`` file?

.. code:: rest

    .. title: index
    .. slug: index
    .. date: 1970-01-01 00:00:00 UTC
    .. tags:
    .. link:
    .. description:


    Write your post here.

``title`` is the page title, ``slug`` is the name of the generated HTML file
(in this case it would be ``index.html``). ``date``, ``tags`` and ``link``
doesn’t matter at all in pages. ``description`` is useful for SEO purposes
if you care for that.

And below, the content. By default Nikola uses
`reStructuredText <https://getnikola.com/quickstart.html>`_ but it supports
a ton of formats, including Markdown, plain HTML, Jupyter Notebooks, BBCode,
Wiki, and Textile. We will use reStructuredText for this example, but some
people might find it a bit too limiting — if that is the case, try using HTML
for your pages (Nikola does this on the index page, for example).

So, let's give the page a nicer title, and some fake content. Since the default
Nikola theme (called ``bootblog4``) is based on `Bootstrap <http://getbootstrap.com/>`_
you can use anything you like from it:

.. code:: rest

    .. title: Welcome To The Fake Site
    .. slug: index
    .. date: 1970-01-01 00:00:00 UTC
    .. tags:
    .. link:
    .. description: Fake Site version 1, welcome page!


    .. class:: jumbotron col-md-6

    .. admonition:: This is a Fake Site

        It pretends to be about things, but is really just an example.

        .. raw:: html

           <a href="https://getnikola.com/" class="btn btn-primary btn-lg">Click Me!</a>


    .. class:: col-md-5

    Lorem ipsum dolor sit amet, consectetur adipiscing elit. Mauris non nunc turpis.
    Phasellus a ullamcorper leo. Sed fringilla dapibus orci eu ornare. Quisque
    gravida quam a mi dignissim consequat. Morbi sed iaculis mi. Vivamus ultrices
    mattis euismod. Mauris aliquet magna eget mauris volutpat a egestas leo rhoncus.
    In hac habitasse platea dictumst. Ut sed mi arcu. Nullam id massa eu orci
    convallis accumsan. Nunc faucibus sodales justo ac ornare. In eu congue eros.
    Pellentesque iaculis risus urna. Proin est lorem, scelerisque non elementum at,
    semper vel velit. Phasellus consectetur orci vel tortor tempus imperdiet. Class
    aptent taciti sociosqu ad litora torquent per conubia nostra, per inceptos
    himenaeos.

.. admonition:: TIP: Nice URLs

   If you like your URLs without the ``.html`` then you want to create folders and
   put the pages in ``index.html`` inside them using the ``PRETTY_URLS`` option
   (on by default)

And that's it. You will want to change the NAVIGATION_LINKS option to create a reasonable
menu for your site, you may want to modify the theme (check ``nikola help bootswatch_theme``
for a quick & dirty solution), and you may want to add a blog later on, for company news
or whatever.

.. admonition:: TIP: So, how do I add a blog now?

    First, change the ``POSTS`` option like this:

    .. code:: python

        POSTS = (
            ("posts/*.rst", "blog", "post.tmpl"),
            ("posts/*.txt", "blog", "post.tmpl"),
            ("posts/*.html", "blog", "post.tmpl"),
        )

    Create a post with ``nikola new_post`` and that's it, you now have a blog
    in the ``/blog/`` subdirectory of your site — you may want to link to
    it in ``NAVIGATION_LINKS``.

If you want to see a site implementing all of the above, check out `the Nikola
website <https://getnikola.com/>`_.

I hope this was helpful!
