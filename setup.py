#!/usr/bin/env python

# find_package data is
# (c) 2005 Ian Bicking and contributors; written for Paste
# (http://pythonpaste.org)
# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license.php

# Don't use __future__ in this script, it breaks buildout
# from __future__ import print_function
import os
import subprocess
import sys
import shutil
from setuptools import setup
from setuptools.command.install import install
from setuptools.command.test import test as TestCommand


class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)


with open('requirements.txt', 'r') as fh:
    dependencies = [l.strip() for l in fh]

extras = {}

with open('requirements-extras.txt', 'r') as fh:
    extras['extras'] = [l.strip() for l in fh][1:]
    # Alternative name.
    extras['full'] = extras['extras']

with open('requirements-tests.txt', 'r') as fh:
    extras['tests'] = [l.strip() for l in fh][1:]

# ########## platform specific stuff #############
if sys.version_info[0] == 2 and sys.version_info[1] < 6:
    raise Exception('Python 2 version < 2.6 is not supported')
elif sys.version_info[0] == 3 and sys.version_info[1] < 3:
    raise Exception('Python 3 version < 3.3 is not supported')

##################################################

# Provided as an attribute, so you can append to these instead
# of replicating them:
standard_exclude = ('*.pyc', '*$py.class', '*~', '.*', '*.bak')
standard_exclude_directories = ('.*', 'CVS', '_darcs', './build',
                                './dist', 'EGG-INFO', '*.egg-info')


def copy_messages():
    themes_directory = os.path.join(
        os.path.dirname(__file__), 'nikola', 'data', 'themes')
    original_messages_directory = os.path.join(
        themes_directory, 'default', 'messages')

    for theme in ('orphan', 'monospace'):
        theme_messages_directory = os.path.join(
            themes_directory, theme, 'messages')

        if os.path.exists(theme_messages_directory):
            shutil.rmtree(theme_messages_directory)

        shutil.copytree(original_messages_directory, theme_messages_directory)


def expands_symlinks_for_windows():
    """replaces the symlinked files with a copy of the original content.

    In windows (msysgit), a symlink is converted to a text file with a
    path to the file it points to. If not corrected, installing from a git
    clone will end with some files with bad content

    After install the working copy  will be dirty (symlink markers rewroted with
    real content)
    """
    if sys.platform != 'win32':
        return

    # apply the fix
    localdir = os.path.dirname(os.path.abspath(__file__))
    oldpath = sys.path[:]
    sys.path.insert(0, os.path.join(localdir, 'nikola'))
    winutils = __import__('winutils')
    failures = winutils.fix_all_git_symlinked(localdir)
    sys.path = oldpath
    del sys.modules['winutils']
    print('WARNING: your working copy is now dirty by changes in samplesite, sphinx and themes')
    if failures:
        raise Exception("Error: \n\tnot all symlinked files could be fixed." +
                        "\n\tYour best bet is to start again from clean.")


def install_manpages(root, prefix):
    try:
        man_pages = [
            ('docs/man/nikola.1', 'share/man/man1/nikola.1'),
        ]
        join = os.path.join
        normpath = os.path.normpath
        if root is not None:
            prefix = os.path.realpath(root) + os.path.sep + prefix
        for src, dst in man_pages:
            path_dst = join(normpath(prefix), normpath(dst))
            try:
                os.makedirs(os.path.dirname(path_dst))
            except OSError:
                pass
            rst2man_cmd = ['rst2man.py', 'rst2man']
            for rst2man in rst2man_cmd:
                try:
                    subprocess.call([rst2man, src, path_dst])
                except OSError:
                    continue
                else:
                    break
    except Exception as e:
        print("Not installing the man pages:", e)


def remove_old_files(self):
    tree = os.path.join(self.install_lib, 'nikola')
    tree2 = os.path.join('build', 'lib', 'nikola')
    try:
        shutil.rmtree(tree, ignore_errors=True)
    except:
        pass

    try:
        shutil.rmtree(tree2, ignore_errors=True)
    except:
        pass


class nikola_install(install):
    def run(self):
        expands_symlinks_for_windows()
        remove_old_files(self)
        install.run(self)
        install_manpages(self.root, self.prefix)


setup(name='Nikola',
      version='7.0.1',
      description='A modular, fast, simple, static website generator',
      long_description=open('README.rst').read(),
      author='Roberto Alsina and others',
      author_email='ralsina@netmanagers.com.ar',
      url='http://getnikola.com',
      packages=['nikola',
                'nikola.plugins',
                'nikola.plugins.command',
                'nikola.plugins.compile',
                'nikola.plugins.compile.ipynb',
                'nikola.plugins.compile.markdown',
                'nikola.plugins.compile.rest',
                'nikola.plugins.task',
                'nikola.plugins.task.sitemap',
                'nikola.plugins.template',
                ],
      license='MIT',
      keywords='website, static',
      classifiers=(b'Development Status :: 5 - Production/Stable',
                   b'Environment :: Console',
                   b'Environment :: Plugins',
                   b'Environment :: Web Environment',
                   b'Intended Audience :: End Users/Desktop',
                   b'License :: OSI Approved :: MIT License',
                   b'Operating System :: MacOS',
                   b'Operating System :: Microsoft :: Windows',
                   b'Operating System :: OS Independent',
                   b'Operating System :: POSIX',
                   b'Operating System :: Unix',
                   b'Programming Language :: Python',
                   b'Programming Language :: Python :: 2.6',
                   b'Programming Language :: Python :: 2.7',
                   b'Programming Language :: Python :: 3.3',
                   b'Programming Language :: Python :: 3.4',
                   b'Topic :: Internet',
                   b'Topic :: Internet :: WWW/HTTP',
                   b'Topic :: Text Processing :: Markup'),
      install_requires=dependencies,
      extras_require=extras,
      tests_require=['pytest'],
      include_package_data=True,
      cmdclass={'install': nikola_install, 'test': PyTest},
      data_files=[
              ('share/doc/nikola', [
               'docs/manual.txt',
               'docs/theming.txt',
               'docs/extending.txt']),
      ],
      entry_points = {
          'console_scripts': [
              'nikola = nikola.__main__:main'
          ]
      },
      )
