.. title: Creating a Theme
.. slug: creating-a-theme
.. date: 2012-03-13 12:00:00 UTC-03:00
.. tags:
.. link:
.. description:

Creating A Theme From Scratch (Almost)
======================================

.. class:: lead

There is some documentation about creating themes for Nikola, but maybe a tutorial is also a useful way
to explain it. So, here it is. I'll explain how to create a theme (almost) from scratch. All themes
in Nikola must inherit from the ``base`` theme. In this case, we will inherit from ``bootstrap``
so we get good support for slides and galleries.

I will try to create a theme that looks like `Vinicius Massuchetto's Monospace Theme <http://wordpress.org/themes/monospace>`_.

.. TEASER_END

Starting The Theme
------------------

First we will create a testing site::

    $ nikola init --demo monospace-site
    A new site with some sample data has been created at monospace-site.
    See README.txt in that folder for more information.

    $ cd monospace-site/

Our theme will inherit from the ``bootstrap`` theme, which is full-featured but boring.

::

    $ mkdir themes
    $ mkdir themes/monospace
    $ echo bootstrap > themes/monospace/parent

The next step is to make the testing site use this new theme, by editing ``conf.py`` and
changing the ``THEME`` option::

    # Name of the theme to use. Themes are located in themes/theme_name
    THEME = 'monospace'

Now we can already build and test the site::

    $ nikola build && nikola serve

.. figure:: http://ralsina.com.ar/galleries/monospace-tut/monospace-1.png
   :height: 400px

   This is the default "bootstrap" theme.

Of course, the page layout is completely different from what we want. To fix that, we need to
get into templates.

Templates: Page Layout
----------------------

The general page layout for the theme is done by the ``base.tmpl`` template, which is done using
`Mako <http://www.makotemplates.org/>`_. This is bootstrap's ``base.tmpl``, it's not very big:

.. code-block:: mako

    ## -*- coding: utf-8 -*-
    <%namespace name="base" file="base_helper.tmpl" import="*" />
    <%namespace name="bootstrap" file="bootstrap_helper.tmpl" import="*" />
    ${set_locale(lang)}
    <!DOCTYPE html>
    <html% if comment_system == 'facebook': xmlns:fb="http://ogp.me/ns/fb#" %endif lang="${lang}">
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        ${bootstrap.html_head()}
        <%block name="extra_head">
        </%block>
        ${extra_head_data}
    </head>
    <body>
    <!-- Menubar -->
    <div class="navbar navbar-fixed-top" id="navbar">
        <div class="navbar-inner">
            <div class="container">

            <!-- .btn-navbar is used as the toggle for collapsed navbar content -->
            <a class="btn btn-navbar" data-toggle="collapse" data-target=".nav-collapse">
                <span class="icon-bar"></span>
                <span class="icon-bar"></span>
                <span class="icon-bar"></span>
            </a>

                <a class="brand" href="${abs_link('/')}">
                ${blog_title}
                </a>
                <!-- Everything you want hidden at 940px or less, place within here -->
                <div class="nav-collapse collapse">
                    <ul class="nav">
                        ${bootstrap.html_navigation_links()}
                    </ul>
                    %if search_form:
                        ${search_form}
                    %endif
                    <ul class="nav pull-right">
                    <%block name="belowtitle">
                    %if len(translations) > 1:
                        <li>${base.html_translations()}</li>
                    %endif
                    </%block>
                    % if show_sourcelink:
                        <li><%block name="sourcelink"></%block></li>
                    %endif
                    </ul>
                </div>
            </div>
        </div>
    </div>
    <!-- End of Menubar -->
    <div class="container-fluid" id="container-fluid">
        <!--Body content-->
        <div class="row-fluid">
        <div class="span2"></div>
        <div class="span8">
        <%block name="content"></%block>
        </div>
        </div>
        <!--End of body content-->
    </div>
    <div class="footerbox">
        ${content_footer}
    </div>
    ${bootstrap.late_load_js()}
    ${base.html_social()}
        <script>jQuery("a.image-reference").colorbox({rel:"gal",maxWidth:"100%",maxHeight:"100%",scalePhotos:true});
        $(window).on('hashchange', function(){
            if (location.hash && $(location.hash)[0]) {
                $('body').animate({scrollTop: $(location.hash).offset().top - $('#navbar').outerHeight(true)*1.2 }, 1);
            }
        });
        $(document).ready(function(){$(window).trigger('hashchange')});
        </script>
    <%block name="extra_js"></%block>
    ${body_end}
    </body>


It's basically a HTML document with some placeholders to be replaced with actual content, configuration options, and some helper functions.
For example, the ``html_head`` helper can be used to add CSS or JS files in all document's ``head`` tags.

Monospace is a two-column-with-footer layout, so let's copy the basics from its HTML and see what happens:

.. code-block:: mako

    ## -*- coding: utf-8 -*-
    <%namespace name="base" file="base_helper.tmpl" import="*"/>
    <%namespace name="bootstrap" file="bootstrap_helper.tmpl" import="*" />
    ${set_locale(lang)}
    <!DOCTYPE html>
    <html lang="${lang}">
    <head>
        ${bootstrap.html_head()}
        <%block name="extra_head">
        </%block>
        ${extra_head_data}
    </head>
    <body class="home blog">
        <div id="wrap" style="width:850px">
            <div id="container" style="width:560px">
                <%block name="content"></%block>
            </div>
            <div id="sidebar">
                <!--Sidebar content-->
                <h1 id="blog-title">
                    <a href="${abs_link('/')}" title="${blog_title}">${blog_title}</a>
                </h1>
                <%block name="belowtitle">
                %if len(translations) > 1:
                <small>
                    ${(messages("Also available in"))}:&nbsp;
                    ${base.html_translations()}
                </small>
                %endif
                </%block>
                <ul class="unstyled">
                <li>${license}
                ${base.html_social()}
                ${bootstrap.html_navigation_links()}
                <li>${search_form}
                </ul>
            </div>
            <div id="footer">
                ${content_footer}
            </div>
        </div>
        ${bootstrap.late_load_js()}
        <script>jQuery("a.image-reference").colorbox({rel:"gal",maxWidth:"100%",maxHeight:"100%",scalePhotos:true});</script>
        <%block name="extra_js"></%block>
        ${body_end}
    </body>

.. figure:: http://ralsina.com.ar/galleries/monospace-tut/monospace-2.png

   Yikes!

This will get better quickly once we add some CSS


Base CSS
--------

The orphan theme includes just a little styling, specifically ``rest.css`` so
the reStructuredText output looks reasonable, and ``code.css`` for code snippets.

It also includes an empty ``assets/css/theme.css`` where you can add your own CSS.
For example, this is taken from the original monospace theme, except for the last
few selectors:

.. code-block:: css

    body { margin:0px; padding:20px 0px; text-align:center; font-family:Monospace; color:#585858; }
    .post { margin:0px 0px 30px 0px; padding:0px 0px 30px 0px; border-bottom:1px dotted #C8C8C8; }
    .meta { margin:10px; padding:15px; background:#EAEAEA; clear:both; }
    #footer { text-align:center; clear:both; margin:30px 0px 0px 0px; padding:30px 0px 0px 0px; border-top:1px dotted #C8C8C8; }
    #wrap { margin:0px auto; text-align:left; font-size: 13px; line-height: 1.4; }
    #container { float:right; }
    #sidebar { overflow:hidden; clear:left; text-align:right; width:250px; height:auto; padding:0px 15px 0px 0px; border-right:1px dotted #C8C8C8; }
    #sidebar li { list-style-type:none; }
    #sidebar > li { margin:20px 0px; }
    #sidebar h1 { border-bottom:1px dotted #C8C8C8; }
    #sidebar .description { display:block; width:100%; height:auto; margin:0px 0px 10px 0px; }
    h1, h2, h3, h4, h5, h6, h7 { margin:0px; text-transform:uppercase; }
    h4, h5, h6 { font-size:14px; }
    #blog-title { margin-top: 0; line-height:48px;}
    .literal-block {padding: .5em;}
    div.sidebar, div.admonition, div.attention, div.caution, div.danger, div.error, div.hint, div.important, div.note, div.tip, div.warning {
        /* Issue 277 */
        border: 1px solid #aaa;
        border-radius: 5px;
        width: 100%;
    }
    ul.breadcrumb > li:before {
        content: " / ";
    }

This will (after we rebuild it) make the site looks different of course, and getting closer to our goal:

.. figure:: http://ralsina.com.ar/galleries/monospace-tut/monospace-3.png
   :height: 400px

   Monospaced allright.

If you compare it to `the original <http://wp-themes.com/monospace/>`_, however, you will see that the layout of
the posts themselves is different, and that was not described in ``base.tmpl`` at all. But if you look, you'll see that
there is a placeholder called content: ``<%block name="content"></%block>``

That's because ``base.tmpl`` defines the *base* layout. The layout of more specific pages, like "the page that shows
a list of posts" is defined in the other templates. Specifically, this is defined in ``index.tmpl``.
It turns out ``bootstrap`` doesn' have one of those! That's because it inherits that template from ``base``:

.. code-block:: mako

    ## -*- coding: utf-8 -*-
    <%namespace name="helper" file="index_helper.tmpl"/>
    <%namespace name="comments" file="comments_helper.tmpl"/>
    <%inherit file="base.tmpl"/>
    <%block name="content">
        % for post in posts:
            <div class="postbox post-${post.meta('type')}">
            <h1><a href="${post.permalink()}">${post.title()}</a>
            <small>&nbsp;&nbsp;
                ${messages("Posted")}: <time class="published" datetime="${post.date.isoformat()}">${post.formatted_date(date_format)}</time>
            </small></h1>
            <hr>
            ${post.text(teaser_only=index_teasers)}
            % if not post.meta('nocomments'):
                ${comments.comment_link(post.permalink(), post.base_path)}
            % endif
            </div>
        % endfor
        ${helper.html_pager()}
        ${comments.comment_link_script()}
        ${helper.mathjax_script(posts)}
    </%block>

So, let's tweak that to be closer to the original. We put the post's metadata in a
box, add links for the posts tags, move the date there, etc.

.. code-block:: mako

    ## -*- coding: utf-8 -*-
    <%namespace name="helper" file="index_helper.tmpl"/>
    <%namespace name="disqus" file="disqus_helper.tmpl"/>
    <%inherit file="base.tmpl"/>
    <%block name="content">
        % for post in posts:
            <div class="postbox post-${post.meta('type')}">
            <h1><a href="${post.permalink()}">${post.title()}</a></h1>
                <div class="meta" style="background-color: rgb(234, 234, 234); ">
                    <span class="authordate">
                        ${messages("Posted")}: ${post.formatted_date(date_format)}
                    </span>
                    <br>
                    <span class="tags">Tags:&nbsp;
                        %if post.tags:
                            %for tag in post.tags:
                                <a class="tag" href="${_link('tag', tag)}"><span>${tag}</span></a>
                            %endfor
                        %endif
                    </span>
                </div>
            ${post.text(teaser_only=index_teasers)}
            % if not post.meta('nocomments'):
                ${disqus.html_disqus_link(post.permalink()+"#disqus_thread", post.base_path)}
            % endif
            </div>
        % endfor
        ${helper.html_pager()}
        ${disqus.html_disqus_script()}
    </%block>


.. figure:: http://ralsina.com.ar/galleries/monospace-tut/monospace-4.png
   :height: 400px

   Close enough!

Then if we click on the post title, we will see some broken details in the metadata that can be fixed in ``post.tmpl``, and so on.

.. code-block:: mako

    ## -*- coding: utf-8 -*-
    <%namespace name="helper" file="post_helper.tmpl"/>
    <%namespace name="disqus" file="disqus_helper.tmpl"/>
    <%inherit file="base.tmpl"/>
    <%block name="extra_head">
    ${helper.twitter_card_information(post)}
    % if post.meta('keywords'):
        <meta name="keywords" content="${post.meta('keywords')|h}"/>
    % endif
    </%block>
    <%block name="content">
        <div class="post">
        ${helper.html_title()}
            <div class="meta" style="background-color: rgb(234, 234, 234); ">
            <span class="authordate">
                ${messages("Posted")}: ${post.formatted_date(date_format)}
                % if not post.meta('password'):
                [<a href="${post.source_link()}" id="sourcelink">${messages("Source")}</a>]
                % endif
            </span>
            <br>
                %if post.tags:
                    <span class="tags">${messages("Tags")}:&nbsp;
                    %for tag in post.tags:
                        <a class="tag" href="${_link('tag', tag)}"><span>${tag}</span></a>
                    %endfor
                    </span>
                    <br>
                %endif
            <span class="authordate">
                ${helper.html_translations(post)}
            </span>
            </div>
        ${post.text()}
        ${helper.html_pager(post)}
        % if not post.meta('nocomments'):
            ${disqus.html_disqus(post.permalink(absolute=True), post.title(), post.base_path)}
        % endif
        </div>
    </%block>


.. figure:: http://ralsina.com.ar/galleries/monospace-tut/monospace-5.png
   :height: 400px

   Details, details.

The demo site exercises most of the features in Nikola, so if you make it look good, your site probably will look good too.
This monospace theme is included with nikola, if you want to use it or play with it.

