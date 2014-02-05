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

with open('requirements.txt', 'r') as fh:
    dependencies = [l.strip() for l in fh]

########### platform specific stuff #############
import platform
platform_system = platform.system()

scripts = ['scripts/nikola']
# platform specific scripts
if platform_system == "Windows":
    scripts.append('scripts/nikola.bat')

if sys.version_info[0] == 2 and sys.version_info[1] < 6:
    raise Exception('Python 2 version < 2.6 is not supported')
elif sys.version_info[0] == 3 and sys.version_info[1] < 3:
    raise Exception('Python 3 version < 3.3 is not supported')

##################################################

if sys.version_info[0] == 2:
    # in Python 3 this becomes a builtin, for Python 2 we need the backport
    dependencies.append('configparser')

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


def copy_symlinked_for_windows():
    """replaces the symlinked files with a copy of the original content.

    In windows (msysgit), a symlink is converted to a text file with a
    path to the file it points to. If not corrected, installing from a git
    clone will end with some files with bad content

    After install the WC will be dirty (symlink markers rewroted with real
    content)
    """

    # essentially nikola.utils.should_fix_git_symlinked inlined, to not
    # fiddle with sys.path / import unless really needed
    if sys.platform != 'win32':
        return
    path = (os.path.dirname(__file__) +
            r'nikola\data\samplesite\stories\theming.rst')
    try:
        if os.path.getsize(path) < 200:
            pass
        else:
            return
    except Exception:
        return

    # apply the fix
    localdir = os.path.dirname(__file__)
    dst = os.path.join(localdir, 'nikola', 'data', 'samplesite')
    src = dst
    oldpath = sys.path[:]
    sys.path.insert(0, os.path.join(localdir, 'nikola'))
    winutils = __import__('winutils')
    winutils.fix_git_symlinked(src, dst)
    sys.path = oldpath
    del sys.modules['winutils']
    print('WARNING: your working copy is now dirty by changes in samplesite')


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


class nikola_install(install):
    def run(self):
        copy_symlinked_for_windows()
        install.run(self)
        install_manpages(self.root, self.prefix)


setup(name='Nikola',
      version='6.3.0',
      description='A modular, fast, simple, static website generator',
      long_description=open('README.rst').read(),
      author='Roberto Alsina and others',
      author_email='ralsina@netmanagers.com.ar',
      url='http://getnikola.com',
      packages=['nikola',
                'nikola.plugins',
                'nikola.plugins.command',
                'nikola.plugins.command.planetoid',
                'nikola.plugins.compile',
                'nikola.plugins.compile.ipynb',
                'nikola.plugins.compile.markdown',
                'nikola.plugins.compile.rest',
                'nikola.plugins.task',
                'nikola.plugins.task.localsearch',
                'nikola.plugins.task.mustache',
                'nikola.plugins.task.sitemap',
                'nikola.plugins.template',
                ],
      license='MIT',
      keywords='website, static',
      scripts=scripts,
      classifiers=('Development Status :: 5 - Production/Stable',
                   'Environment :: Console',
                   'Environment :: Plugins',
                   'Environment :: Web Environment',
                   'Intended Audience :: End Users/Desktop',
                   'License :: OSI Approved :: MIT License',
                   'Operating System :: MacOS',
                   'Operating System :: Microsoft :: Windows',
                   'Operating System :: OS Independent',
                   'Operating System :: POSIX',
                   'Operating System :: Unix',
                   'Programming Language :: Python',
                   'Programming Language :: Python :: 2.6',
                   'Programming Language :: Python :: 2.7',
                   'Programming Language :: Python :: 3.3',
                   'Topic :: Internet',
                   'Topic :: Internet :: WWW/HTTP',
                   'Topic :: Text Processing :: Markup'),
      install_requires=dependencies,
      include_package_data=True,
      cmdclass={'install': nikola_install},
      data_files=[
              ('share/doc/nikola', [
               'docs/manual.txt',
               'docs/theming.txt',
               'docs/extending.txt']),
      ],
      )
