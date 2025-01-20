from typing import Optional

import pytest

from nikola.utils import base_path_from_siteuri


@pytest.mark.parametrize(("uri", "expected_basepath"), [
    ("http://localhost", ""),
    ("http://local.host", ""),
    ("http://localhost/", ""),
    ("http://local.host/", ""),
    ("http://localhost:123/", ""),
    ("http://local.host:456/", ""),
    ("https://localhost", ""),
    ("https://local.host", ""),
    ("https://localhost/", ""),
    ("https://local.host/", ""),
    ("https://localhost:123/", ""),
    ("https://local.host:456/", ""),
    ("http://example.org/blog", "/blog"),
    ("https://lorem.ipsum/dolet/", "/dolet"),
    ("http://example.org:124/blog", "/blog"),
    ("http://example.org:124/Deep/Rab_bit/hol.e/", "/Deep/Rab_bit/hol.e"),
    # Would anybody in a sane mind actually do this?
    ("http://example.org:124/blog?lorem=ipsum&dol=et", "/blog"),
])
def test_basepath(uri: str, expected_basepath: Optional[str]) -> None:
    assert expected_basepath == base_path_from_siteuri(uri)
