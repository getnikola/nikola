.. title: Nikola Internals
.. slug: internals
.. date: 2012-03-30 23:00:00 UTC-03:00
.. tags:
.. link:
.. description:
.. author: The Nikola Team

.. class:: lead

When trying to guide someone into adding a feature in Nikola, it hit me that
while the way it's structured makes sense **to me** it is far from obvious.

So, this is a short document explaining what each piece of Nikola does and
how it all fits together.

Nikola is a Pile of Plugins
    Most of Nikola is implemented as plugins using `Yapsy <http://yapsy.sourceforge.net/>`_.
    You can ignore that they are plugins and just think of them as regular python
    modules and packages with a funny little ``.plugin`` file next to them.

    So, 90% of the time, what you want to do is either write a new plugin or extend
    an existing one.

    There are several kinds of plugins, all implementing interfaces defined in
    ``nikola/plugin_categories.py`` and documented in
    `Extending Nikola <https://getnikola.com/extending.html>`_

    If your plugin has a dependency, please make sure it doesn't make Nikola
    throw an exception when the dependency is missing. Try to fail gracefully
    with an informative message.

Commands are plugins
    When you use ``nikola foo`` you are using the plugin ``command/foo``. Those are
    used to extend Nikola's command line. Their interface is defined in the ``Command``
    class. They take options and arguments and do whatever you want, so go wild.

The ``build`` command is special
    The ``build`` command triggers a whole lot of things, and is the core of Nikola
    because it's the one that you use to build sites. So it deserves its own section.

The Build Command
-----------------

Nikola's goal is similar, deep at heart, to a Makefile. Take sources, compile them
into something, in this case a website. Instead of a Makefile, Nikola uses
`doit <https://pydoit.org>`_

Doit has the concept of "tasks". The 1 minute summary of tasks is that they have:

actions
    What the task **does**. For example, convert a markdown document into HTML.

dependencies
    If this file changes, then we need to redo the actions. If this configuration
    option changes, redo it, etc.

targets
    Files that the action generates. No two actions can have the same targets.

basename:name
    Each task is identified by either a name or a basename:name pair.

.. sidebar:: More about tasks

   If you ever want to do your own tasks, you really should read the doit
   `documentation on tasks <https://pydoit.org/tasks.html>`_

So, what Nikola does, when you use the build command, is to read the
configuration ``conf.py`` from the current folder, instantiate
the ``Nikola`` class, and have it generate a whole list of tasks for doit
to process. Then doit will decide which tasks need doing, and do them, in
the right order.

The place where the tasks are generated is in ``Nikola.gen_tasks``, which collects tasks
from all the plugins inheriting ``BaseTask``, massages them a bit, then passes them
to doit.

So, if you want things to happen on ``build`` you want to create a Task plugin, or extend
one of the existing ones.

.. sidebar:: Tests

    While Nikola is not a hardcore TDD project, we like tests. So, please add them if you can.
    You can write unit tests or integration tests. (Doctests are not supported
    anymore due to fragility.)

Posts and Pages
---------------

Nikola has a concept of posts and pages. Both are more or less the same thing, except
posts are added into RSS feeds and pages are not. All of them are in a list called
"the timeline" formed by objects of class ``Post``.

When you are creating a task that needs the list of posts and/or pages (for example,
the RSS creation plugin) on task execution time, your plugin should call ``self.site.scan_posts()``
in ``gen_tasks`` to ensure the timeline is created and available in
``self.site.timeline``. You should not modify the timeline, because it will cause consistency issues.

.. sidebar:: scan_posts

   The ``Nikola.scan_posts`` function can be used in plugins to force the
   timeline creation, for example, while creating the tasks.

Your plugin can use the timeline to generate "stuff" (technical term). For example,
Nikola comes with plugins that use the timeline to create a website (surprised?).

The workflow included with nikola is as follows (incomplete!):

#. The post is assigned a compiler based on its extension and the ``COMPILERS`` option.
#. The compiler is applied to the post data and a "HTML fragment" is produced. That
   fragment is stored in a cache (the ``posts`` plugin).
#. The configured theme has templates (and a template engine), which are applied to the post's
   HTML fragment and metadata (the ``pages`` plugin).
#. The original sources for the post are copied to some accessible place (the ``sources`` plugin).
#. If the post is tagged, some pages and RSS feeds for each tag are updated (the ``tags`` plugin).
#. If the post is new, it's included in the blog's RSS feed (the ``rss`` plugin).
#. The post is added in the right place in the index pages for the blog (the ``indexes`` plugin).
#. CSS/JS/Images for the theme are put in the right places (the ``copy_assets`` and ``bundles`` plugins).
#. A File describing the whole site is created (the ``sitemap`` plugin).

You can add whatever you want to that list: just create a plugin for it.

You can also expand Nikola's capabilities at several points:

compilers
    Nikola supports a variety of markups. If you want to add another one, you need to create
    a ``Compiler`` plugin.

templates
    Nikola's themes can use Jinja2 or Mako templates. If you prefer another template system,
    you have to create a ``TemplateSystem`` plugin.

themes
    To change how the generated site looks, you can create custom themes.

And of course, you can also replace or extend each of the existing plugins.

Nikola Architecture
===================

.. thumbnail:: https://getnikola.com/images/architecture.png
