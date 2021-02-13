.. title: Using Alternative Social Buttons with Nikola
.. slug: social_buttons
.. date: 2013-08-19 23:00:00 UTC-03:00
.. tags:
.. link:
.. description:
.. author: The Nikola Team

:Version: 8.1.3

.. class:: alert alert-primary float-md-right

.. contents::


The Default
-----------

By Default, the themes provided with Nikola will add to your pages a "slide in" widget at
the bottom right of the page, provided by Addthis. This is the HTML code for that:

.. code-block:: html

    <!-- Social buttons -->
    <div id="addthisbox" class="addthis_toolbox addthis_peekaboo_style
        addthis_default_style addthis_label_style addthis_32x32_style">
    <a class="addthis_button_more">Share</a>
    <ul><li><a class="addthis_button_facebook"></a>
    <li><a class="addthis_button_google_plusone_share"></a>
    <li><a class="addthis_button_linkedin"></a>
    <li><a class="addthis_button_twitter"></a>
    </ul>
    </div>
    <script src="//s7.addthis.com/js/300/addthis_widget.js#pubid=ra-4f7088a56bb93798"></script>
    <!-- End of social buttons -->
    """

You can change that using the ``SOCIAL_BUTTONS_CODE`` option in your conf.py. In some cases, just
doing that will be enough but in others, it won't. This document tries to describe all the bits
involved in making this work correctly.

Part 1: ``SOCIAL_BUTTONS_CODE``
    Social sharing services like addthis and others will provide you a HTML snippet.
    If it is self-contained, then just setting ``SOCIAL_BUTTONS_CODE`` may be enough.
    Try :-)

Part 2: The theme
    The ``SOCIAL_BUTTONS_CODE`` HTML fragment will be embedded *somewhere* by the theme. Whether that
    is the correct place or not is not something the theme author can truly know, so it is possible that
    you may have to tweak the ``base.html`` template to make it look good.

Part 3: ``BODY_END`` and ``EXTRA_HEAD_DATA``
    Some social sharing code requires JS execution that depends on JQuery being available
    (example: `SocialSharePrivacy <https://github.com/panzi/SocialSharePrivacy>`__). It's good
    practice (and often, the only way that will work) to put those at the end of ``<BODY>``,
    and one easy way to do that is to put them in ``BODY_END``

    On the other hand, it's possible that it requires you to load some CSS files.
    The right place for that is in the document's ``<HEAD>`` so they should be added
    in ``EXTRA_HEAD_DATA``

Part 4: assets
    For sharing code that doesn't rely on a social sharing service, you may need to add CSS, Image, or JS
    files to your site

ShareNice
---------

`ShareNice <https://graingert.co.uk/shareNice/>`__ is "written in order to provide social sharing features to
web developers and website administrators who wish to maintain and protect their users' privacy"
which sounds cool to me.

Let's go step by step into integrating the hosted version of ShareNice into a Nikola site.

For testing purposes, let's do it on a demo site::

    $ nikola init --demo sharenice_test
    A new site with example data has been created at sharenice_test.
    See README.txt in that folder for more information.
    $ cd sharenice_test/

To see what's going on, let's start Nikola in "auto mode". This should build the
site and open a web browser showing the default configuration, with the AddThis widget::

    $ nikola auto -b

First, let's add the HTML snippet that will show the sharing options. In your conf.py, set this, which
is the HTML code suggested by ShareNice:

.. code-block:: python

    SOCIAL_BUTTONS_CODE = """<div id="shareNice" data-share-label="Share"
        data-color-scheme="black" data-icon-size="32" data-panel-bottom="plain"
        data-services="plus.google.com,facebook.com,digg.com,email,delicious.com,twitter.com"
        style="float:right"></div>"""

    BODY_END = """<script src="https://graingert.co.uk/shareNice/code.js"></script>"""

And you should now see a sharing box at the bottom right of the page.

Main problem remaining is that it doesn't really look good and integrated in the page layout.
I suggest changing the code to this which looks nicer, but still has some placement issues:

.. code-block:: python

    SOCIAL_BUTTONS_CODE = """<div id="shareNice" data-share-label="Share"
        data-color-scheme="black" data-icon-size="32" data-panel-bottom="plain"
        data-services="plus.google.com,facebook.com,email,twitter.com"
        style="position: absolute; left: 20px; top: 60px;"></div>"""

If anyone comes up with a better idea of styling/placement, just let me know ;-)

One bad bit of this so far is that you are now using a script from another site, and that
doesn't let Nikola perform as many optimizations to your page as it could.
So, if you really want to go the extra mile to save a few KB and round trips, you *could*
install your own copy from the `github repo <https://github.com/mischat/shareNice>`_ and
use that instead of the copy at `ShareNice <https://graingert.co.uk/shareNice>`_.

Then, you can create your own theme inheriting from the one you are using and add the CSS
and JS files from ShareNice into your ``bundles`` configuration so they are combined and
minified.

SocialSharePrivacy
------------------

The Hard Way
~~~~~~~~~~~~

`SocialSharePrivacy <https://github.com/panzi/SocialSharePrivacy>`__ is "a jQuery plugin that
lets you add social share buttons to your website that don't allow the social sites to track
your users." Nice!

Let's go step-by-step into integrating SocialSharePrivacy into a Nikola site. To improve
privacy, they recommend you not use the hosted service so we'll do it the hard way, by
getting and distributing everything in our own site.

https://github.com/panzi/SocialSharePrivacy

For testing purposes, let's do it on a demo site::

    $ nikola init --demo ssp_test
    A new site with example data has been created at ssp_test.
    See README.txt in that folder for more information.
    $ cd ssp_test/

To see what's going on, let's start Nikola in "auto mode". This should build the
site and open a web browser showing the default configuration, with the AddThis widget::

    $ nikola auto -b

Now, download `the current version <https://github.com/panzi/SocialSharePrivacy/archive/master.zip>`_
and unzip it. You will have a ``SocialSharePrivacy-master`` folder with lots of stuff in it.

First, we need to build it (this requires a working and modern uglifyjs, this may not be easy)::

    $ cd SocialSharePrivacy-master
    $ sh build.sh -m gplus,twitter,facebook,mail -s "/assets/css/socialshareprivacy.css" -a off

You will now have several files in a ``build`` folder. We need to bring them into the site::

    $ cp -Rv SocialSharePrivacy-master/build/* files/
    $ cp -R SocialSharePrivacy-master/images/ files/assets/

Edit your ``conf.py``:

.. code-block:: python

    BODY_END = """
    <script src="/javascripts/jquery.socialshareprivacy.min.js"></script>
    <script>
    $(document).ready(function () {
        $('.share').socialSharePrivacy();
    });
    </script>
    """

    SOCIAL_BUTTONS_CODE = """<div class="share"></div>"""

In my experience this produces a broken, duplicate, semi-working thing. YMMV and if you make it work correctly, let me know how :-)

The Easy Way
~~~~~~~~~~~~

Go to https://panzi.github.io/SocialSharePrivacy/ and use the provided form to get the code. Make sure you check "I already use JQuery"
if you are using one of the themes that require it, like site or default, select the services you want, and use your disqus name if
you have one.

It will give you 3 code snippets:

"Insert this once in the head of your page"
    Put it in ``BODY_END``

"Insert this wherever you want a share widget displayed"
    Put it in ``SOCIAL_BUTTONS_CODE``

"Insert this once anywhere after the other code"
    Put it in ``BODY_END``

That should give you a working integration (not tested)
