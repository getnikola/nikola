.. title: The Nikola Test Suite
.. slug: tests
.. date: 2012/03/30 23:00

The Nikola Test Suite
=====================

Nikola, like many software projects, has a test suite.  There are over 100
tests.

Tests (in alphabetical order)
-----------------------------

* ``test_command_import_wordpress`` tests the WordPress importer for
  Nikola.
* ``test_command_init`` checks whether new sites are created properly via the
  ``init`` command.
* ``test_compile_markdown`` exercises the Markdown compiler plugin of Nikola.
* ``test_integration`` are used to validate that sites actually build.
* ``test_locale`` tests the locale support of Nikola.
* ``test_plugin_importing`` checks three basic plugins to know whether they
  get imported properly.
* ``test_rss_feeds`` asserts that RSS created by Nikola is sane.
* ``test_rst_compiler`` exercises the reStructuredText compiler plugin of
  Nikola.
* ``test_scheduling`` performs tests on post scheduling rules.
* ``test_utils`` test various Nikola utilities.

Requirements to run the tests
-----------------------------

You need:

* ``pip install -r requirements-tests.txt``
* a few minutes’ time
* appropriate locale settings

How to set the locale for Nikola tests?
---------------------------------------

For testing nikola needs to specify two languages, each one with a supported locale. By default, the test suite uses ``en`` and ``pl`` as languages, and their respective default locale for them.

The choice of Polish is due to having one locale to generate instead of 20 (Spanish) and you can happily ignore it — just set the language–locale pairs by exporting two shell variables, for example::

    export NIKOLA_LOCALE_DEFAULT=en,en_US.utf8
    export NIKOLA_LOCALE_OTHER=pl,pl_PL.utf8

In Windows that would be::

    set NIKOLA_LOCALE_DEFAULT=en,English
    set NIKOLA_LOCALE_OTHER=pl,Polish

Replace the part before the comma with a Nikola translation selector (see ``nikola/conf.py.in`` for details), and the part after the comma with an *installed* glibc locale.

To check if the desired locale is supported in your host you can, in a python console::

    import locale
    locale.setlocale(locale.LC_ALL, 'locale_name')
    # for example, 'en_US.utf8' (posix) 'English' (windows)
    # if it does not traceback, then python can use that locale

Alternatively, if you have some disk space to spare, you can install
the two default locales. Here is how to do that in Ubuntu::

    sudo apt-get install language-pack-en language-pack-pl


How to execute the tests
------------------------

The command to execute tests is::

    doit coverage

Note that Travis does not use this command — and as such, differences between the two may appear.

In Windows you want to drop the doctests parts, they fail over trivial differences in OS details.

It is also recommended to run ``nikola help`` to see if Nikola actually
works.

If you are committing code, make sure to run ``flake8 --ignore=E501 .`` to see if you comply with the PEP 8 style guide and do not have basic code mistakes (we ignore the 79-characters-per-line rule).

In windows ignore the two flake8 diagnostics about messages_sl_si.py , they are artifacts of (symlinks + git + windows).


Travis CI
---------

We also run our tests on `Travis CI <https://travis-ci.org/>`_.
You can check the `current build status <https://travis-ci.org/getnikola/nikola>`_ there.


Writing tests
-------------

* When adding new *.py files under tests/ , remember to include at the begining the lines::

	# This code is so you can run the samples without installing the package,
	# and should be before any import touching nikola, in any file under tests/
	import os
	import sys
	sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

  Those lines allow to run the tests without installing nikola.
