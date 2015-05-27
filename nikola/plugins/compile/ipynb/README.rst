1. You should install the ``ipython`` theme using this command


    .. code-block:: console

        $ nikola install_theme ipython

    (or ``ipython-xkcd``, if you want xkcd styling)

    More info here about themes:
    https://getnikola.com/handbook.html#getting-more-themes

    If you want to use your own theme, copy the ``ipython.min.css`` and
    ``nikola_ipython.css`` files from ``ipython`` to your theme (and include them
    in ``bundles`` if necessary)

2. Then, just add to ``conf.py``:


    .. code-block:: python

        POSTS = (
            ("posts/*.ipynb", "posts", "post.tmpl", True),
        )
        PAGES = (
            ("stories/*.ipynb", "stories", "story.tmpl", False),
        )

    and set ``THEME`` to ``'ipython'`` or ``'ipython-xkcd'``, depending on your
    choice.

To create a new post or page, use:

.. code-block:: console

    $ nikola new_post -f ipynb
    $ nikola new_page -f ipynb

**NOTE**: the ``-1`` and ``-2`` options are ignored; two-file posts are always
created for ipynb posts.
