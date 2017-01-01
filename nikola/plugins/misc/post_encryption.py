# -*- coding: utf-8 -*-

# Copyright © 2012-2017 Roberto Alsina and others.

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

"""Render the taxonomy overviews, classification pages and feeds."""

from __future__ import unicode_literals
import blinker
import io
import string

from nikola.plugin_categories import SignalHandler
from nikola import utils
from nikola.rc4 import rc4


class PostEncryption(SignalHandler):
    """Encrypt posts with passwords."""

    name = "post_encryption"

    @staticmethod
    def wrap_encrypt(path, password):
        """Wrap a post with encryption."""
        with io.open(path, 'r+', encoding='utf8') as inf:
            data = inf.read() + "<!--tail-->"
        data = CRYPT.substitute(data=rc4(password, data))
        with io.open(path, 'w+', encoding='utf8') as outf:
            outf.write(data)

    def _handle_post_compiled(self, data):
        """Encrypt post if password is set."""
        dest = data['dest']
        post = data['post']
        if post.meta('password'):
            # TODO: get rid of this feature one day (v8?; warning added in v7.3.0.)
            utils.LOGGER.warn("The post {0} is using the `password` attribute, which may stop working in the future.")
            utils.LOGGER.warn("Please consider switching to a more secure method of encryption.")
            utils.LOGGER.warn("More details: https://github.com/getnikola/nikola/issues/1547")
            self.wrap_encrypt(dest, post.meta('password'))

    def set_site(self, site):
        """Set site, which is a Nikola instance."""
        super(PostEncryption, self).set_site(site)
        # Add hook for after post compilation
        blinker.signal("compiled").connect(self._handle_post_compiled)


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
