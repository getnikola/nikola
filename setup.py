#!/usr/bin/env python

# Don't use __future__ in this script, it breaks buildout
# from __future__ import print_function
import os
import sys
import shutil
from setuptools import setup, find_packages
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
if sys.version_info[0] == 2 and sys.version_info[1] < 7:
    raise Exception('Python 2 version < 2.7 is not supported')
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

    After install the working copy will be dirty (symlink markers overwritten
    with real content)
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
    if failures != -1:
        print('WARNING: your working copy is now dirty by changes in '
              'samplesite, sphinx and themes')
    if failures > 0:
        raise Exception("Error: \n\tnot all symlinked files could be fixed." +
                        "\n\tYour best bet is to start again from clean.")


def remove_old_files(self):
    tree = os.path.join(self.install_lib, 'nikola')
    try:
        shutil.rmtree(tree, ignore_errors=True)
    except:
        pass


class nikola_install(install):
    def run(self):
        expands_symlinks_for_windows()
        remove_old_files(self)
        install.run(self)


setup(name='Nikola',
      version='7.8.1',
      description='A modular, fast, simple, static website and blog generator',
      long_description=open('README.rst').read(),
      author='Roberto Alsina and others',
      author_email='ralsina@netmanagers.com.ar',
      url='https://getnikola.com/',
      packages=find_packages(exclude=('tests',)),
      license='MIT',
      keywords='website, blog, static',
      classifiers=('Development Status :: 5 - Production/Stable',
                   'Environment :: Console',
                   'Environment :: Plugins',
                   'Environment :: Web Environment',
                   'Intended Audience :: End Users/Desktop',
                   'License :: OSI Approved :: MIT License',
                   'Operating System :: MacOS',
                   'Operating System :: MacOS :: MacOS X',
                   'Operating System :: Microsoft :: Windows',
                   'Operating System :: OS Independent',
                   'Operating System :: POSIX',
                   'Operating System :: Unix',
                   'Programming Language :: Python',
                   'Programming Language :: Python :: 2.7',
                   'Programming Language :: Python :: 3.3',
                   'Programming Language :: Python :: 3.4',
                   'Programming Language :: Python :: 3.5',
                   'Topic :: Internet',
                   'Topic :: Internet :: WWW/HTTP',
                   'Topic :: Text Processing :: Markup'),
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
              ('share/man/man1', ['docs/man/nikola.1.gz']),
      ],
      entry_points={
          'console_scripts': [
              'nikola = nikola.__main__:main'
          ]
      },
      )
