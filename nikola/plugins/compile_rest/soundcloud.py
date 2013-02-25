from docutils import nodes
from docutils.parsers.rst import directives

CODE = ("""<iframe width="{width}" height="{height}"
scrolling="no" frameborder="no"
src="https://w.soundcloud.com/player/?url=http://api.soundcloud.com/tracks/"""
        """{sid}">
</iframe>""")


def soundcloud(name, args, options, content, lineno,
               contentOffset, blockText, state, stateMachine):
    """ Restructured text extension for inserting SoundCloud embedded music """
    string_vars = {
        'sid': content[0],
        'width': 600,
        'height': 160,
        'extra': ''
    }
    extra_args = content[1:]  # Because content[0] is ID
    extra_args = [ea.strip().split("=") for ea in extra_args]  # key=value
    extra_args = [ea for ea in extra_args if len(ea) == 2]  # drop bad lines
    extra_args = dict(extra_args)
    if 'width' in extra_args:
        string_vars['width'] = extra_args.pop('width')
    if 'height' in extra_args:
        string_vars['height'] = extra_args.pop('height')

    return [nodes.raw('', CODE.format(**string_vars), format='html')]

soundcloud.content = True
directives.register_directive('soundcloud', soundcloud)
