=====================
The Nikola Test Suite
=====================

Nikola, like many software projects, has a test suite.  There are over 100
tests.

Tests (in alphabetical order)
=============================

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
=============================

You need:

* ``pip -r requirements-tests.txt``
* a few minutes’ time
* appropriate locale settings

How to set the locale for Nikola tests?
---------------------------------------

You need at least two locales.  By default, the test suite uses ``en`` and
``es``.  You can set the locales you want by exporting two shell variables.
They are::

    export NIKOLA_LOCALE_DEFAULT=en,en_US.utf8
    export NIKOLA_LOCALE_OTHER=es,es_ES.utf8

Replace the part before the comma with a Nikola locale (see ``nikola/conf.py.in`` for details), and the part after the comma with an *installed* glibc locale.

How to execute the tests
========================

The command to execute tests is::

    nosetests --with-coverage --cover-package=nikola --with-doctest --doctest-options=+NORMALIZE_WHITESPACE --logging-filter=-yapsy

However, this command may change at any given moment.  Check the
``/.travis.yml`` file to get the current command.

It is also recommended to run ``nikola help`` to see if Nikola actually
works.  If you are committing code, make sure to run ``flake8 --ignore=E501 .`` to see if you comply with the PEP 8 style guide and do not have basic code mistakes (we ignore the 79-characters-per-line rule)

Travis CI
=========

We also run our tests on `Travis CI <https://travis-ci.org/>`_.
You can check the `current build status <https://travis-ci.org/getnikola/nikola>`_ there.
