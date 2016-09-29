# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

import os

import unittest
import mock

import nikola
import nikola.plugins.command.import_wordpress
from .base import BaseTestCase


class BasicCommandImportWordpress(BaseTestCase):
    def setUp(self):
        self.module = nikola.plugins.command.import_wordpress
        self.import_command = self.module.CommandImportWordpress()
        self.import_command.onefile = False
        self.import_filename = os.path.abspath(os.path.join(
            os.path.dirname(__file__), 'wordpress_export_example.xml'))

    def tearDown(self):
        del self.import_command
        del self.import_filename


class TestQTranslateContentSeparation(BasicCommandImportWordpress):

    def test_conserves_qtranslate_less_post(self):
        content = """Si vous préférez savoir à qui vous parlez commencez par visiter l'<a title="À propos" href="http://some.blog/about/">À propos</a>.

Quoiqu'il en soit, commentaires, questions et suggestions sont les bienvenues !"""
        content_translations = self.module.separate_qtranslate_content(content)
        self.assertEqual(1, len(content_translations))
        self.assertEqual(content, content_translations[""])

    def test_split_a_two_language_post(self):
        content = """<!--:fr-->Si vous préférez savoir à qui vous parlez commencez par visiter l'<a title="À propos" href="http://some.blog/about/">À propos</a>.

Quoiqu'il en soit, commentaires, questions et suggestions sont les bienvenues !
<!--:--><!--:en-->If you'd like to know who you're talking to, please visit the <a title="À propos" href="http://some.blog/about/">about page</a>.

Comments, questions and suggestions are welcome !
<!--:-->"""
        content_translations = self.module.separate_qtranslate_content(content)
        self.assertEqual("""Si vous préférez savoir à qui vous parlez commencez par visiter l'<a title="À propos" href="http://some.blog/about/">À propos</a>.

Quoiqu'il en soit, commentaires, questions et suggestions sont les bienvenues !
""", content_translations["fr"])
        self.assertEqual("""If you'd like to know who you're talking to, please visit the <a title="À propos" href="http://some.blog/about/">about page</a>.

Comments, questions and suggestions are welcome !
""", content_translations["en"])

    def test_split_a_two_language_post_with_teaser(self):
        content = """<!--:fr-->Si vous préférez savoir à qui vous parlez commencez par visiter l'<a title="À propos" href="http://some.blog/about/">À propos</a>.

Quoiqu'il en soit, commentaires, questions et suggestions sont les bienvenues !
<!--:--><!--:en-->If you'd like to know who you're talking to, please visit the <a title="À propos" href="http://some.blog/about/">about page</a>.

Comments, questions and suggestions are welcome !
<!--:--><!--more--><!--:fr-->
Plus de détails ici !
<!--:--><!--:en-->
More details here !
<!--:-->"""
        content_translations = self.module.separate_qtranslate_content(content)
        self.assertEqual("""Si vous préférez savoir à qui vous parlez commencez par visiter l'<a title="À propos" href="http://some.blog/about/">À propos</a>.

Quoiqu'il en soit, commentaires, questions et suggestions sont les bienvenues !
 <!--more--> \n\
Plus de détails ici !
""", content_translations["fr"])
        self.assertEqual("""If you'd like to know who you're talking to, please visit the <a title="À propos" href="http://some.blog/about/">about page</a>.

Comments, questions and suggestions are welcome !
 <!--more--> \n\
More details here !
""", content_translations["en"])

    def test_split_a_two_language_post_with_intermission(self):
        content = """<!--:fr-->Voila voila<!--:-->COMMON<!--:en-->BLA<!--:-->"""
        content_translations = self.module.separate_qtranslate_content(content)
        self.assertEqual("Voila voila COMMON", content_translations["fr"])
        self.assertEqual("COMMON BLA", content_translations["en"])

    def test_split_a_two_language_post_with_uneven_repartition(self):
        content = """<!--:fr-->Voila voila<!--:-->COMMON<!--:fr-->MOUF<!--:--><!--:en-->BLA<!--:-->"""
        content_translations = self.module.separate_qtranslate_content(content)
        self.assertEqual("Voila voila COMMON MOUF", content_translations["fr"])
        self.assertEqual("COMMON BLA", content_translations["en"])

    def test_split_a_two_language_post_with_uneven_repartition_bis(self):
        content = """<!--:fr-->Voila voila<!--:--><!--:en-->BLA<!--:-->COMMON<!--:fr-->MOUF<!--:-->"""
        content_translations = self.module.separate_qtranslate_content(content)
        self.assertEqual("Voila voila COMMON MOUF", content_translations["fr"])
        self.assertEqual("BLA COMMON", content_translations["en"])


class CommandImportWordpressRunTest(BasicCommandImportWordpress):
    def setUp(self):
        super(self.__class__, self).setUp()
        self.data_import = mock.MagicMock()
        self.site_generation = mock.MagicMock()
        self.write_urlmap = mock.MagicMock()
        self.write_configuration = mock.MagicMock()

        site_generation_patch = mock.patch('os.system', self.site_generation)
        data_import_patch = mock.patch(
            'nikola.plugins.command.import_wordpress.CommandImportWordpress.import_posts', self.data_import)
        write_urlmap_patch = mock.patch(
            'nikola.plugins.command.import_wordpress.CommandImportWordpress.write_urlmap_csv', self.write_urlmap)
        write_configuration_patch = mock.patch(
            'nikola.plugins.command.import_wordpress.CommandImportWordpress.write_configuration', self.write_configuration)

        self.patches = [site_generation_patch, data_import_patch,
                        write_urlmap_patch, write_configuration_patch]
        for patch in self.patches:
            patch.start()

    def tearDown(self):
        del self.data_import
        del self.site_generation
        del self.write_urlmap
        del self.write_configuration

        for patch in self.patches:
            patch.stop()
        del self.patches

        super(self.__class__, self).tearDown()

    def test_create_import(self):
        valid_import_arguments = (
            dict(options={'output_folder': 'some_folder'},
                 args=[self.import_filename]),
            dict(args=[self.import_filename]),
            dict(args=[self.import_filename, 'folder_argument']),
        )

        for arguments in valid_import_arguments:
            self.import_command.execute(**arguments)

            self.assertTrue(self.site_generation.called)
            self.assertTrue(self.data_import.called)
            self.assertTrue(self.write_urlmap.called)
            self.assertTrue(self.write_configuration.called)
            self.assertFalse(self.import_command.exclude_drafts)

    def test_ignoring_drafts(self):
        valid_import_arguments = (
            dict(options={'exclude_drafts': True}, args=[
                 self.import_filename]),
            dict(
                options={'exclude_drafts': True,
                         'output_folder': 'some_folder'},
                args=[self.import_filename]),
        )

        for arguments in valid_import_arguments:
            self.import_command.execute(**arguments)
            self.assertTrue(self.import_command.exclude_drafts)


class CommandImportWordpressTest(BasicCommandImportWordpress):
    def test_create_import_work_without_argument(self):
        # Running this without an argument must not fail.
        # It should show the proper usage of the command.
        self.import_command.execute()

    def test_populate_context(self):
        channel = self.import_command.get_channel_from_file(
            self.import_filename)
        self.import_command.html2text = False
        self.import_command.transform_to_markdown = False
        self.import_command.transform_to_html = False
        self.import_command.use_wordpress_compiler = False
        context = self.import_command.populate_context(channel)

        for required_key in ('POSTS', 'PAGES', 'COMPILERS'):
            self.assertTrue(required_key in context)

        self.assertEqual('de', context['DEFAULT_LANG'])
        self.assertEqual('Wordpress blog title', context['BLOG_TITLE'])
        self.assertEqual('Nikola test blog ;) - with moré Ümläüts',
                         context['BLOG_DESCRIPTION'])
        self.assertEqual('http://some.blog/', context['SITE_URL'])
        self.assertEqual('mail@some.blog', context['BLOG_EMAIL'])
        self.assertEqual('Niko', context['BLOG_AUTHOR'])

    def test_importing_posts_and_attachments(self):
        channel = self.import_command.get_channel_from_file(
            self.import_filename)
        self.import_command.base_dir = ''
        self.import_command.output_folder = 'new_site'
        self.import_command.squash_newlines = True
        self.import_command.no_downloads = False
        self.import_command.export_categories_as_categories = False
        self.import_command.export_comments = False
        self.import_command.html2text = False
        self.import_command.transform_to_markdown = False
        self.import_command.transform_to_html = False
        self.import_command.use_wordpress_compiler = False
        self.import_command.tag_saniziting_strategy = 'first'
        self.import_command.context = self.import_command.populate_context(
            channel)

        # Ensuring clean results
        self.import_command.url_map = {}
        self.module.links = {}

        write_metadata = mock.MagicMock()
        write_content = mock.MagicMock()
        write_post = mock.MagicMock()
        write_attachments_info = mock.MagicMock()
        download_mock = mock.MagicMock()

        with mock.patch('nikola.plugins.command.import_wordpress.CommandImportWordpress.write_content', write_content):
            with mock.patch('nikola.plugins.command.import_wordpress.CommandImportWordpress.write_metadata', write_metadata):
                with mock.patch('nikola.plugins.command.import_wordpress.CommandImportWordpress.download_url_content_to_file', download_mock):
                    with mock.patch('nikola.plugins.command.import_wordpress.CommandImportWordpress.write_attachments_info', write_attachments_info):
                        with mock.patch('nikola.plugins.command.import_wordpress.os.makedirs'):
                            self.import_command.import_posts(channel)

        self.assertTrue(download_mock.called)
        qpath = 'new_site/files/wp-content/uploads/2008/07/arzt_und_pfusch-sick-cover.png'
        download_mock.assert_any_call(
            'http://some.blog/wp-content/uploads/2008/07/arzt_und_pfusch-sick-cover.png',
            qpath.replace('/', os.sep))

        self.assertTrue(write_metadata.called)
        write_metadata.assert_any_call(
            'new_site/pages/kontakt.meta'.replace('/', os.sep), 'Kontakt',
            'kontakt', '2009-07-16 20:20:32', '', [], **{'wp-status': 'publish'})

        self.assertTrue(write_content.called)
        write_content.assert_any_call('new_site/posts/2007/04/hoert.md'.replace('/', os.sep),
                                      """An image.

<img class="size-full wp-image-16" title="caption test" src="http://some.blog/wp-content/uploads/2009/07/caption_test.jpg" alt="caption test" width="739" height="517" />

Some source code.

```Python

import sys
print sys.version

```

The end.
""", True)

        self.assertTrue(write_attachments_info.called)
        write_attachments_info.assert_any_call('new_site/posts/2008/07/arzt-und-pfusch-s-i-c-k.attachments.json'.replace('/', os.sep),
                                               {10: {'wordpress_user_name': 'Niko',
                                                     'files_meta': [{'width': 300, 'height': 299},
                                                                    {'width': 150, 'size': 'thumbnail', 'height': 150}],
                                                     'excerpt': 'Arzt+Pfusch - S.I.C.K.',
                                                     'date_utc': '2009-07-16 19:40:37',
                                                     'content': 'Das Cover von Arzt+Pfusch - S.I.C.K.',
                                                     'files': ['/wp-content/uploads/2008/07/arzt_und_pfusch-sick-cover.png',
                                                               '/wp-content/uploads/2008/07/arzt_und_pfusch-sick-cover-150x150.png'],
                                                     'title': 'Arzt+Pfusch - S.I.C.K.'}})

        write_content.assert_any_call(
            'new_site/posts/2008/07/arzt-und-pfusch-s-i-c-k.md'.replace('/', os.sep),
            '''<img class="size-full wp-image-10 alignright" title="Arzt+Pfusch - S.I.C.K." src="http://some.blog/wp-content/uploads/2008/07/arzt_und_pfusch-sick-cover.png" alt="Arzt+Pfusch - S.I.C.K." width="210" height="209" />Arzt+Pfusch - S.I.C.K.Gerade bin ich \xfcber das Album <em>S.I.C.K</em> von <a title="Arzt+Pfusch" href="http://www.arztpfusch.com/" target="_blank">Arzt+Pfusch</a> gestolpert, welches Arzt+Pfusch zum Download f\xfcr lau anbieten. Das Album steht unter einer Creative Commons <a href="http://creativecommons.org/licenses/by-nc-nd/3.0/de/">BY-NC-ND</a>-Lizenz.
Die Ladung <em>noisebmstupidevildustrial</em> gibts als MP3s mit <a href="http://www.archive.org/download/dmp005/dmp005_64kb_mp3.zip">64kbps</a> und <a href="http://www.archive.org/download/dmp005/dmp005_vbr_mp3.zip">VBR</a>, als Ogg Vorbis und als FLAC (letztere <a href="http://www.archive.org/details/dmp005">hier</a>). <a href="http://www.archive.org/download/dmp005/dmp005-artwork.zip">Artwork</a> und <a href="http://www.archive.org/download/dmp005/dmp005-lyrics.txt">Lyrics</a> gibts nochmal einzeln zum Download.''', True)
        write_content.assert_any_call(
            'new_site/pages/kontakt.md'.replace('/', os.sep), """<h1>Datenschutz</h1>
Ich erhebe und speichere automatisch in meine Server Log Files Informationen, die dein Browser an mich \xfcbermittelt. Dies sind:
<ul>
    <li>Browsertyp und -version</li>
    <li>verwendetes Betriebssystem</li>
    <li>Referrer URL (die zuvor besuchte Seite)</li>
    <li>IP Adresse des zugreifenden Rechners</li>
    <li>Uhrzeit der Serveranfrage.</li>
</ul>
Diese Daten sind f\xfcr mich nicht bestimmten Personen zuordenbar. Eine Zusammenf\xfchrung dieser Daten mit anderen Datenquellen wird nicht vorgenommen, die Daten werden einzig zu statistischen Zwecken erhoben.""", True)

        self.assertTrue(len(self.import_command.url_map) > 0)

        self.assertEqual(
            self.import_command.url_map['http://some.blog/2007/04/hoert/'],
            'http://some.blog/posts/2007/04/hoert.html')
        self.assertEqual(
            self.import_command.url_map[
                'http://some.blog/2008/07/arzt-und-pfusch-s-i-c-k/'],
            'http://some.blog/posts/2008/07/arzt-und-pfusch-s-i-c-k.html')
        self.assertEqual(
            self.import_command.url_map['http://some.blog/kontakt/'],
            'http://some.blog/pages/kontakt.html')

        image_thumbnails = [
            'http://some.blog/wp-content/uploads/2012/12/2012-12-19-1355925145_1024x600_scrot-64x64.png',
            'http://some.blog/wp-content/uploads/2012/12/2012-12-19-1355925145_1024x600_scrot-300x175.png',
            'http://some.blog/wp-content/uploads/2012/12/2012-12-19-1355925145_1024x600_scrot-36x36.png',
            'http://some.blog/wp-content/uploads/2012/12/2012-12-19-1355925145_1024x600_scrot-24x24.png',
            'http://some.blog/wp-content/uploads/2012/12/2012-12-19-1355925145_1024x600_scrot-96x96.png',
            'http://some.blog/wp-content/uploads/2012/12/2012-12-19-1355925145_1024x600_scrot-96x96.png',
            'http://some.blog/wp-content/uploads/2012/12/2012-12-19-1355925145_1024x600_scrot-48x48.png',
            'http://some.blog/wp-content/uploads/2012/12/2012-12-19-1355925145_1024x600_scrot-96x96.png',
            'http://some.blog/wp-content/uploads/2012/12/2012-12-19-1355925145_1024x600_scrot-150x150.png'
        ]

        for link in image_thumbnails:
            self.assertTrue(
                link in self.module.links,
                'No link to "{0}" found in {map}.'.format(
                    link,
                    map=self.module.links
                )
            )

    def test_transforming_content(self):
        """Applying markup conversions to content."""
        transform_code = mock.MagicMock()
        transform_caption = mock.MagicMock()
        transform_newlines = mock.MagicMock()

        self.import_command.html2text = False
        self.import_command.transform_to_markdown = False
        self.import_command.transform_to_html = False
        self.import_command.use_wordpress_compiler = False

        with mock.patch('nikola.plugins.command.import_wordpress.CommandImportWordpress.transform_code', transform_code):
            with mock.patch('nikola.plugins.command.import_wordpress.CommandImportWordpress.transform_caption', transform_caption):
                with mock.patch('nikola.plugins.command.import_wordpress.CommandImportWordpress.transform_multiple_newlines', transform_newlines):
                    self.import_command.transform_content("random content", "wp", None)

        self.assertTrue(transform_code.called)
        self.assertTrue(transform_caption.called)
        self.assertTrue(transform_newlines.called)

    def test_transforming_source_code(self):
        """
        Tests the handling of sourcecode tags.
        """
        content = """Hello World.
[sourcecode language="Python"]
import sys
print sys.version
[/sourcecode]"""

        content = self.import_command.transform_code(content)

        self.assertFalse('[/sourcecode]' in content)
        self.assertFalse('[sourcecode language=' in content)

        replaced_content = """Hello World.
```Python

import sys
print sys.version

```"""
        self.assertEqual(content, replaced_content)

    def test_transform_caption(self):
        caption = '[caption id="attachment_16" align="alignnone" width="739" caption="beautiful picture"]<img class="size-full wp-image-16" src="http://some.blog/wp-content/uploads/2009/07/caption_test.jpg" alt="beautiful picture" width="739" height="517" />[/caption]'
        transformed_content = self.import_command.transform_caption(caption)

        expected_content = '<img class="size-full wp-image-16" src="http://some.blog/wp-content/uploads/2009/07/caption_test.jpg" alt="beautiful picture" width="739" height="517" />'

        self.assertEqual(transformed_content, expected_content)

    def test_transform_multiple_captions_in_a_post(self):
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

        self.assertEqual(
            expected_content, self.import_command.transform_caption(content))

    def test_transform_multiple_newlines(self):
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
        self.import_command.squash_newlines = False
        self.assertEqual(content,
                         self.import_command.transform_multiple_newlines(content))

        self.import_command.squash_newlines = True
        self.assertEqual(expected_content,
                         self.import_command.transform_multiple_newlines(content))

    def test_transform_caption_with_link_inside(self):
        content = """[caption caption="Fehlermeldung"]<a href="http://some.blog/openttd-missing_sound.png"><img class="size-thumbnail wp-image-551" title="openttd-missing_sound" src="http://some.blog/openttd-missing_sound-150x150.png" alt="Fehlermeldung" /></a>[/caption]"""
        transformed_content = self.import_command.transform_caption(content)

        expected_content = """<a href="http://some.blog/openttd-missing_sound.png"><img class="size-thumbnail wp-image-551" title="openttd-missing_sound" src="http://some.blog/openttd-missing_sound-150x150.png" alt="Fehlermeldung" /></a>"""
        self.assertEqual(expected_content, transformed_content)

    def test_get_configuration_output_path(self):
        self.import_command.output_folder = 'new_site'
        default_config_path = os.path.join('new_site', 'conf.py')

        self.import_command.import_into_existing_site = False
        self.assertEqual(default_config_path,
                         self.import_command.get_configuration_output_path())

        self.import_command.import_into_existing_site = True
        config_path_with_timestamp = self.import_command.get_configuration_output_path(
        )
        self.assertNotEqual(default_config_path, config_path_with_timestamp)
        self.assertTrue(self.import_command.name in config_path_with_timestamp)

    def test_write_content_does_not_detroy_text(self):
        content = b"""FOO"""
        open_mock = mock.mock_open()
        with mock.patch('nikola.plugins.basic_import.open', open_mock, create=True):
            self.import_command.write_content('some_file', content)

        open_mock.assert_has_calls([
            mock.call(u'some_file', u'wb+'),
            mock.call().__enter__(),
            mock.call().write(b'<html><body><p>FOO</p></body></html>'),
            mock.call().__exit__(None, None, None)]
        )

    def test_configure_redirections(self):
        """
        Testing the configuration of the redirections.

        We need to make sure that we have valid sources and target links.
        """
        url_map = {
            '/somewhere/else': 'http://foo.bar/posts/somewhereelse.html'
        }

        redirections = self.import_command.configure_redirections(url_map)

        self.assertEqual(1, len(redirections))
        self.assertTrue(('somewhere/else/index.html', '/posts/somewhereelse.html') in redirections)


if __name__ == '__main__':
    unittest.main()
