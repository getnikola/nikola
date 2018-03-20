.. title: Extending Nikola
.. slug: extending
.. date: 2012-03-30 23:00:00 UTC-03:00
.. tags:
.. link:
.. description:
.. author: The Nikola Team

Extending Nikola
================

:Version: 7.8.8
:Author: Roberto Alsina <ralsina@netmanagers.com.ar>

.. class:: alert alert-info float-md-right

.. contents::


.. class:: lead

Nikola is extensible. Almost all its functionality is based on plugins,
and you can add your own or replace the provided ones.

Plugins consist of a metadata file (with ``.plugin`` extension) and
a Python module (a ``.py`` file) or package (a folder containing
a ``__init__.py`` file.

To use a plugin in your site, you just have to put it in a ``plugins``
folder in your site.

Plugins come in various flavours, aimed at extending different aspects
of Nikola.

Command Plugins
---------------

When you run ``nikola --help`` you will see something like this:

.. code-block:: console

    $ nikola help
    Nikola is a tool to create static websites and blogs. For full documentation and more
    information, please visit https://getnikola.com/


    Available commands:
    nikola auto                 automatically detect site changes, rebuild
                                and optionally refresh a browser
    nikola bootswatch_theme     given a swatch name from bootswatch.com and a
                                parent theme, creates a custom theme
    nikola build                run tasks
    nikola check                check links and files in the generated site
    nikola clean                clean action / remove targets
    nikola console              start an interactive python console with access to
                                your site and configuration
    nikola deploy               deploy the site
    nikola dumpdb               dump dependency DB
    nikola forget               clear successful run status from internal DB
    nikola help                 show help
    nikola ignore               ignore task (skip) on subsequent runs
    nikola import_blogger       import a blogger dump
    nikola import_feed          import a RSS/Atom dump
    nikola import_wordpress     import a WordPress dump
    nikola init                 create a Nikola site in the specified folder
    nikola list                 list tasks from dodo file
    nikola mincss               apply mincss to the generated site
    nikola new_post             create a new blog post or site page
    nikola run                  run tasks
    nikola serve                start the test webserver
    nikola strace               use strace to list file_deps and targets
    nikola theme                manage themes
    nikola version              print the Nikola version number

    nikola help                 show help / reference
    nikola help <command>       show command usage
    nikola help <task-name>     show task usage

That will give you a list of all available commands in your version of Nikola.
Each and every one of those is a plugin. Let's look at a typical example:

First, the ``serve.plugin`` file:

.. code-block:: ini

    [Core]
    Name = serve
    Module = serve

    [Documentation]
    Author = Roberto Alsina
    Version = 0.1
    Website = https://getnikola.com
    Description = Start test server.

.. note:: If you want to publish your plugin on the Plugin Index, `read
          the docs for the Index
          <https://github.com/getnikola/plugins/blob/master/README.md>`__
          (and the .plugin file examples and explanations).

For your own plugin, just change the values in a sensible way. The
``Module`` will be used to find the matching Python module, in this case
``serve.py``, from which this is the interesting bit:

.. code-block:: python

    from nikola.plugin_categories import Command

    # You have to inherit Command for this to be a
    # command plugin:

    class CommandServe(Command):
        """Start test server."""

        name = "serve"
        doc_usage = "[options]"
        doc_purpose = "start the test webserver"

        cmd_options = (
            {
                'name': 'port',
                'short': 'p',
                'long': 'port',
                'default': 8000,
                'type': int,
                'help': 'Port number (default: 8000)',
            },
            {
                'name': 'address',
                'short': 'a',
                'long': '--address',
                'type': str,
                'default': '127.0.0.1',
                'help': 'Address to bind (default: 127.0.0.1)',
            },
        )

        def _execute(self, options, args):
            """Start test server."""
            out_dir = self.site.config['OUTPUT_FOLDER']
            if not os.path.isdir(out_dir):
                print("Error: Missing '{0}' folder?".format(out_dir))
            else:
                os.chdir(out_dir)
                httpd = HTTPServer((options['address'], options['port']),
                                OurHTTPRequestHandler)
                sa = httpd.socket.getsockname()
                print("Serving HTTP on", sa[0], "port", sa[1], "...")
                httpd.serve_forever()

As mentioned above, a plugin can have options, which the user can see by doing
``nikola help command`` and can later use, for example:

.. code-block:: console

    $ nikola help serve
    Purpose: start the test webserver
    Usage:   nikola serve [options]

    Options:
    -p ARG, --port=ARG        Port number (default: 8000)
    -a ARG, ----address=ARG   Address to bind (default: 127.0.0.1)

    $ nikola serve -p 9000
    Serving HTTP on 127.0.0.1 port 9000 ...

So, what can you do with commands? Well, anything you want, really. I have implemented
a sort of planet using it. So, be creative, and if you do something interesting,
let me know ;-)

TemplateSystem Plugins
----------------------

Nikola supports Mako and Jinja2. If you prefer some other templating
system, then you will have to write a ``TemplateSystem`` plugin. Here's how they work.
First, you have to create a ``.plugin`` file. Here's the one for the Mako plugin:

.. code-block:: ini

    [Core]
    Name = mako
    Module = mako

    [Documentation]
    Author = Roberto Alsina
    Version = 0.1
    Website = https://getnikola.com
    Description = Support for Mako templates.

.. note:: If you want to publish your plugin on the Plugin Index, `read
          the docs for the Index
          <https://github.com/getnikola/plugins/blob/master/README.md>`__
          (and the .plugin file examples and explanations).

You will have to replace "mako" with your template system's name, and other data
in the obvious ways.

The "Module" option is the name of the module, which has to look something like this,
a stub for a hypothetical system called "Templater":

.. code-block:: python

    from nikola.plugin_categories import TemplateSystem

    # You have to inherit TemplateSystem

    class TemplaterTemplates(TemplateSystem):
        """Wrapper for Templater templates."""

        # name has to match Name in the .plugin file
        name = "templater"

        # A list of directories where the templates will be
        # located. Most template systems have some sort of
        # template loading tool that can use this.
        def set_directories(self, directories, cache_folder):
            """Sets the list of folders where templates are located and cache."""
            pass

        # You *must* implement this, even if to return []
        # It should return a list of all the files that,
        # when changed, may affect the template's output.
        # usually this involves template inheritance and
        # inclusion.
        def template_deps(self, template_name):
            """Returns filenames which are dependencies for a template."""
            return []

        def render_template(self, template_name, output_name, context):
            """Renders template to a file using context.

            This must save the data to output_name *and* return it
            so that the caller may do additional processing.
            """
            pass

        # The method that does the actual rendering.
        # template_name is the name of the template file,
        # context is a dictionary containing the data the template
        # uses for rendering.
        def render_template_to_string(self, template, context):
            """Renders template to a string using context. """
            pass

        def inject_directory(self, directory):
            """Injects the directory with the lowest priority in the
            template search mechanism."""
            pass

You can see a real example in `the Jinja plugin <https://github.com/getnikola/nikola/blob/master/nikola/plugins/template/jinja.py>`__

Task Plugins
------------

If you want to do something that depends on the data in your site, you
probably want to do a ``Task`` plugin, which will make it be part of the
``nikola build`` command. These are the currently available tasks, all
provided by plugins:

.. sidebar:: Other Tasks

    There are also ``LateTask`` plugins, which are executed later,
    and ``TaskMultiplier`` plugins that take a task and create
    more tasks out of it.

.. code-block:: console

    $ nikola list
    Scanning posts....done!
    build_bundles
    build_less
    copy_assets
    copy_files
    post_render
    redirect
    render_archive
    render_galleries
    render_galleries_clean
    render_indexes
    render_listings
    render_pages
    render_posts
    render_rss
    render_site
    render_sources
    render_tags
    sitemap

These have access to the ``site`` object which contains your timeline and
your configuration.

The critical bit of Task plugins is their ``gen_tasks`` method, which ``yields``
`doit tasks <http://pydoit.org/tasks.html>`_.

The details of how to handle dependencies, etc., are a bit too much for this
document, so I'll just leave you with an example, the ``copy_assets`` task.
First the ``task_copy_assets.plugin`` file, which you should copy and edit
in the logical ways:

.. code-block:: ini

    [Core]
    Name = copy_assets
    Module = task_copy_assets

    [Documentation]
    Author = Roberto Alsina
    Version = 0.1
    Website = https://getnikola.com
    Description = Copy theme assets into output.


.. note:: If you want to publish your plugin on the Plugin Index, `read
          the docs for the Index
          <https://github.com/getnikola/plugins/blob/master/README.md>`_
          (and the .plugin file examples and explanations).

And the ``task_copy_assets.py`` file, in its entirety:

.. code-block:: python

    import os

    from nikola.plugin_categories import Task
    from nikola import utils

    # Have to inherit Task to be a task plugin
    class CopyAssets(Task):
        """Copy theme assets into output."""

        name = "copy_assets"

        # This yields the tasks
        def gen_tasks(self):
            """Create tasks to copy the assets of the whole theme chain.

            If a file is present on two themes, use the version
            from the "youngest" theme.
            """

            # I put all the configurations and data the plugin uses
            # in a dictionary because utils.config_changed will
            # make it so that if these change, this task will be
            # marked out of date, and run again.

            kw = {
                "themes": self.site.THEMES,
                "output_folder": self.site.config['OUTPUT_FOLDER'],
                "filters": self.site.config['FILTERS'],
            }

            tasks = {}
            for theme_name in kw['themes']:
                src = os.path.join(utils.get_theme_path(theme_name), 'assets')
                dst = os.path.join(kw['output_folder'], 'assets')
                for task in utils.copy_tree(src, dst):
                    if task['name'] in tasks:
                        continue
                    tasks[task['name']] = task
                    task['uptodate'] = task.get('uptodate', []) + \
                        [utils.config_changed(kw)]
                    task['basename'] = self.name
                    # If your task generates files, please do this.
                    yield utils.apply_filters(task, kw['filters'])

PageCompiler Plugins
--------------------

These plugins implement markup languages, they take sources for posts or pages and
create HTML or other output files. A good example is `the misaka plugin
<https://github.com/getnikola/plugins/tree/master/v7/misaka>`__ or the built-in
compiler plugins.

They must provide:

``compile``
    Function that builds a file.

``create_post``
    Function that creates an empty file with some metadata in it.

If the compiler produces something other than HTML files, it should also implement ``extension`` which
returns the preferred extension for the output file.

These plugins can also be used to extract metadata from a file. To do so, the
plugin must set ``supports_metadata`` to ``True`` and implement ``read_metadata`` that will return a dict containing the
metadata contained in the file. Optionally, it may list ``metadata_conditions`` (see `MetadataExtractor Plugins`_ below)

MetadataExtractor Plugins
-------------------------

Plugins that extract metadata from posts. If they are based on post content,
they must implement ``_extract_metadata_from_text`` (takes source of a post
returns a dict of metadata).  They may also implement
``split_metadata_from_text``, ``extract_text``. If they are based on filenames,
they only need ``extract_filename``. If ``support_write`` is set to True,
``write_metadata`` must be implemented.

Every extractor must be configured properly. The ``name``, ``source`` (from the
``MetaSource`` enum in ``metadata_extractors``) and ``priority``
(``MetaPriority``) fields are mandatory.  There might also be a list of
``conditions`` (tuples of ``MetaCondition, arg``), used to check if an
extractor can provide metadata, a compiled regular expression used to split
metadata (``split_metadata_re``, may be ``None``, used by default
``split_metadata_from_text``), a list of ``requirements`` (3-tuples: import
name, pip name, friendly name), ``map_from`` (name of ``METADATA_MAPPING`` to
use, if any) and ``supports_write`` (whether the extractor supports writing
metadata in the desired format).

For more details, see the definition in  ``plugin_categories.py`` and default extractors in ``metadata_extractors.py``.

RestExtension Plugins
---------------------

Implement directives for reStructuredText, see `media.py <https://github.com/getnikola/nikola/blob/master/nikola/plugins/compile/rest/media.py>`__ for a simple example.

If your output depends on a config value, you need to make your post record a
dependency on a pseudo-path, like this:

.. code-block:: text

    ####MAGIC####CONFIG:OPTIONNAME

Then, whenever the ``OPTIONNAME`` option is changed in conf.py, the file will be rebuilt.

If your directive depends or may depend on the whole timeline (like the
``post-list`` directive, where adding new posts to the site could make it
stale), you should record a dependency on the pseudo-path
``####MAGIC####TIMELINE``.

MarkdownExtension Plugins
-------------------------

Implement Markdown extensions, see `mdx_nikola.py <https://github.com/getnikola/nikola/blob/master/nikola/plugins/compile/markdown/mdx_nikola.py>`__ for a simple example.

Note that Python markdown extensions are often also available as separate
packages. This is only meant to ship extensions along with Nikola.

SignalHandler Plugins
---------------------

These plugins extend the ``SignalHandler`` class and connect to one or more
signals via `blinker <http://pythonhosted.org/blinker/>`_.

The easiest way to do this is to reimplement ``set_site()`` and just connect to
whatever signals you want there.

Currently Nikola emits the following signals:

``sighandlers_loaded``
    Right after SignalHandler plugin activation.
``initialized``
    When all tasks are loaded.
``configured``
    When all the configuration file is processed. Note that plugins are activated before this is emitted.
``scanned``
    After posts are scanned.
``new_post`` / ``new_page``
    When a new post is created, using the ``nikola new_post``/``nikola new_page`` commands.  The signal
    data contains the path of the file, and the metadata file (if there is one).
``existing_post`` / ``existing_page``
    When a new post fails to be created due to a title conflict. Contains the same data as ``new_post``.
``deployed``
    When the ``nikola deploy`` command is run, and there is at least one new
    entry/post since ``last_deploy``.  The signal data is of the form::

        {
         'last_deploy: # datetime object for the last deployed time,
         'new_deploy': # datetime object for the current deployed time,
         'clean': # whether there was a record of a last deployment,
         'deployed': # all files deployed after the last deploy,
         'undeployed': # all files not deployed since they are either future posts/drafts
        }

``compiled``
    When a post/page is compiled from its source to html, before anything else is done with it.  The signal
    data is in the form::

        {
         'source': # the path to the source file
         'dest': # the path to the cache file for the post/page
         'post': # the Post object for the post/page
        }

One example is the `deploy_hooks plugin. <https://github.com/getnikola/plugins/tree/master/v6/deploy_hooks>`__

ConfigPlugin Plugins
--------------------

Does nothing specific, can be used to modify the site object (and thus the config).

Put all the magic you want in ``set_site()``, and don’t forget to run the one
from ``super()``. Example  plugin: `navstories <https://github.com/getnikola/plugins/tree/master/v7/navstories>`__

PostScanner Plugins
-------------------

Get posts and pages from "somewhere" to be added to the timeline.
The only currently existing plugin of this kind reads them from disk.


Plugin Index
============

There is a `plugin index <https://plugins.getnikola.com/>`__, which stores all
of the plugins for Nikola people wanted to share with the world.

You may want to read the `README for the Index
<https://github.com/getnikola/plugins/blob/master/README.md>`_ if you want to
publish your package there.

Path/Link Resolution Mechanism
==============================

Any plugin can register a function using ``Nikola.register_path_handler`` to
allow resolution of paths and links. These are useful for templates, which
can access them via ``_link``.

For example, you can always get a link to the path for the feed of the "foo" tag
by using ``_link('tag_rss', 'foo')`` or the ``link://tag_rss/foo`` URL.

Here's the relevant code from the tag plugin.

.. code-block:: python

    # In set_site
    site.register_path_handler('tag_rss', self.tag_rss_path)

    # And these always take name and lang as arguments and returl a list of
    # path elements.
    def tag_rss_path(self, name, lang):
        return [_f for _f in [self.site.config['TRANSLATIONS'][lang],
                              self.site.config['TAG_PATH'], self.slugify_name(name, lang) + ".xml"] if
                _f]

Template Hooks
==============

Plugins can use a hook system for adding stuff into templates.  In order to use
it, a plugin must register itself.  The following hooks currently exist:

* ``extra_head`` (not equal to the config option!)
* ``body_end`` (not equal to the config option!)
* ``page_header``
* ``menu``
* ``menu_alt`` (right-side menu in bootstrap, after ``menu`` in base)
* ``page_footer``

For example, in order to register a script into ``extra_head``:

.. code-block:: python

    # In set_site
    site.template_hooks['extra_head'].append('<script src="/assets/js/fancyplugin.js">')

There is also another API available.  It allows use of dynamically generated
HTML:

.. code-block:: python

    # In set_site
    def generate_html_bit(name, ftype='js'):
        """Generate HTML for an asset."""
        return '<script src="/assets/{t}/{n}.{t}">'.format(n=name, t=ftype)

    site.template_hooks['extra_head'].append(generate_html_bit, False, 'fancyplugin', ftype='js')


The second argument to ``append()`` is used to determine whether the function
needs access to the current template context and the site.  If it is set to
``True``, the function will also receive ``site`` and ``context`` keyword
arguments.  Example use:

.. code-block:: python

    # In set_site
    def greeting(addr, endswith='', site=None, context=None):
        """Greet someone."""
        if context['lang'] == 'en':
            greet = u'Hello'
        elif context['lang'] == 'es':
            greet = u'¡Hola'

        t = u' BLOG_TITLE = {0}'.format(site.config['BLOG_TITLE'](context['lang']))

        return u'<h3>{greet} {addr}{endswith}</h3>'.format(greet=greet, addr=addr,
        endswith=endswith) + t

    site.template_hooks['page_header'].append(greeting, True, u'Nikola Tesla', endswith=u'!')

Dependencies for template hooks:

* if the input is a string, the string value, alongside arguments to ``append``, is used for calculating dependencies
* if the input is a callable, it attempts ``input.template_registry_identifier``, then ``input.__doc__``, and if neither is available, it uses a static string.

Make sure to provide at least a docstring, or a identifier, to ensure rebuilds work properly.

Shortcodes
==========

Some (hopefully all) markup compilers support shortcodes in these forms::

    {{% raw %}}{{% foo %}}  # No arguments
    {{% foo bar %}}  # One argument, containing "bar"
    {{% foo bar baz=bat %}}  # Two arguments, one containing "bar", one called "baz" containing "bat"

    {{% foo %}}Some text{{% /foo %}}  # one argument called "data" containing "Some text"{{% /raw %}}

So, if you are creating a plugin that generates markup, it may be a good idea
to register it as a shortcode in addition of to restructured text directive or
markdown extension, thus making it available to all markup formats.

To implement your own shortcodes from a plugin, you can create a plugin inheriting ``ShortcodePlugin`` and
from its ``set_site`` method,  call

``Nikola.register_shortcode(name, func)`` with the following arguments:

``name``:
    Name of the shortcode ("foo" in the examples above)
``func``:
    A function that will handle the shortcode

The shortcode handler **must** return a two-element tuple, ``(output, dependencies)``

``output``:
    The text that will replace the shortcode in the document.

``dependencies``:
    A list of all the files on disk which will make the output be considered
    out of date. For example, if the shortcode uses a template, it should be
    the path to the template file.

The shortcode handler **must** accept the following named arguments (or
variable keyword arguments):

``site``:
    An instance of the Nikola class, to access site state

``data``:
    If the shortcut is used as opening/closing tags, it will be the text
    between them, otherwise ``None``.

``lang``:
    The current language.

If the shortcode tag has arguments of the form ``foo=bar`` they will be
passed as named arguments. Everything else will be passed as positional
arguments in the function call.

So, for example::

    {{% raw %}}{{% foo bar baz=bat beep %}}Some text{{% /foo %}}{{% /raw %}}

Assuming you registered ``foo_handler`` as the handler function for the
shortcode named ``foo``, this will result in the following call when the above
shortcode is encountered::

    foo_handler("bar", "beep", baz="bat", data="Some text", site=whatever)

Template-based Shortcodes
-------------------------

Another way to define a new shortcode is to add a template file to the
``shortcodes`` directory of your site. The template file must have the
shortcode name as the basename and the extension ``.tmpl``. For example, if you
want to add a new shortcode named ``foo``, create the template file as
``shortcodes/foo.tmpl``.

When the shortcode is encountered, the matching template will be rendered with
its context provided by the arguments given in the shortcode. Keyword arguments
are passed directly, i.e. the key becomes the variable name in the template
namespace with a matching string value. Non-keyword arguments are passed as
string values in a tuple named ``_args``. As for normal shortcodes with a
handler function, ``site`` and ``data`` will be added to the keyword arguments.

Example:

The following shortcode:

.. code:: text

    {{% raw %}}{{% foo bar="baz" spam %}}{{% /raw %}}

With a template in ``shortcodes/foo.tmpl`` with this content (using Jinja2
syntax in this example)

.. code:: jinja

    <div class="{{ _args[0] if _args else 'ham' }}">{{ bar }}</div>

Will result in this output

.. code:: html

    <div class="spam">baz</div>


State and Cache
===============

Sometimes your plugins will need to cache things to speed up further actions. Here are the conventions for that:

* If it's a file, put it somewhere in ``self.site.config['CACHE_FOLDER']`` (defaults to ``cache/``.
* If it's a value, use ``self.site.cache.set(key, value)`` to set it and ``self.site.cache.get(key)`` to get it.
  The key should be a string, the value should be json-encodable (so, be careful with datetime objects)

The values and files you store there can **and will** be deleted sometimes by the user. They should always be
things you can reconstruct without lossage. They are throwaways.

On the other hand, sometimes you want to save something that is **not** a throwaway. These are things that may
change the output, so the user should not delete them. We call that **state**. To save state:

* If it's a file, put it somewhere in the working directory. Try not to do that please.
* If it's a value, use ``self.site.state.set(key, value)`` to set it and ``self.state.cache.get(key)`` to get it.
  The key should be a string, the value should be json-encodable (so, be careful with datetime objects)

The ``cache`` and ``state`` objects are rather simplistic, and that's intentional. They have no default values: if
the key is not there, you will get ``None`` and like it. They are meant to be both threadsafe, but hey, who can
guarantee that sort of thing?

There are no sections, and no access protection, so let's not use it to store passwords and such. Use responsibly.

