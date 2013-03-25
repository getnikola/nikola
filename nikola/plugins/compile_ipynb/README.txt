To make this work...

1- First, you have to put this plugin in your_site/plugins/ folder.

2- Then, you have to download the custom nbconvert from here: https://github.com/damianavila/compile_ipynb-for-Nikola.git
and put it inside your_site/plugins/compile_ipynb/ folder

3- Also, you have to use the site-ipython theme (or make a new one containing the ipython css, mathjax.js and the proper template).
You can get it here: https://github.com/damianavila/site-ipython-theme-for-Nikola

4- Finally, you have to put: 

post_pages = (
    ("posts/*.ipynb", "posts", "post.tmpl", True),
    ("stories/*.ipynb", "stories", "story.tmpl", False),
)

in your conf.py

Then... to use it:

$nikola new_page -f ipynb

**NOTE**: Just IGNORE the "-1" and "-2" options in nikola new_page command, by default this compiler 
create one metadata file and the corresponding naive IPython notebook.

$nikola build

And deploy the output folder... to see it locally: $nikola serve

If you have any doubts, just ask: @damianavila

Cheers.

Damián
