# Copyright (c) 2012 Roberto Alsina y otros.

# Permission is hereby granted, free of charge, to any
# person obtaining a copy of this software and associated
# documentation files (the "Software"), to deal in the
# Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the
# Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice
# shall be included in all copies or substantial portions of
# the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY
# KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
# PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS
# OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

from copy import copy
import codecs
import string

from nikola.plugin_categories import Task
from nikola import utils, rc4


def wrap_encrypt(path, password):
    """Wrap a post with encryption."""
    with codecs.open(path, 'rb+', 'utf8') as inf:
        data = inf.read() + "<!--tail-->"
    data = CRYPT.substitute(data=rc4.rc4(password, data))
    with codecs.open(path, 'wb+', 'utf8') as outf:
        outf.write(data)


class RenderPosts(Task):
    """Build HTML fragments from metadata and text."""

    name = "render_posts"

    def gen_tasks(self):
        """Build HTML fragments from metadata and text."""
        self.site.scan_posts()
        kw = {
            "translations": self.site.config["TRANSLATIONS"],
            "timeline": self.site.timeline,
            "default_lang": self.site.config["DEFAULT_LANG"],
            "hide_untranslated_posts": self.site.config['HIDE_UNTRANSLATED_POSTS'],
        }

        flag = False
        for lang in kw["translations"]:
            deps_dict = copy(kw)
            deps_dict.pop('timeline')
            for post in kw['timeline']:
                source = post.source_path
                dest = post.base_path
                if not post.is_translation_available(lang) and kw["hide_untranslated_posts"]:
                    continue
                else:
                    source = post.translated_source_path(lang)
                    if lang != post.default_lang:
                        dest = dest + '.' + lang
                flag = True
                task = {
                    'basename': self.name,
                    'name': dest,
                    'file_dep': post.fragment_deps(lang),
                    'targets': [dest],
                    'actions': [(self.site.get_compiler(post.source_path).compile_html,
                                 [source, dest, post.is_two_file])],
                    'clean': True,
                    'uptodate': [utils.config_changed(deps_dict)],
                }
                if post.meta('password'):
                    task['actions'].append((wrap_encrypt, (dest, post.meta('password'))))
                yield task
        if flag is False:  # Return a dummy task
            yield {
                'basename': self.name,
                'name': 'None',
                'uptodate': [True],
                'actions': [],
            }


CRYPT = string.Template("""\
<script>
function rc4(key, str) {
    var s = [], j = 0, x, res = '';
    for (var i = 0; i < 256; i++) {
        s[i] = i;
    }
    for (i = 0; i < 256; i++) {
        j = (j + s[i] + key.charCodeAt(i % key.length)) % 256;
        x = s[i];
        s[i] = s[j];
        s[j] = x;
    }
    i = 0;
    j = 0;
    for (var y = 0; y < str.length; y++) {
        i = (i + 1) % 256;
        j = (j + s[i]) % 256;
        x = s[i];
        s[i] = s[j];
        s[j] = x;
        res += String.fromCharCode(str.charCodeAt(y) ^ s[(s[i] + s[j]) % 256]);
    }
    return res;
}
function decrypt() {
    key = $$("#key").val();
    crypt_div = $$("#encr")
    crypted = crypt_div.html();
    decrypted = rc4(key, window.atob(crypted));
    if (decrypted.substr(decrypted.length - 11) == "<!--tail-->"){
        crypt_div.html(decrypted);
        $$("#pwform").hide();
        crypt_div.show();
    } else { alert("Wrong password"); };
}
</script>

<div id="encr" style="display: none;">${data}</div>
<div id="pwform">
<form onsubmit="javascript:decrypt(); return false;" class="form-inline">
<fieldset>
<legend>This post is password-protected.</legend>
<input type="password" id="key" placeholder="Type password here">
<button type="submit" class="btn">Show Content</button>
</fieldset>
</form>
</div>""")
