# -*- coding: utf-8 -*-
import nikola.utils

def test_ascii():
    o = nikola.utils.slugify(u'abcdef')
    assert o == u'abcdef'
    assert isinstance(o, nikola.utils.unicode_str)

def test_ascii_dash():
    o = nikola.utils.slugify(u'abc-def')
    assert o == u'abc-def'
    assert isinstance(o, nikola.utils.unicode_str)

def test_pl():
    o = nikola.utils.slugify(u'ąbćdef')
    assert o == u'abcdef'
    assert isinstance(o, nikola.utils.unicode_str)

def test_pl_dash():
    o = nikola.utils.slugify(u'ąbć-def')
    assert o == u'abc-def'
    assert isinstance(o, nikola.utils.unicode_str)

def test_disarmed():
    nikola.utils.USE_SLUGIFY = False
    o = nikola.utils.slugify(u'ąbć-def')
    assert o == u'ąbć-def'
    assert isinstance(o, nikola.utils.unicode_str)
    nikola.utils.USE_SLUGIFY = True

def test_disarmed_weird():
    nikola.utils.USE_SLUGIFY = False
    o = nikola.utils.slugify(u'ąbć-def "Hello World"?#H<e>l/l\\o:W\'o\rr*l\td|!\n')
    assert o == u'ąbć-def -Hello World---H-e-l-l-o-W-o-r-l-d-!-'
    assert isinstance(o, nikola.utils.unicode_str)
    nikola.utils.USE_SLUGIFY = True
