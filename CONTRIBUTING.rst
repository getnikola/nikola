Patch submission guidelines [1]_
--------------------------------

Here are some guidelines about how you can contribute to Nikola:

* Please make sure the bug you’re fixing or the feature you’re contributing has
  a GitHub issue. If there is no issue for the bug/feature, please create it
  first. The issue description should be precise. We need information about
  what the bug/feature is. For features, we need to have information that can
  help us understand the request, the benefits and drawbacks of adding this
  feature to Nikola.

* If your contribution is a new feature, it should be discussed first, under
  the GitHub issue for the feature request. You can also discuss it on the
  `GitHub Discussions tab <https://github.com/getnikola/nikola/discussions>`_.

* Using LLMs ("AI") for issue reports is not allowed.
  Issues clearly written by LLMs will be closed without response.
  LLM-assisted "security" reports which do not describe a real vulnerability will be closed,
  and the GitHub account which posted it blocked from the project.

* If you use LLMs ("AI") for your code contributions, please indicate so in the pull request.
  We allow LLM-assisted contributions, but we will reject LLM-written pull requests
  without comment if they introduce large, significant, previously undiscussed changes.

* **Create a new Git branch specific to your change(s).** For example, if
  you’re adding a new feature to foo the bars, do something like the
  following::

    $ git checkout master
    $ git pull
    $ git checkout -b foo-the-bars
    <hack hack hack>
    $ git push origin HEAD
    <submit pull request based on your new 'foo-the-bars' branch>

  This makes life much easier for maintainers if you have (or ever plan to
  have) additional changes in your own ``master`` branch.

  Also, if you have commit rights to the main Nikola repository, we suggest
  having your branch there, instead of a personal fork.

.. admonition:: A corollary:

      Please **don’t put multiple fixes/features in the same
      branch/pull request**! In other words, if you’re hacking on new feature X
      and find a bugfix that doesn’t *require* new feature X, **make a new
      distinct branch and PR** for the bugfix.

* You may want to use the `Tim Pope’s Git commit messages standard
  <http://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html>`_.
  It’s not necessary, but if you are doing something big, we recommend
  describing it in the commit message.
* Your Pull Request should have an informative title and description.
* While working, rebase instead of merging (if possible). You can use rebase
  instead of merge by default with ``git config pull.rebase true``. If rebases
  fail, you can just use ``git pull --no-rebase``.
* We will squash your commits when merging the pull request. This means
  you don’t need to do this yourself (and it’s easier for us to review pull requests
  which don’t squash things on their own).
* **Make sure documentation is updated** — at the very least, keep docstrings
  current, and if necessary, update the reStructuredText documentation in ``docs/``.
* **Add a CHANGELOG entry** at the *top* of ``CHANGES.txt`` mentioning the
  issue number in parentheses and in the correct Features/Bugfixes section. Put
  it under *New in master*.  Create that section if it does not exist yet. Do
  not add an entry if the change is trivial (documentation, typo fixes) or if
  the change is internal (not noticeable to end users in any way).
* Add your name to ``AUTHORS.txt`` if the change is non-trivial.
* If you are fixing an issue, **include the issue number in commit** and/or pull
  request text (eg. ``fix #1234``) so the issue `is automatically closed
  <https://help.github.com/articles/closing-issues-via-commit-messages/>`_.
* Run ``flake8 nikola tests`` and ``pydocstyle --count --match-dir='(?!^\\.)(?!data).*' nikola/``
  for **style consistency**.
* Ensure your Git name and e-mail are set correctly (they will be public)
  and `added to GitHub <https://github.com/settings/emails>`_
* **Try writing some tests** if possible — again, following existing tests is
  often easiest, and a good way to tell whether the feature you are modifying is
  easily testable.
* **Test your code.** If you can, run the test suite with ``pytest tests/``
  (you can install all the dependencies via ``pip install '.[extras,tests]'``). Alternatively,
  you can push, make a PR and wait for our CI to pick up and test your changes
  (but note that workflows for new  contributors require maintainer approval for
  security reasons). Test results will appear at the bottom of the PR page, and
  you can get `notifications <https://github.com/settings/notifications>`_ about
  failed runs if you configure them on GitHub.

  If running tests is not feasible before you push, please at least confirm that:

  * the demo site (created with ``nikola init -qd demosite``) builds without errors
  * the bugs you were trying to fix do not occur anymore (if applicable)
  * the features you added work properly (if applicable)

* There are some quirks to how Nikola’s codebase is structured, and to how
  some things need to be done [2]_ but don’t worry, we’ll guide you!

.. [1] Very inspired by `fabric’s <https://github.com/fabric/fabric/blob/master/CONTRIBUTING.rst>`_ — thanks!

.. [2] For example, logging, or always making sure directories are created using ``utils.makedirs()``.

Previewing documentation changes
--------------------------------

The user documentation in ``docs/`` is published on `getnikola.com
<https://getnikola.com/documentation.html>`_ using the separate
`nikola-site repository <https://github.com/getnikola/nikola-site>`_.
To preview it with the website's templates, use sibling checkouts of both
repositories. For example, in a POSIX shell::

    git clone https://github.com/getnikola/nikola.git
    git clone https://github.com/getnikola/nikola-site.git
    python3 -m venv .venv
    . .venv/bin/activate
    python -m pip install -e './nikola[extras]'
    cd nikola-site
    cp ../nikola/docs/*.rst ../nikola/AUTHORS.txt ../nikola/CHANGES.txt stories/
    nikola build
    nikola serve --address 127.0.0.1 --browser

If you already have a Nikola checkout, use that checkout instead of cloning
it again. Visit http://127.0.0.1:8000/documentation.html to find the documentation,
or http://127.0.0.1:8000/handbook.html for ``docs/manual.rst``.
Stop the preview server with Ctrl-C.

Make your edits in the **Nikola repository's** ``docs/`` directory, then repeat
the copy and ``nikola build`` commands from ``nikola-site`` and refresh the
browser. The files in ``nikola-site/stories/`` are copies; editing them does not
update the sources for your pull request. Submit documentation changes to the
Nikola repository. The website's release-update steps are not needed for this
preview, and its bundled configuration listing may describe a released version.

This previews the user documentation, not the Sphinx API reference under
``docs/sphinx/``.
