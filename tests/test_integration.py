import io
import os
import shutil
import sys
import tempfile
import unittest

import nikola
import nikola.plugins.command
import nikola.plugins.command.init
import nikola.utils
from nikola import __main__

from .base import BaseTestCase, cd, initialize_localeborg


class DemoBuildTest(BaseTestCase):
    """Test that a default build of --demo works."""

    @classmethod
    def setUpClass(cls):
        """Setup a demo site."""
        # for tests that need bilingual support override language_settings
        initialize_localeborg()
        cls.startdir = os.getcwd()
        cls.tmpdir = tempfile.mkdtemp()
        cls.target_dir = os.path.join(cls.tmpdir, "target")
        cls.init_command = nikola.plugins.command.init.CommandInit()
        cls.fill_site()
        cls.patch_site()
        cls.build()

    @classmethod
    def fill_site(self):
        """Fill the site with demo content."""
        self.init_command.copy_sample_site(self.target_dir)
        self.init_command.create_configuration(self.target_dir)
        src1 = os.path.join(os.path.dirname(__file__), 'data', '1-nolinks.rst')
        dst1 = os.path.join(self.target_dir, 'posts', '1.rst')
        shutil.copy(src1, dst1)
        # File for Issue #374 (empty post text)
        with io.open(os.path.join(self.target_dir, 'posts', 'empty.txt'), "w+", encoding="utf8") as outf:
            outf.write(
                ".. title: foobar\n"
                ".. slug: foobar\n"
                ".. date: 2013-03-06 19:08:15\n"
            )

    @classmethod
    def patch_site(self):
        """Make any modifications you need to the site."""

    @classmethod
    def build(self):
        """Build the site."""
        with cd(self.target_dir):
            __main__.main(["build"])

    @classmethod
    def tearDownClass(self):
        """Remove the demo site."""
        # Don't saw off the branch you're sitting on!
        os.chdir(self.startdir)
        # ignore_errors=True for windows by issue #782
        shutil.rmtree(self.tmpdir, ignore_errors=(sys.platform == 'win32'))
        # Fixes Issue #438
        try:
            del sys.modules['conf']
        except KeyError:
            pass
        # clear LocaleBorg state
        nikola.utils.LocaleBorg.reset()
        if hasattr(self.__class__, "ol"):
            delattr(self.__class__, "ol")

    def test_build(self):
        """Ensure the build did something."""
        index_path = os.path.join(
            self.target_dir, "output", "archive.html")
        self.assertTrue(os.path.isfile(index_path))

    def test_index_in_sitemap(self):
        sitemap_path = os.path.join(self.target_dir, "output", "sitemap.xml")
        with io.open(sitemap_path, "r", encoding="utf8") as inf:
            sitemap_data = inf.read()
        self.assertTrue(
            '<loc>https://example.com/</loc>'
            in sitemap_data)

    def test_avoid_double_slash_in_rss(self):
        rss_path = os.path.join(self.target_dir, "output", "rss.xml")
        with io.open(rss_path, "r", encoding="utf8") as inf:
            rss_data = inf.read()
        self.assertFalse('https://example.com//' in rss_data)


class TestCheckFailure(DemoBuildTest):
    """The demo build should pass 'nikola check'"""

    def test_check_links_fail(self):
        with cd(self.target_dir):
            os.unlink(os.path.join("output", "archive.html"))

            result = __main__.main(['check', '-l'])
            assert result != 0

    def test_check_files_fail(self):
        with cd(self.target_dir):
            with io.open(os.path.join("output", "foobar"), "w+", encoding="utf8") as outf:
                outf.write("foo")

            result = __main__.main(['check', '-f'])
            assert result != 0


if __name__ == "__main__":
    unittest.main()
