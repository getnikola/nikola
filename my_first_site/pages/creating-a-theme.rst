.. title: Creating a Theme
.. slug: creating-a-theme
.. date: 2015-05-28 18:46:48 UTC
.. tags:
.. category:
.. link:
.. description:
.. type: text

Nikola is a static site and blog generator. So is Jekyll. While I like what we have done with Nikola,
I do admit that Jekyll (and others!) have many more, and nicer themes than Nikola does.

This document is an attempt at making it easier for 3rd parties (that means *you* people! ;-) to
create themes. Since I **suck** at designing websites, I asked for opinions on themes to port,
and got some feedback. Since this is **Not So Hard™**, I will try to make time to port a few
and see what happens.

If you are looking for a reference, check out :doc:`Theming reference <theming>` and `Template variables <https://getnikola.com/template-variables.html>`_.

Today’s theme is `Lanyon <https://github.com/poole/lanyon>`__ which is written by `@mdo <https://twitter.com/mdo>`__
and released under a MIT license, which is liberal enough.

So, let’s get started.

Checking It Out
---------------

The first step in porting a theme is making the original theme work. Lanyon is awesome in that its
`GitHub project <https://github.com/poole/lanyon>`__ is a full site!

So::

    # Get jekyll
    sudo apt-get install jekyll

    # Get Lanyon
    git clone git@github.com:poole/lanyon.git

    # Build it
    cd lanyon && jekyll build

    # Look at it
    jekyll serve & google-chrome http://localhost:4000

If you **do not want to install Jekyll**, you can also see it in action at https://lanyon.getpoole.com/

Some things jump to my mind:

1. This is one fine looking theme
2. Very clear and readable
3. Nice hidden navigation-thingy

Also, from looking at `the project’s README <https://github.com/poole/lanyon/blob/master/README.md>`__
it supports some nice configuration options:

1. Color schemes
2. Reverse layout
3. Sidebar overlay instead of push
4. Open the sidebar by default, or on a per-page basis by using its metadata

Let’s try to make all those nice things survive the porting.

Starting From Somewhere
-----------------------

Nikola has a nice, clean, base theme from which you can start when writing your own theme.
Why start from that instead of from a clean slate? Because theme inheritance is going to save you a ton of work,
that’s why. If you start from scratch you won’t be able to build **anything** until you have a bunch of
templates written. Starting from base, you just need to hack on the things you **need** to change.

First, we create a site with some content in it. We’ll use the ``nikola init`` wizard (with the ``--demo`` option) for that::

    $ nikola init --demo lanyon-port
    Creating Nikola Site
    ====================

    This is Nikola v7.8.0.  We will now ask you a few easy questions about your new site.
    If you do not want to answer and want to go with the defaults instead, simply restart with the `-q` parameter.
    --- Questions about the site ---
    Site title [My Nikola Site]:
    Site author [Nikola Tesla]:
    Site author's e-mail [n.tesla@example.com]:
    Site description [This is a demo site for Nikola.]:
    Site URL [https://example.com/]:
    --- Questions about languages and locales ---
    We will now ask you to provide the list of languages you want to use.
    Please list all the desired languages, comma-separated, using ISO 639-1 codes.  The first language will be used as the default.
    Type '?' (a question mark, sans quotes) to list available languages.
    Language(s) to use [en]:

    Please choose the correct time zone for your blog. Nikola uses the tz database.
    You can find your time zone here:
    https://en.wikipedia.org/wiki/List_of_tz_database_time_zones

    Time zone [UTC]:
        Current time in UTC: 16:02:07
    Use this time zone? [Y/n]
    --- Questions about comments ---
    You can configure comments now.  Type '?' (a question mark, sans quotes) to list available comment systems.  If you do not want any comments, just leave the field blank.
    Comment system:

    That's it, Nikola is now configured.  Make sure to edit conf.py to your liking.
    If you are looking for themes and addons, check out https://themes.getnikola.com/ and https://plugins.getnikola.com/.
    Have fun!
    [2015-05-28T16:02:08Z] INFO: init: A new site with example data has been created at lanyon-port.
    [2015-05-28T16:02:08Z] INFO: init: See README.txt in that folder for more information.


Then, we create an empty theme inheriting from base. This theme will use Mako templates. If you prefer Jinja2,
then you should use ``base-jinja`` as a parent and ``jinja`` as engine instead::

    $ cd lanyon-port/
    $ nikola theme -n lanyon --parent base --engine mako

Edit ``conf.py`` and set ``THEME = 'lanyon'``. Also set ``USE_BUNDLES = False`` (just do it for now, we’ll get to bundles later).
Also, if you intend to publish your theme on the Index, or want to use it with older versions (v7.8.5 or older), use the ``--legacy-meta`` option for ``nikola theme -n``.

You can now build that site using ``nikola build`` and it will look like this:

.. figure:: https://getnikola.com/images/lanyon-0.thumbnail.png
   :target: https://getnikola.com/images/lanyon-0.png

   This is just the base theme.

Basic CSS
---------

The next step is to know exactly how Lanyon’s pages work. To do this, we read its HTML.
First let’s look at the head element:

.. code:: html

    <!DOCTYPE html>
    <html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en-us">

    <head>
    <link href="https://gmpg.org/xfn/11" rel="profile">
    <meta http-equiv="content-type" content="text/html; charset=utf-8">

    <!-- Enable responsiveness on mobile devices-->
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1">

    <title>
        Lanyon &middot; A Jekyll theme
    </title>

    <!-- CSS -->
    <link rel="stylesheet" href="/public/css/poole.css">
    <link rel="stylesheet" href="/public/css/syntax.css">
    <link rel="stylesheet" href="/public/css/lanyon.css">
    <link rel="stylesheet" href="https://fonts.googleapis.com/css?family=PT+Serif:400,400italic,700|PT+Sans:400">

    <!-- Icons -->
    <link rel="apple-touch-icon-precomposed" sizes="144x144" href="/public/apple-touch-icon-144-precomposed.thumbnail.png">
    <link rel="shortcut icon" href="/public/favicon.ico">

    <!-- RSS -->
    <link rel="alternate" type="application/rss+xml" title="RSS" href="/atom.xml">

    <!-- Google Analytics -->
    [...]
    </head>

The interesting part there is that it loads a few CSS files. If you check the source of your Nikola site, you will
see something fairly similar:

.. code:: html

    <!DOCTYPE html>
    <html prefix="og: http://ogp.me/ns# article: http://ogp.me/ns/article# " vocab="http://ogp.me/ns" lang="en">
    <head>
    <meta charset="utf-8">
    <meta name="description" content="This is a demo site for Nikola.">
    <meta name="viewport" content="width=device-width">
    <title>My Nikola Site | My Nikola Site</title>

    <link href="assets/css/rst_base.css" rel="stylesheet" type="text/css">
    <link href="assets/css/code.css" rel="stylesheet" type="text/css">
    <link href="assets/css/theme.css" rel="stylesheet" type="text/css">

    <link rel="alternate" type="application/rss+xml" title="RSS" href="rss.xml">
    <link rel="canonical" href="https://example.com/index.html">
    <!--[if lt IE 9]><script src="assets/js/html5.js"></script><![endif]--><link rel="prefetch" href="posts/welcome-to-nikola.html" type="text/html">
    </head>



Luckily, since this is all under a very liberal license, we can just copy these CSS files into
Nikola, adapting the paths a little so that they follow our conventions::

    $ mkdir -p themes/lanyon/assets/css
    $ cp ../lanyon/public/css/poole.css themes/lanyon/assets/css/
    $ cp ../lanyon/public/css/lanyon.css themes/lanyon/assets/css/

Notice I am *not* copying ``syntax.css``? That’s because Nikola handles that styles for syntax highlighting
in a particular way, using a setting called ``CODE_COLOR_SCHEME`` where you can configure
what color scheme the syntax highlighter uses. You can use your own ``assets/css/code.css`` if you
don’t like the provided ones.

Nikola **requires** ``assets/css/rst_base.css`` and ``assets/css/code.css`` to function properly.
We will also add themes for Jupyter (``assets/css/ipython.min.css``
and ``assets/css/nikola_ipython.css``) into the template; note that they are
activated only if you configured your ``POSTS``/``PAGES`` with ipynb support.
There’s also ``assets/css/nikola_rst.css``, which adds Bootstrap 3-style reST notes etc.

But how do I tell **our** lanyon theme to use those CSS files instead of whatever it’s using now?
By giving our theme its own base_helper.tmpl.

That file is a **template** used to generate parts of the pages. It’s large and
complicated but we don’t need to change a lot of it. First, make a copy in your
theme (note this command requires setting your ``THEME`` in ``conf.py`` to
``lanyon``)::

    $ nikola theme -c base_helper.tmpl

The part we want to change is this:

.. code:: html+mako

    <%def name="html_stylesheets()">
        %if use_bundles:
            %if use_cdn:
                <link href="/assets/css/all.css" rel="stylesheet" type="text/css">
            %else:
                <link href="/assets/css/all-nocdn.css" rel="stylesheet" type="text/css">
            %endif
        %else:
            <link href="/assets/css/rst_base.css" rel="stylesheet" type="text/css">
            <link href="/assets/css/nikola_rst.css" rel="stylesheet" type="text/css">
            <link href="/assets/css/code.css" rel="stylesheet" type="text/css">
            <link href="/assets/css/theme.css" rel="stylesheet" type="text/css">
            %if has_custom_css:
                <link href="/assets/css/custom.css" rel="stylesheet" type="text/css">
            %endif
        %endif
        % if needs_ipython_css:
            <link href="/assets/css/ipython.min.css" rel="stylesheet" type="text/css">
            <link href="/assets/css/nikola_ipython.css" rel="stylesheet" type="text/css">
        % endif
    </%def>

And we will change it so it uses the lanyon styles instead of theme.css (again, ignore the bundles for now!):

.. code:: html+mako

    <%def name="html_stylesheets()">
        %if use_bundles:
            <link href="/assets/css/all.css" rel="stylesheet" type="text/css">
        %else:
            <link href="/assets/css/rst_base.css" rel="stylesheet" type="text/css">
            <link href="/assets/css/nikola_rst.css" rel="stylesheet" type="text/css">
            <link href="/assets/css/poole.css" rel="stylesheet" type="text/css">
            <link href="/assets/css/lanyon.css" rel="stylesheet" type="text/css">
            <link href="/assets/css/code.css" rel="stylesheet" type="text/css">
            %if has_custom_css:
                <link href="/assets/css/custom.css" rel="stylesheet" type="text/css">
            %endif
        %endif
        % if needs_ipython_css:
            <link href="/assets/css/ipython.min.css" rel="stylesheet" type="text/css">
            <link href="/assets/css/nikola_ipython.css" rel="stylesheet" type="text/css">
        % endif
        <link rel="stylesheet" href="https://fonts.googleapis.com/css?family=PT+Serif:400,400italic,700|PT+Sans:400">
    </%def>

.. figure:: https://getnikola.com/images/lanyon-1.thumbnail.png
   :target: https://getnikola.com/images/lanyon-1.png

   You may say this looks like crap. Don’t worry, we are just starting :-)

Page Layout
-----------

This is trickier but should be no problem for people with a basic understanding of HTML and a desire to make a theme!

Lanyon’s content is split in two parts: a sidebar and the rest. The sidebar looks like this (shortened for comprehension):

.. code:: html

    <body>
    <!-- Target for toggling the sidebar `.sidebar-checkbox` is for regular
         styles, `#sidebar-checkbox` for behavior. -->
    <input type="checkbox" class="sidebar-checkbox" id="sidebar-checkbox">

    <!-- Toggleable sidebar -->
    <div class="sidebar" id="sidebar">
        <div class="sidebar-item">
            <p>A reserved <a href="https://jekyllrb.com" target="_blank">Jekyll</a> theme that places the utmost gravity on content with a hidden drawer. Made by <a href="https://twitter.com/mdo" target="_blank">@mdo</a>.</p>
        </div>

        <nav class="sidebar-nav">
            <a class="sidebar-nav-item active" href="/">Home</a>
            <a class="sidebar-nav-item" href="/about/">About</a>
            [...]
        </nav>
    </div>

So, a plain body, with an input element that controls the sidebar, a div which is the sidebar itself.
Inside that, div.sidebar-item for items, and a nav with "navigational links". This is followed by the "masthead" and
the content itself, which we will look at in a bit.

If we look for the equivalent code in Nikola’s side, we see this:

.. code:: html

    <body>
    <a href="#content" class="sr-only sr-only-focusable">Skip to main content</a>
    <div id="container">
    <header id="header" role="banner">
    <h1 id="brand"><a href="https://example.com/" title="My Nikola Site" rel="home"> <span id="blog-title">My Nikola Site</span> </a></h1>
    <nav id="menu" role="navigation"><ul>
    <li><a href="../archive.html">Archive</a></li>
                    <li><a href="../categories/index.html">Tags</a></li>
                    <li><a href="../rss.xml">RSS feed</a></li>

So Nikola has the "masthead" above the nav element, and uses list elements in nav instead of bare links.
Not all that different is it?

Let’s make it lanyon-like! We will need 2 more templates: `base.tmpl <https://github.com/getnikola/nikola/blob/master/nikola/data/themes/base/templates/base.tmpl>`__ and `base_header.tmpl <https://github.com/getnikola/nikola/blob/master/nikola/data/themes/base/templates/base_header.tmpl>`__. Get them and put them in your ``themes/lanyon/templates`` folder.

Let’s look at ``base.tmpl`` first. It’s short and nice, it looks like a webpage without
all the interesting stuff:

.. code:: html+mako

    ## -*- coding: utf-8 -*-
    <%namespace name="base" file="base_helper.tmpl" import="*"/>
    <%namespace name="header" file="base_header.tmpl" import="*"/>
    <%namespace name="footer" file="base_footer.tmpl" import="*"/>
    ${set_locale(lang)}
    ${base.html_headstart()}
    <%block name="extra_head">
    ### Leave this block alone.
    </%block>
    ${template_hooks['extra_head']()}
    </head>
    <body>
    <a href="#content" class="sr-only sr-only-focusable">${messages("Skip to main content")}</a>
        <div id="container">
            ${header.html_header()}
            <main id="content" role="main">
                <%block name="content"></%block>
            </main>
            ${footer.html_footer()}
        </div>
        ${body_end}
        ${template_hooks['body_end']()}
        ${base.late_load_js()}
    </body>
    </html>

That link which says "Skip to main content" is very important for accessibility, so we will leave it in
place. But below, you can see how it creates the "container" div we see in the Nikola page, and the content is
created by ``html_header()`` which is defined in ``base_header.tmpl`` The actual ``nav`` element is done
by the ``html_navigation_links`` function out of the ``NAVIGATION_LINKS`` and ``NAVIGATION_ALT_LINKS`` options. (Let's put the alt links after regular ones; Bootstrap puts it on the right side, for example.)

So, first, lets change that base template to be more lanyon-like:

.. code:: html+mako

    ## -*- coding: utf-8 -*-
    <%namespace name="base" file="base_helper.tmpl" import="*"/>
    <%namespace name="header" file="base_header.tmpl" import="*"/>
    <%namespace name="footer" file="base_footer.tmpl" import="*"/>
    ${set_locale(lang)}
    ${base.html_headstart()}
    <%block name="extra_head">
    ### Leave this block alone.
    </%block>
    ${template_hooks['extra_head']()}
    </head>
    <body>
        <a href="#content" class="sr-only sr-only-focusable">${messages("Skip to main content")}</a>
        <!-- Target for toggling the sidebar `.sidebar-checkbox` is for regular
                styles, `#sidebar-checkbox` for behavior. -->
        <input type="checkbox" class="sidebar-checkbox" id="sidebar-checkbox">

        <!-- Toggleable sidebar -->
        <div class="sidebar" id="sidebar">
            <div class="sidebar-item">
                <p>A reserved <a href="https://getnikola.com" target="_blank" rel="noopener">Nikola</a> theme that places the utmost gravity on content with a hidden drawer. Made by <a href="https://twitter.com/mdo" target="_blank" rel="noopener">@mdo</a> for Jekyll,
                ported to Nikola by <a href="https://twitter.com/ralsina" target="_blank">@ralsina</a>.</p>
            </div>
            ${header.html_navigation_links()}
        </div>

        <main id="content" role="main">
            <%block name="content"></%block>
        </main>
        ${footer.html_footer()}
        ${body_end}
        ${template_hooks['body_end']()}
        ${base.late_load_js()}
    </body>
    </html>

.. figure:: https://getnikola.com/images/lanyon-2.thumbnail.png
   :target: https://getnikola.com/images/lanyon-2.png

   And that’s after I exposed the sidebar by clicking on an invisible widget!

One problem, which causes that yellow color in the sidebar is a CSS conflict.
We are loading ``rst_base.css`` which specifies
the background color of ``div.sidebar`` which is more specific than
``lanyon.css``, which specifies for ``.sidebar`` alone.

There are many ways to fix this, I chose to change lanyon.css to also use div.sidebar:

.. code:: css

    div.sidebar,.sidebar {
        position: fixed;
        top: 0;
        bottom: 0;
        left: -14rem;
        width: 14rem;
        [...]

This is annoying but it will happen when you just grab CSS from different places. The "Inspect Element"
feature of your web browser is your best friend for these situations.

Another problem is that the contents of the nav element are wrong. They are not bare links. We will fix that in
``base_header.html``, like this:

.. code:: html+mako

    <%def name="html_navigation_links()">
        <nav id="menu" role="navigation" class="sidebar-nav">
        %for url, text in navigation_links[lang]:
            <a class="sidebar-nav-item" href="${url}">${text}</a>
        %endfor
        ${template_hooks['menu']()}

        %for url, text in navigation_alt_links[lang]:
            <a class="sidebar-nav-item" href="${url}">${text}</a>
        %endfor
        ${template_hooks['menu_alt']()}
        </nav>
    </%def>

**Note: this means this theme will not support submenus in navigation. If you want that, I’ll happily take a patch.**

.. figure:: https://getnikola.com/images/lanyon-3.thumbnail.png
   :target: https://getnikola.com/images/lanyon-3.png

   Starting to see a resemblance?

Now let’s look at the content. In Lanyon, this is how the "main" content looks:

.. code:: html

    <!-- Wrap is the content to shift when toggling the sidebar. We wrap the
         content to avoid any CSS collisions with our real content. -->
    <div class="wrap">
      <div class="masthead">
        <div class="container">
          <h3 class="masthead-title">
            <a href="/" title="Home">Lanyon</a>
            <small>A Jekyll theme</small>
          </h3>
        </div>
      </div>

      <div class="container content">
        <div class="post">
            <h1 class="post-title">Introducing Lanyon</h1>
            <span class="post-date">02 Jan 2014</span>
            <p>Lanyon is an unassuming <a href="https://jekyllrb.com">Jekyll</a> theme [...]
        </div>
      </div>
    </div>
    <label for="sidebar-checkbox" class="sidebar-toggle"></label>
    </body>
    </html>

Everything inside the "container content" div is… the content. The rest is a masthead with the site title
and at the bottom a label for the sidebar toggle. Easy to do in ``base.tmpl``
(only showing the relevant part):

.. code:: html+mako

        <!-- Wrap is the content to shift when toggling the sidebar. We wrap the
            content to avoid any CSS collisions with our real content. -->
        <div class="wrap">
        <div class="masthead">
            <div class="container">
            <h3 class="masthead-title">
                <a href="/" title="Home">Lanyon</a>
                <small>A Jekyll theme</small>
            </h3>
            </div>
        </div>

        <div class="container content" id="content">
            <%block name="content"></%block>
        </div>
        </div>
        <label for="sidebar-checkbox" class="sidebar-toggle"></label>
        ${footer.html_footer()}
        ${body_end}
        ${template_hooks['body_end']()}
        ${base.late_load_js()}
    </body>
    </html>

.. figure:: https://getnikola.com/images/lanyon-4.thumbnail.png
   :target: https://getnikola.com/images/lanyon-4.png

   Getting there!

The sidebar looks bad because of yet more CSS conflicts with ``rst_base.css``. By
adding some extra styling in ``lanyon.css``, it will look better.

.. code:: css

    /* Style and "hide" the sidebar */
    div.sidebar, .sidebar {
      position: fixed;
      top: 0;
      bottom: 0;
      left: -14rem;
      width: 14rem;
      visibility: hidden;
      overflow-y: auto;
      padding: 0;
      margin: 0;
      border: none;
      font-family: "PT Sans", Helvetica, Arial, sans-serif;
      font-size: .875rem; /* 15px */
      color: rgba(255,255,255,.6);
      background-color: #202020;
      -webkit-transition: all .3s ease-in-out;
              transition: all .3s ease-in-out;
    }

Also, the accessibility link on top is visible when it should not. That’s
because we removed ``theme.css`` from the base theme, and with it, we lost a
couple of classes. We can add them in ``lanyon.css``, along with others used by other
pieces of the site:

.. code:: css

    .sr-only {
      position: absolute;
      width: 1px;
      height: 1px;
      padding: 0;
      margin: -1px;
      overflow: hidden;
      clip: rect(0, 0, 0, 0);
      border: 0;
    }

    .sr-only-focusable:active,
    .sr-only-focusable:focus {
      position: static;
      width: auto;
      height: auto;
      margin: 0;
      overflow: visible;
      clip: auto;
    }

    .breadcrumb {
      padding: 8px 15px;
      margin-bottom: 20px;
      list-style: none;
    }

    .breadcrumb > li {
      display: inline-block;
      margin-right: 0;
      margin-left: 0;
    }

    .breadcrumb > li:after {
      content: ' / ';
      color: #888;
    }

    .breadcrumb > li:last-of-type:after {
      content: '';
      margin-left: 0;
    }

    .thumbnails > li {
      display: inline-block;
      margin-right: 10px;
    }

    .thumbnails > li:last-of-type {
      margin-right: 0;
    }


.. figure:: https://getnikola.com/images/lanyon-5.thumbnail.png
   :target: https://getnikola.com/images/lanyon-5.png

   Little by little, things look better.

One clear problem is that the title "Lanyon · A Jekyll theme" is set in the
theme itself. We don’t do that sort of thing in Nikola, we have settings for
that. So, let’s use them. There is a ``html_site_title`` function in
``base_helper.tmpl`` which is just the thing. So we change base.tmpl to use it:

.. code:: html+mako

    <div class="wrap">
      <div class="masthead">
        <div class="container">
          ${header.html_site_title()}
        </div>
      </div>

That’s a ``<h1>`` instead of a ``<h3>`` like Lanyon does, but hey, it’s the
right thing to do. If you want to go with an ``<h3>``, just
change ``html_site_title`` itself.

And now we more or less have the correct page layout and styles. Except for a
rather large thing…

Typography
----------

You can see in the previous screenshot that text still looks quite different in our port: Serif versus Sans-Serif
content, and the titles have different colors!

Let’s start with the titles. Here’s how they look in Lanyon:

.. code:: html

          <h3 class="masthead-title">
            <a href="/" title="Home">Lanyon</a>
            <small>A Jekyll theme</small>
          </h3>

Versus our port:

.. code:: html

    <h1 id="brand"><a href="https://example.com/" title="My Nikola Site" rel="home">

So, it looks like we will have to fix ``html_site_title`` after all:

.. code:: html+mako

    <%def name="html_site_title()">
        <h3 id="brand" class="masthead-title">
        <a href="${_link("root", None, lang)}" title="${blog_title}" rel="home">${blog_title}</a>
        </h3>
    </%def>

As for the actual content, that’s not in any of the templates we have seen so far. The page you see is an
"index.tmpl" page, which means it’s a list of blog posts shown one below the
other. Obviously it’s not doing
things in the way the Lanyon CSS expects it to. Here’s the original, which you
can find in Nikola’s source
code:

.. code:: html+mako

    ## -*- coding: utf-8 -*-
    <%namespace name="helper" file="index_helper.tmpl"/>
    <%namespace name="comments" file="comments_helper.tmpl"/>
    <%inherit file="base.tmpl"/>

    <%block name="extra_head">
        ${parent.extra_head()}
        % if posts and (permalink == '/' or permalink == '/' + index_file):
            <link rel="prefetch" href="${posts[0].permalink()}" type="text/html">
        % endif
    </%block>

    <%block name="content">
    <%block name="content_header"></%block>
    <div class="postindex">
    % for post in posts:
        <article class="h-entry post-${post.meta('type')}">
        <header>
            <h1 class="p-name entry-title"><a href="${post.permalink()}" class="u-url">${post.title()|h}</a></h1>
            <div class="metadata">
                <p class="byline author vcard"><span class="byline-name fn">${post.author()}</span></p>
                <p class="dateline"><a href="${post.permalink()}" rel="bookmark"><time class="published dt-published" datetime="${post.date.isoformat()}" title="${post.formatted_date(date_format)}">${post.formatted_date(date_format)}</time></a></p>
                % if not post.meta('nocomments') and site_has_comments:
                    <p class="commentline">${comments.comment_link(post.permalink(), post._base_path)}
                % endif
            </div>
        </header>
        %if index_teasers:
        <div class="p-summary entry-summary">
        ${post.text(teaser_only=True)}
        %else:
        <div class="e-content entry-content">
        ${post.text(teaser_only=False)}
        %endif
        </div>
        </article>
    % endfor
    </div>
    ${helper.html_pager()}
    ${comments.comment_link_script()}
    ${helper.mathjax_script(posts)}
    </%block>


And this is how it looks after I played with it for a while, making it generate code that looks closer to
the Lanyon original:

.. code:: html+mako

    <%block name="content">
    <%block name="content_header"></%block>
    <div class="posts">
    % for post in posts:
        <article class="post h-entry post-${post.meta('type')}">
        <header>
            <h1 class="post-title p-name"><a href="${post.permalink()}" class="u-url">${post.title()|h}</a></h1>
            <div class="metadata">
                <p class="byline author vcard"><span class="byline-name fn">${post.author()}</span></p>
                <p class="dateline"><a href="${post.permalink()}" rel="bookmark"><time class="post-date published dt-published" datetime="${post.date.isoformat()}" title="${post.formatted_date(date_format)}">${post.formatted_date(date_format)}</time></a></p>
                % if not post.meta('nocomments') and site_has_comments:
                    <p class="commentline">${comments.comment_link(post.permalink(), post._base_path)}
                % endif
            </div>
        </header>
        %if index_teasers:
        <div class="p-summary entry-summary">
        ${post.text(teaser_only=True)}
        %else:
        <div class="e-content entry-content">
        ${post.text(teaser_only=False)}
        %endif
        </div>
        </article>
    % endfor
    </div>
    ${helper.html_pager()}
    ${comments.comment_link_script()}
    ${helper.mathjax_script(posts)}
    </%block>

With these changes, it looks… similar?

.. figure:: https://getnikola.com/images/lanyon-6.thumbnail.png
   :target: https://getnikola.com/images/lanyon-6.png

   It does!

Similar changes (basically adding class names to elements) needed to be done in ``post_header.tmpl``:

.. code:: html+mako

    <%def name="html_post_header()">
        <header>
            ${html_title()}
            <div class="metadata">
                <p class="byline author vcard"><span class="byline-name fn">${post.author()}</span></p>
                <p class="dateline"><a href="${post.permalink()}" rel="bookmark"><time class="post-date published dt-published" datetime="${post.date.isoformat()}" itemprop="datePublished" title="${post.formatted_date(date_format)}">${post.formatted_date(date_format)}</time></a></p>
                % if not post.meta('nocomments') and site_has_comments:
                    <p class="commentline">${comments.comment_link(post.permalink(), post._base_path)}
                % endif
                %if post.description():
                    <meta name="description" itemprop="description" content="${post.description()}">
                %endif
            </div>
            ${html_translations(post)}
        </header>
    </%def>

Customization
-------------

The original Lanyon theme supports some personalization options. It suggests you do them by tweaking the templates, and
you *can* also do that in the Nikola port. But we prefer to use options for that, so that you can get a later, better
version of the theme and it will still "just work".

Let’s see the color schemes first. They apply easily, just tweak your ``body`` element like this:

.. code:: html

    <body class="theme-base-08">
    ...
    </body>

We can tweak ``base.tmpl`` to do just that:

.. code:: html+mako

    % if lanyon_subtheme:
    <body class="${lanyon_subtheme}">
    %else:
    <body>
    %endif

And then we can put the options in conf.py’s ``GLOBAL_CONTEXT``:

.. code:: python

    GLOBAL_CONTEXT = {
        "lanyon_subtheme": "theme-base-08"
    }

.. figure:: https://getnikola.com/images/lanyon-7.thumbnail.png
   :target: https://getnikola.com/images/lanyon-7.png

   Look at it, all themed up.

Doing the same for layout-reverse, sidebar-overlay and the rest is left as an exercise for the reader.

Bundles
-------

If the ``USE_BUNDLES`` option set to True,
Nikola can put several CSS or JS files together in a larger file, which can
makes site load faster for some deployments. To do this, your theme needs
a ``bundles`` file. The file format is a modified
`config <https://docs.python.org/3/library/configparser.html>`_ file with no
defined section; the basic syntax is::

    outputfile1.js=
        thing1.js,
        thing2.js,
        ...
    outputfile2.css=
        thing1.css,
        thing2.css,
        ...

For the Lanyon theme, it should look like this::

    assets/css/all.css=
        rst_base.css,
        nikola_rst.css,
        code.css,
        poole.css,
        lanyon.css,
        custom.css,

**Note:** trailing commas are optional

**Note:** Some themes also support the ``USE_CDN`` option meaning that in some cases it will load one bundle with all CSS and in other will load some CSS files
from a CDN and others from a bundle. This is complicated and probably not worth the effort.

The End
-------

And that’s it, that’s a whole theme. Eventually, once people start using it, they will notice small broken details, which will need handling one at a time.

This theme should be available in https://themes.getnikola.com/v7/lanyon/ and you can see it in action at https://themes.getnikola.com/v7/lanyon/demo/ .

What if you want to extend other parts of the theme? Check out the :doc:`Theming reference <theming>`. You can also contribute your improvements to the `nikola-themes <https://github.com/getnikola/nikola>` repository on GitHub.
