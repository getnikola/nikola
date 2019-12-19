import os
from unittest import mock

import pytest

import nikola.plugins.command.import_wordpress


def test_create_import_work_without_argument(import_command):
    """
    Running import command without an argument must not fail.
    It should show the proper usage of the command.
    """
    import_command.execute()


@pytest.mark.parametrize(
    "key, expected_value",
    [
        ("DEFAULT_LANG", "de"),
        ("BLOG_TITLE", "Wordpress blog title"),
        ("BLOG_DESCRIPTION", "Nikola test blog ;) - with moré Ümläüts"),
        ("SITE_URL", "http://some.blog/"),
        ("BLOG_EMAIL", "mail@some.blog"),
        ("BLOG_AUTHOR", "Niko"),
    ],
)
def test_populate_context(import_command, import_filename, key, expected_value):
    channel = import_command.get_channel_from_file(import_filename)
    import_command.html2text = False
    import_command.transform_to_markdown = False
    import_command.transform_to_html = False
    import_command.use_wordpress_compiler = False
    import_command.translations_pattern = "{path}.{lang}.{ext}"
    context = import_command.populate_context(channel)

    for required_key in ("POSTS", "PAGES", "COMPILERS"):
        assert required_key in context

    assert expected_value == context[key]


def test_importing_posts_and_attachments(module, import_command, import_filename):
    channel = import_command.get_channel_from_file(import_filename)
    import_command.base_dir = ""
    import_command.output_folder = "new_site"
    import_command.squash_newlines = True
    import_command.no_downloads = False
    import_command.export_categories_as_categories = False
    import_command.export_comments = False
    import_command.html2text = False
    import_command.transform_to_markdown = False
    import_command.transform_to_html = False
    import_command.use_wordpress_compiler = False
    import_command.tag_saniziting_strategy = "first"
    import_command.separate_qtranslate_content = False
    import_command.translations_pattern = "{path}.{lang}.{ext}"

    import_command.context = import_command.populate_context(channel)

    # Ensuring clean results
    # assert not import_command.url_map
    assert not module.links
    import_command.url_map = {}

    write_metadata = mock.MagicMock()
    write_content = mock.MagicMock()
    write_attachments_info = mock.MagicMock()
    download_mock = mock.MagicMock()

    with mock.patch(
        "nikola.plugins.command.import_wordpress.CommandImportWordpress.write_content",
        write_content,
    ), mock.patch(
        "nikola.plugins.command.import_wordpress.CommandImportWordpress.write_metadata",
        write_metadata,
    ), mock.patch(
        "nikola.plugins.command.import_wordpress.CommandImportWordpress.download_url_content_to_file",
        download_mock,
    ), mock.patch(
        "nikola.plugins.command.import_wordpress.CommandImportWordpress.write_attachments_info",
        write_attachments_info,
    ), mock.patch(
        "nikola.plugins.command.import_wordpress.os.makedirs"
    ):
        import_command.import_posts(channel)

    assert download_mock.called
    qpath = "new_site/files/wp-content/uploads/2008/07/arzt_und_pfusch-sick-cover.png"
    download_mock.assert_any_call(
        "http://some.blog/wp-content/uploads/2008/07/arzt_und_pfusch-sick-cover.png",
        qpath.replace("/", os.sep),
    )

    assert write_metadata.called
    write_metadata.assert_any_call(
        "new_site/pages/kontakt.meta".replace("/", os.sep),
        "Kontakt",
        "kontakt",
        "2009-07-16 20:20:32",
        "",
        [],
        **{"wp-status": "publish"}
    )

    assert write_content.called
    write_content.assert_any_call(
        "new_site/posts/2007/04/hoert.md".replace("/", os.sep),
        """An image.

<img class="size-full wp-image-16" title="caption test" src="http://some.blog/wp-content/uploads/2009/07/caption_test.jpg" alt="caption test" width="739" height="517" />

Some source code.

```Python

import sys
print sys.version

```

The end.
""",
        True,
    )

    assert write_attachments_info.called
    write_attachments_info.assert_any_call(
        "new_site/posts/2008/07/arzt-und-pfusch-s-i-c-k.attachments.json".replace(
            "/", os.sep
        ),
        {
            10: {
                "wordpress_user_name": "Niko",
                "files_meta": [
                    {"width": 300, "height": 299},
                    {"width": 150, "size": "thumbnail", "height": 150},
                ],
                "excerpt": "Arzt+Pfusch - S.I.C.K.",
                "date_utc": "2009-07-16 19:40:37",
                "content": "Das Cover von Arzt+Pfusch - S.I.C.K.",
                "files": [
                    "/wp-content/uploads/2008/07/arzt_und_pfusch-sick-cover.png",
                    "/wp-content/uploads/2008/07/arzt_und_pfusch-sick-cover-150x150.png",
                ],
                "title": "Arzt+Pfusch - S.I.C.K.",
            }
        },
    )

    write_content.assert_any_call(
        "new_site/posts/2008/07/arzt-und-pfusch-s-i-c-k.md".replace("/", os.sep),
        """<img class="size-full wp-image-10 alignright" title="Arzt+Pfusch - S.I.C.K." src="http://some.blog/wp-content/uploads/2008/07/arzt_und_pfusch-sick-cover.png" alt="Arzt+Pfusch - S.I.C.K." width="210" height="209" />Arzt+Pfusch - S.I.C.K.Gerade bin ich \xfcber das Album <em>S.I.C.K</em> von <a title="Arzt+Pfusch" href="http://www.arztpfusch.com/" target="_blank">Arzt+Pfusch</a> gestolpert, welches Arzt+Pfusch zum Download f\xfcr lau anbieten. Das Album steht unter einer Creative Commons <a href="http://creativecommons.org/licenses/by-nc-nd/3.0/de/">BY-NC-ND</a>-Lizenz.
Die Ladung <em>noisebmstupidevildustrial</em> gibts als MP3s mit <a href="http://www.archive.org/download/dmp005/dmp005_64kb_mp3.zip">64kbps</a> und <a href="http://www.archive.org/download/dmp005/dmp005_vbr_mp3.zip">VBR</a>, als Ogg Vorbis und als FLAC (letztere <a href="http://www.archive.org/details/dmp005">hier</a>). <a href="http://www.archive.org/download/dmp005/dmp005-artwork.zip">Artwork</a> und <a href="http://www.archive.org/download/dmp005/dmp005-lyrics.txt">Lyrics</a> gibts nochmal einzeln zum Download.""",
        True,
    )
    write_content.assert_any_call(
        "new_site/pages/kontakt.md".replace("/", os.sep),
        """<h1>Datenschutz</h1>
Ich erhebe und speichere automatisch in meine Server Log Files Informationen, die dein Browser an mich \xfcbermittelt. Dies sind:
<ul>
    <li>Browsertyp und -version</li>
    <li>verwendetes Betriebssystem</li>
    <li>Referrer URL (die zuvor besuchte Seite)</li>
    <li>IP Adresse des zugreifenden Rechners</li>
    <li>Uhrzeit der Serveranfrage.</li>
</ul>
Diese Daten sind f\xfcr mich nicht bestimmten Personen zuordenbar. Eine Zusammenf\xfchrung dieser Daten mit anderen Datenquellen wird nicht vorgenommen, die Daten werden einzig zu statistischen Zwecken erhoben.""",
        True,
    )

    assert len(import_command.url_map) > 0

    assert (
        "http://some.blog/posts/2007/04/hoert.html" ==
        import_command.url_map["http://some.blog/2007/04/hoert/"]
    )
    assert (
        "http://some.blog/posts/2008/07/arzt-und-pfusch-s-i-c-k.html" ==
        import_command.url_map["http://some.blog/2008/07/arzt-und-pfusch-s-i-c-k/"]
    )
    assert (
        "http://some.blog/pages/kontakt.html" ==
        import_command.url_map["http://some.blog/kontakt/"]
    )

    image_thumbnails = [
        "http://some.blog/wp-content/uploads/2012/12/2012-12-19-1355925145_1024x600_scrot-64x64.png",
        "http://some.blog/wp-content/uploads/2012/12/2012-12-19-1355925145_1024x600_scrot-300x175.png",
        "http://some.blog/wp-content/uploads/2012/12/2012-12-19-1355925145_1024x600_scrot-36x36.png",
        "http://some.blog/wp-content/uploads/2012/12/2012-12-19-1355925145_1024x600_scrot-24x24.png",
        "http://some.blog/wp-content/uploads/2012/12/2012-12-19-1355925145_1024x600_scrot-96x96.png",
        "http://some.blog/wp-content/uploads/2012/12/2012-12-19-1355925145_1024x600_scrot-96x96.png",
        "http://some.blog/wp-content/uploads/2012/12/2012-12-19-1355925145_1024x600_scrot-48x48.png",
        "http://some.blog/wp-content/uploads/2012/12/2012-12-19-1355925145_1024x600_scrot-96x96.png",
        "http://some.blog/wp-content/uploads/2012/12/2012-12-19-1355925145_1024x600_scrot-150x150.png",
    ]

    for link in image_thumbnails:
        assert link in module.links


def test_transforming_content(import_command):
    """Applying markup conversions to content."""

    import_command.html2text = False
    import_command.transform_to_markdown = False
    import_command.transform_to_html = False
    import_command.use_wordpress_compiler = False
    import_command.translations_pattern = "{path}.{lang}.{ext}"

    transform_code = mock.MagicMock()
    transform_caption = mock.MagicMock()
    transform_newlines = mock.MagicMock()

    with mock.patch(
        "nikola.plugins.command.import_wordpress.CommandImportWordpress.transform_code",
        transform_code,
    ), mock.patch(
        "nikola.plugins.command.import_wordpress.CommandImportWordpress.transform_caption",
        transform_caption,
    ), mock.patch(
        "nikola.plugins.command.import_wordpress.CommandImportWordpress.transform_multiple_newlines",
        transform_newlines,
    ):
        import_command.transform_content("random content", "wp", None)

    assert transform_code.called
    assert transform_caption.called
    assert transform_newlines.called


def test_transforming_source_code(import_command):
    """
    Tests the handling of sourcecode tags.
    """
    content = """Hello World.
[sourcecode language="Python"]
import sys
print sys.version
[/sourcecode]"""

    content = import_command.transform_code(content)

    assert "[/sourcecode]" not in content
    assert "[sourcecode language=" not in content

    replaced_content = """Hello World.
```Python

import sys
print sys.version

```"""
    assert content == replaced_content


def test_transform_caption(import_command):
    caption = '[caption id="attachment_16" align="alignnone" width="739" caption="beautiful picture"]<img class="size-full wp-image-16" src="http://some.blog/wp-content/uploads/2009/07/caption_test.jpg" alt="beautiful picture" width="739" height="517" />[/caption]'
    transformed_content = import_command.transform_caption(caption)

    expected_content = '<img class="size-full wp-image-16" src="http://some.blog/wp-content/uploads/2009/07/caption_test.jpg" alt="beautiful picture" width="739" height="517" />'

    assert transformed_content == expected_content


def test_transform_multiple_captions_in_a_post(import_command):
    content = """asdasdas
[caption id="attachment_16" align="alignnone" width="739" caption="beautiful picture"]<img class="size-full wp-image-16" src="http://some.blog/wp-content/uploads/2009/07/caption_test.jpg" alt="beautiful picture" width="739" height="517" />[/caption]
asdasdas
asdasdas
[caption id="attachment_16" align="alignnone" width="739" caption="beautiful picture"]<img class="size-full wp-image-16" title="pretty" src="http://some.blog/wp-content/uploads/2009/07/caption_test.jpg" alt="beautiful picture" width="739" height="517" />[/caption]
asdasdas"""

    expected_content = """asdasdas
<img class="size-full wp-image-16" src="http://some.blog/wp-content/uploads/2009/07/caption_test.jpg" alt="beautiful picture" width="739" height="517" />
asdasdas
asdasdas
<img class="size-full wp-image-16" title="pretty" src="http://some.blog/wp-content/uploads/2009/07/caption_test.jpg" alt="beautiful picture" width="739" height="517" />
asdasdas"""

    assert expected_content == import_command.transform_caption(content)


def test_transform_multiple_newlines(import_command):
    content = """This


has



way to many

newlines.


"""
    expected_content = """This

has

way to many

newlines.

"""
    import_command.squash_newlines = False
    assert content == import_command.transform_multiple_newlines(content)

    import_command.squash_newlines = True
    assert expected_content == import_command.transform_multiple_newlines(content)


def test_transform_caption_with_link_inside(import_command):
    content = """[caption caption="Fehlermeldung"]<a href="http://some.blog/openttd-missing_sound.png"><img class="size-thumbnail wp-image-551" title="openttd-missing_sound" src="http://some.blog/openttd-missing_sound-150x150.png" alt="Fehlermeldung" /></a>[/caption]"""
    transformed_content = import_command.transform_caption(content)

    expected_content = """<a href="http://some.blog/openttd-missing_sound.png"><img class="size-thumbnail wp-image-551" title="openttd-missing_sound" src="http://some.blog/openttd-missing_sound-150x150.png" alt="Fehlermeldung" /></a>"""
    assert expected_content == transformed_content


def test_get_configuration_output_path(import_command):
    import_command.output_folder = "new_site"
    default_config_path = os.path.join("new_site", "conf.py")

    import_command.import_into_existing_site = False
    assert default_config_path == import_command.get_configuration_output_path()

    import_command.import_into_existing_site = True
    config_path_with_timestamp = import_command.get_configuration_output_path()

    assert default_config_path != config_path_with_timestamp
    assert import_command.name in config_path_with_timestamp


def test_write_content_does_not_detroy_text(import_command):
    content = b"""FOO"""
    open_mock = mock.mock_open()
    with mock.patch("nikola.plugins.basic_import.open", open_mock, create=True):
        import_command.write_content("some_file", content)

    open_mock.assert_has_calls(
        [
            mock.call(u"some_file", u"wb+"),
            mock.call().__enter__(),
            mock.call().write(b"<html><body><p>FOO</p></body></html>"),
            mock.call().__exit__(None, None, None),
        ]
    )


def test_configure_redirections(import_command):
    """
    Testing the configuration of the redirections.

    We need to make sure that we have valid sources and target links.
    """
    url_map = {"/somewhere/else": "http://foo.bar/posts/somewhereelse.html"}

    redirections = import_command.configure_redirections(url_map)

    assert 1 == len(redirections)
    assert ("somewhere/else/index.html", "/posts/somewhereelse.html") in redirections


@pytest.mark.parametrize(
    "options, additional_args",
    [
        pytest.param(None, None, id="only import filename"),
        ({"output_folder": "some_folder"}, None),
        (None, ["folder_argument"]),
    ],
)
def test_create_import(
    patched_import_command, import_filename, mocks, options, additional_args
):
    arguments = {"args": [import_filename]}
    if options:
        arguments["options"] = options
    if additional_args:
        arguments["args"].extend(additional_args)

    patched_import_command.execute(**arguments)

    for applied_mock in mocks:
        assert applied_mock.called

    assert patched_import_command.exclude_drafts is False


@pytest.mark.parametrize(
    "options",
    [
        {"exclude_drafts": True},
        {"exclude_drafts": True, "output_folder": "some_folder"},
    ],
)
def test_ignoring_drafts_during_import(
    patched_import_command, import_filename, options
):
    arguments = {"options": options, "args": [import_filename]}

    patched_import_command.execute(**arguments)
    assert patched_import_command.exclude_drafts is True


@pytest.fixture
def import_command(module):
    command = module.CommandImportWordpress()
    command.onefile = False
    return command


@pytest.fixture
def module():
    return nikola.plugins.command.import_wordpress


@pytest.fixture
def import_filename(test_dir):
    return os.path.abspath(
        os.path.join(
            test_dir, "data", "wordpress_import", "wordpress_export_example.xml"
        )
    )


@pytest.fixture
def patched_import_command(import_command, testsite, mocks):
    """
    Import command with disabled site generation and various functions mocked.
    """
    data_import, site_generation, write_urlmap, write_configuration = mocks

    import_command.site = testsite
    with mock.patch("os.system", site_generation), mock.patch(
        "nikola.plugins.command.import_wordpress.CommandImportWordpress.import_posts",
        data_import,
    ), mock.patch(
        "nikola.plugins.command.import_wordpress.CommandImportWordpress.write_urlmap_csv",
        write_urlmap,
    ), mock.patch(
        "nikola.plugins.command.import_wordpress.CommandImportWordpress.write_configuration",
        write_configuration,
    ):
        yield import_command


@pytest.fixture
def testsite():
    return FakeSite()


class FakeSite:
    def link(self, *args, **kwargs):
        # We need a link function.
        # Stubbed because there is nothing done with the results.
        pass


@pytest.fixture
def mocks():
    "Mocks to be used in `patched_import_command`"
    return [
        mock.MagicMock(name="data_import"),
        mock.MagicMock(name="site_generation"),
        mock.MagicMock(name="write_urlmap"),
        mock.MagicMock(name="write_configuration"),
    ]
