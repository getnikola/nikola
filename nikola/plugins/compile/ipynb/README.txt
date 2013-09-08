To make this work...

1- You can install the "jinja-site-ipython" theme using this command:

$ nikola install_theme -n jinja-site-ipython

(or xkcd-site-ipython, if you want xkcd styling)

More info here about themes:
http://getnikola.com/handbook.html#getting-more-themes

OR

You can to download the "jinja-site-ipython" theme from here: 
https://github.com/damianavila/jinja-site-ipython-theme-for-Nikola
and copy the "site-ipython" folder inside the "themes" folder of your site.


2- Then, just add:

post_pages = (
    ("posts/*.ipynb", "posts", "post.tmpl", True),
    ("stories/*.ipynb", "stories", "story.tmpl", False),
)

and 

THEME = 'jinja-site-ipython' (or 'xkcd-site-ipython', if you want xkcd styling)

to your conf.py.
Finally... to use it:

$nikola new_page -f ipynb

**NOTE**: Just IGNORE the "-1" and "-2" options in nikola new_page command, by default this compiler 
create one metadata file and the corresponding naive IPython notebook.

$nikola build

And deploy the output folder... to see it locally: $nikola serve
If you have any doubts, just ask: @damianavila

Cheers.
Damián
