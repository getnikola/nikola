======
Nikola
======

--------------------------------
A Static Site and Blog Generator
--------------------------------

:Version: Nikola 7.8.9
:Manual section: 1
:Manual group: User Commands

SYNOPSIS
========

Create an empty site (with a setup wizard):

    ``nikola init mysite``

(You can create a site with demo files in it with ``nikola init --demo mysite``)

Create a post (inside the ``mysite`` directory):

    ``nikola new_post``

Build the site:

    ``nikola build``

Start the test server and open a browser:

    ``nikola serve -b``


DESCRIPTION
===========

Nikola is a static website and blog generator. The very short
explanation is that it takes some texts you wrote, and uses them to
create a folder full of HTML files. If you upload that folder to a
server, you will have a rather full-featured website, done with little
effort.

Its original goal is to create blogs, but it supports most kind of
sites, and can be used as a CMS, as long as what you present to the
user is your own content instead of something the user generates.

Nikola can do:

* A blog
* Your company's site
* Your personal site
* A software project's site
* A book's site

Since Nikola-based sites don't run any code on the server, there is no
way to process user input in forms.

Nikola can't do:

* Twitter
* Facebook
* An Issue tracker
* Anything with forms, really (except for comments!)

Keep in mind that "static" doesn't mean **boring**. You can have
animations, slides or whatever fancy CSS/HTML5 thingie you like. It
only means all that HTML is generated already before being uploaded.
On the other hand, Nikola sites will tend to be content-heavy. What
Nikola is good at is at putting what you write out there.

COMMANDS
========

The most basic commands needed to get by are:

``nikola help``
    get a list of commands, or help for a command
``nikola version [--check]``
    print version number
``nikola init [-d|--demo] [-q|--quiet] folder``
    initialize new site
``nikola build``
    build a site
``nikola new_post``
    create a new post
``nikola new_page``
    create a new page
``nikola status [--list-drafts] [--list-modified] [--list-scheduled]``
    show site and deployment status
``nikola check [-v] (-l [--find-sources] [-r] | -f [--clean-files])``
    check for dangling links or unknown files
``nikola deploy [[preset [preset...]]``
    deploy the site using the ``DEPLOY_COMMANDS`` setting
``nikola github_deploy [-m COMMIT_MESSAGE]```
    deploy the site to GitHub Pages
``nikola serve [-p PORT] [-a ADDRESS] [-d|--detach] [-b|--browser] [-6|--ipv6]``
    start development web server
``nikola auto [-p PORT] [-a ADDRESS] [-b|--browser] [-6|--ipv6]``
    start development web server with automated rebuilds and reloads
``nikola plugin [options]``
    manage plugins from the Plugins Index (https://plugins.getnikola.com/)
``nikola theme [options]``
    manage themes from the Themes Index (https://themes.getnikola.com/)

Use ``nikola help`` to get a list of all commands.

BUGS
====

Issue Tracker: https://github.com/getnikola/nikola/issues

SEE ALSO
========

* The Nikola Website: https://getnikola.com/
* Handbook: https://getnikola.com/handbook.html
* Support: https://getnikola.com/contact.html
