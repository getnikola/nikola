# -*- coding: utf-8 -*-
"""
A RC4 encryption library (used for password-protected posts).

Original RC4 code license:

    Copyright (C) 2012 Bo Zhu http://about.bozhu.me

    Permission is hereby granted, free of charge, to any person obtaining a
    copy of this software and associated documentation files (the "Software"),
    to deal in the Software without restriction, including without limitation
    the rights to use, copy, modify, merge, publish, distribute, sublicense,
    and/or sell copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in
    all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
    DEALINGS IN THE SOFTWARE.
"""

import base64
import sys


def KSA(key):
    """Run Key Scheduling Algorithm."""
    keylength = len(key)

    S = list(range(256))

    j = 0
    for i in range(256):
        j = (j + S[i] + key[i % keylength]) % 256
        S[i], S[j] = S[j], S[i]  # swap

    return S


def PRGA(S):
    """Run Pseudo-Random Generation Algorithm."""
    i = 0
    j = 0
    while True:
        i = (i + 1) % 256
        j = (j + S[i]) % 256
        S[i], S[j] = S[j], S[i]  # swap

        K = S[(S[i] + S[j]) % 256]
        yield K


def RC4(key):
    """Generate RC4 keystream."""
    S = KSA(key)
    return PRGA(S)


def rc4(key, string):
    """Encrypt things.

    >>> print(rc4("Key", "Plaintext"))
    u/MW6NlArwrT
    """
    string.encode('utf8')
    key.encode('utf8')

    def convert_key(s):
        return [ord(c) for c in s]
    key = convert_key(key)
    keystream = RC4(key)
    r = b''
    for c in string:
        if sys.version_info[0] == 3:
            r += bytes([ord(c) ^ next(keystream)])
        else:
            r += chr(ord(c) ^ next(keystream))
    return base64.b64encode(r).replace(b'\n', b'').decode('ascii')
