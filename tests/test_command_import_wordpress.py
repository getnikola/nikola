from context import nikola
import os
import unittest
import mock


class CommandImportWordpressTest(unittest.TestCase):
    def setUp(self):
        self.import_command = nikola.plugins.command_import_wordpress.CommandImportWordpress()
        self.import_filename = os.path.abspath(
            os.path.join(os.path.dirname(__file__),
                         'wordpress_export_example.xml'))

    def tearDown(self):
        del self.import_command
        del self.import_filename

    def test_create_import_work_without_argument(self):
        # Running this without an argument must not fail.
        # It should show the proper usage of the command.
        self.import_command.run()

    def test_create_import(self):
        data_import = mock.MagicMock()
        site_generation = mock.MagicMock()
        write_urlmap = mock.MagicMock()
        write_configuration = mock.MagicMock()

        with mock.patch('nikola.plugins.command_import_wordpress.CommandImportWordpress.generate_base_site', site_generation):
            with mock.patch('nikola.plugins.command_import_wordpress.CommandImportWordpress.import_posts', data_import):
                with mock.patch('nikola.plugins.command_import_wordpress.CommandImportWordpress.write_urlmap_csv', write_urlmap):
                    with mock.patch('nikola.plugins.command_import_wordpress.CommandImportWordpress.write_configuration', write_configuration):
                        self.import_command.run(self.import_filename)

        self.assertTrue(site_generation.called)
        self.assertTrue(data_import.called)

    def test_populate_context(self):
        channel = self.import_command.get_channel_from_file(
            self.import_filename)
        context = self.import_command.populate_context(channel)

        for required_key in ('POST_PAGES', 'POST_COMPILERS'):
            self.assertTrue(required_key in context)

        self.assertEqual('de', context['DEFAULT_LANG'])
        self.assertEqual('Wordpress blog title', context['BLOG_TITLE'])
        self.assertEqual('Nikola test blog ;)', context['BLOG_DESCRIPTION'])
        self.assertEqual('http://some.blog', context['BLOG_URL'])
        self.assertEqual('mail@some.blog', context['BLOG_EMAIL'])
        self.assertEqual('Niko', context['BLOG_AUTHOR'])

    def test_importing_posts_and_attachments(self):
        channel = self.import_command.get_channel_from_file(
            self.import_filename)
        self.import_command.context = self.import_command.populate_context(
            channel)
        self.import_command.url_map = {}  # For testing we use an empty one.

        write_metadata = mock.MagicMock()
        write_content = mock.MagicMock()
        download_mock = mock.MagicMock()

        with mock.patch('nikola.plugins.command_import_wordpress.CommandImportWordpress.write_content', write_content):
            with mock.patch('nikola.plugins.command_import_wordpress.CommandImportWordpress.write_metadata', write_metadata):
                with mock.patch('nikola.plugins.command_import_wordpress.CommandImportWordpress.download_url_content_to_file', download_mock):
                    with mock.patch('nikola.plugins.command_import_wordpress.os.makedirs'):
                        self.import_command.import_posts(channel)

        self.assertTrue(download_mock.called)
        download_mock.assert_any_call(u'http://some.blog/wp-content/uploads/2008/07/arzt_und_pfusch-sick-cover.png', u'new_site/files/wp-content/uploads/2008/07/arzt_und_pfusch-sick-cover.png')

        self.assertTrue(write_metadata.called)
        write_metadata.assert_any_call(u'new_site/stories/kontakt.meta', 'Kontakt', u'kontakt', '2009-07-16 20:20:32', None, [])

        self.assertTrue(write_content.called)
        write_content.assert_any_call(u'new_site/posts/200704hoert.wp', '...!\n\n\n\n[caption id="attachment_16" align="alignnone" width="739" caption="caption test"]<img class="size-full wp-image-16" title="caption test" src="http://some.blog/wp-content/uploads/2009/07/caption_test.jpg" alt="caption test" width="739" height="517" />[/caption]\n\n\n\nNicht, dass daran jemals Zweifel bestanden.')
        write_content.assert_any_call(u'new_site/posts/200807arzt-und-pfusch-s-i-c-k.wp', u'<img class="size-full wp-image-10 alignright" title="Arzt+Pfusch - S.I.C.K." src="http://some.blog/wp-content/uploads/2008/07/arzt_und_pfusch-sick-cover.png" alt="Arzt+Pfusch - S.I.C.K." width="210" height="209" />Arzt+Pfusch - S.I.C.K.Gerade bin ich \xfcber das Album <em>S.I.C.K</em> von <a title="Arzt+Pfusch" href="http://www.arztpfusch.com/" target="_blank">Arzt+Pfusch</a> gestolpert, welches Arzt+Pfusch zum Download f\xfcr lau anbieten. Das Album steht unter einer Creative Commons <a href="http://creativecommons.org/licenses/by-nc-nd/3.0/de/">BY-NC-ND</a>-Lizenz.\n\nDie Ladung <em>noisebmstupidevildustrial</em> gibts als MP3s mit <a href="http://www.archive.org/download/dmp005/dmp005_64kb_mp3.zip">64kbps</a> und <a href="http://www.archive.org/download/dmp005/dmp005_vbr_mp3.zip">VBR</a>, als Ogg Vorbis und als FLAC (letztere <a href="http://www.archive.org/details/dmp005">hier</a>). <a href="http://www.archive.org/download/dmp005/dmp005-artwork.zip">Artwork</a> und <a href="http://www.archive.org/download/dmp005/dmp005-lyrics.txt">Lyrics</a> gibts nochmal einzeln zum Download.')
        write_content.assert_any_call(u'new_site/stories/kontakt.wp', u'<h1>Datenschutz</h1>\n\nIch erhebe und speichere automatisch in meine Server Log Files Informationen, die dein Browser an mich \xfcbermittelt. Dies sind:\n\n<ul>\n\n    <li>Browsertyp und -version</li>\n\n    <li>verwendetes Betriebssystem</li>\n\n    <li>Referrer URL (die zuvor besuchte Seite)</li>\n\n    <li>IP Adresse des zugreifenden Rechners</li>\n\n    <li>Uhrzeit der Serveranfrage.</li>\n\n</ul>\n\nDiese Daten sind f\xfcr mich nicht bestimmten Personen zuordenbar. Eine Zusammenf\xfchrung dieser Daten mit anderen Datenquellen wird nicht vorgenommen, die Daten werden einzig zu statistischen Zwecken erhoben.')

        self.assertTrue(len(self.import_command.url_map) > 0)

        self.assertEqual(self.import_command.url_map['http://some.blog/2007/04/hoert/'], u'http://some.blog/posts/200704hoert.html')
        self.assertEqual(self.import_command.url_map['http://some.blog/2008/07/arzt-und-pfusch-s-i-c-k/'], u'http://some.blog/posts/200807arzt-und-pfusch-s-i-c-k.html')
        self.assertEqual(self.import_command.url_map['http://some.blog/kontakt/'], u'http://some.blog/stories/kontakt.html')


if __name__ == '__main__':
    unittest.main()
