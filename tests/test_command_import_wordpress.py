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

        with mock.patch('nikola.plugins.command_import_wordpress.CommandImportWordpress.generate_base_site', site_generation):
            with mock.patch('nikola.plugins.command_import_wordpress.CommandImportWordpress.import_posts', data_import):
                self.import_command.run(self.import_filename)

        self.assertTrue(site_generation.called)
        self.assertTrue(data_import.called)

    def test_populate_context(self):
        channel = self.import_command.get_channel_from_file(self.import_filename)
        context = self.import_command.populate_context(channel)

        for required_key in ('POST_PAGES', 'POST_COMPILERS'):
            self.assertTrue(required_key in context)

        self.assertEqual('de', context['DEFAULT_LANG'])
        self.assertEqual('Wordpress blog title', context['BLOG_TITLE'])
        self.assertEqual('Nikola test blog ;)', context['BLOG_DESCRIPTION'])
        self.assertEqual('http://some.blog', context['BLOG_URL'])
        self.assertEqual('mail@some.blog', context['BLOG_EMAIL'])
        self.assertEqual('Niko', context['BLOG_AUTHOR'])

if __name__ == '__main__':
    unittest.main()
