# -*- coding: utf-8 -*-
"""
Script to test the import workflow.

It will remove an existing Nikola installation and then install from the
package directory.
After that it will do create a new site with the import_wordpress
command and use that newly created site to make a build.
"""
from __future__ import unicode_literals, print_function

import os
import shutil

TEST_SITE_DIRECTORY = 'import_test_site'


def main(import_directory=None):
    if import_directory is None:
        import_directory = TEST_SITE_DIRECTORY

    if os.path.exists(import_directory):
        print('deleting %s' % import_directory)
        shutil.rmtree(import_directory)

    test_directory = os.path.dirname(__file__)
    package_directory = os.path.abspath(os.path.join(test_directory, '..'))

    os.system('pip uninstall -y Nikola')
    os.system('pip install %s' % package_directory)
    os.system('nikola')
    import_file = os.path.join(test_directory, 'wordpress_export_example.xml')
    os.system(
        'nikola import_wordpress -o {folder} {file}'.format(file=import_file,
                                                            folder=import_directory))

    assert os.path.exists(
        import_directory), "The directory %s should be existing."
    os.chdir(import_directory)
    os.system('nikola build')


if __name__ == '__main__':
    main()
