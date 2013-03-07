Extra Plugins
=============

These are plugins that may not be widely used or that are a bit too radical or 
experimental for the general public.

To enable them for you, create a ``plugins/`` folder in your site, and copy
both the ``.plugin`` file and the matching ``.py`` file or folder.

Planetoid
---------

This plugin converts Nikola into the equivalent of `Planet <http://www.planetplanet.org/>`_
a feed aggregator. It requires `PeeWee <https://github.com/coleifer/peewee>`_ and
`Feedparser <http://code.google.com/p/feedparser/>`_ to work.

It has a configuration option: PLANETOID_REFRESH which is the number of minutes
before retrying a feed (defaults to 60).

You need to create a ``feeds`` file containing the data of which feeds you want to
aggregate. The format is very simple::

   # Roberto Alsina
   http://feeds2.feedburner.com/PostsInLateralOpinionAboutPython
   Roberto Alsina

#. Lines that start with ``#`` are comments and ignored.
#. Lines that start with http are feed URLs.
#. URL lines have to be followed by the "real name" of the feed.

FIXME: explain the planetoid theme stuff

After all that is in place, just run ``nikola build`` and you'll get 
a planet.

Local Search
------------

If you don't want to depend on google or duckduckgo to implement search for you,
or just want it to wok even if you are offline, enable this plugin and the
search will be performed client side.

This plugin implements a Tipue-based local search for your site.

To use it, copy task_localsearch.plugin and task_localsearch
into a plugins/ folder in your nikola site.

After you build your site, you will have several new files in assets/css and assets/js
and a search.html that you can use as a basis for using this in your site.

For more information about how to customize it and use it, please refer to the tipue
docs at http://www.tipue.com/search/

Tipue is under an MIT license (see MIT-LICENSE.txt)


Mustache
--------

This task gives you a ``mustache.html`` file which lets you access your whole
blog without reloading the page, using client-side templates. Makes it much
faster and modern ;-)
