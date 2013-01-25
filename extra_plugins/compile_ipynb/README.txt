To make this work...

1- You have to put this plugin in the installed nikola/plugins/ folder.
2- You have to use the site-ipython theme (or make a new one containing the ipython css, mathjax.js and the proper template).
You can get it here: https://github.com/damianavila/site-ipython-theme-for-Nikola
3- Also, you have to put: 

post_pages = (
    ("posts/*.ipynb", "posts", "post.tmpl", True),
    ("stories/*.ipynb", "stories", "story.tmpl", False),
)

in your conf.py

If you have any doubts, just ask: @damianavila

Cheers.

Damián