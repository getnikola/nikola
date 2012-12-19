from context import nikola
import os
import unittest
import mock


class CommandImportWordpressTest(unittest.TestCase):
    def setUp(self):
        self.import_command = nikola.plugins.command_import_wordpress.CommandImportWordpress()

    def tearDown(self):
        del self.import_command

    def test_create_import_work_without_argument(self):
        self.import_command.run()

    def test_create_import(self):
        import_filename = os.path.abspath(
            os.path.join(os.path.dirname(__file__),
                         'wordpress_export_example.xml'))

        with mock.patch('nikola.plugins.command_import_wordpress.CommandImportWordpress.generate_base_site'):
            with mock.patch('nikola.plugins.command_import_wordpress.CommandImportWordpress.import_posts'):
                self.import_command.run(import_filename)

if __name__ == '__main__':
    unittest.main()
