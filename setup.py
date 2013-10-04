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
from fnmatch import fnmatchcase


try:
    # Prefer setuptools for the installation to have no problem with the
    # "--single-version-externally-managed" option that pip uses when
    # installing packages.
    from setuptools import setup
    from setuptools import convert_path

    from setuptools.command.install import install
except ImportError:
    print('\n*** setuptools not found! Falling back to distutils\n\n')
    from distutils.core import setup  # NOQA

    from distutils.command.install import install
    from distutils.util import convert_path  # NOQA

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
    if sys.platform == 'win32':
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


def find_package_data(
    where='.', package='',
    exclude=standard_exclude,
    exclude_directories=standard_exclude_directories,
    only_in_packages=True,
        show_ignored=False):
    """
    Return a dictionary suitable for use in ``package_data``
    in a distutils ``setup.py`` file.

    The dictionary looks like::

        {'package': [files]}

    Where ``files`` is a list of all the files in that package that
    don't match anything in ``exclude``.

    If ``only_in_packages`` is true, then top-level directories that
    are not packages won't be included (but directories under packages
    will).

    Directories matching any pattern in ``exclude_directories`` will
    be ignored; by default directories with leading ``.``, ``CVS``,
    and ``_darcs`` will be ignored.

    If ``show_ignored`` is true, then all the files that aren't
    included in package data are shown on stderr (for debugging
    purposes).

    Note patterns use wildcards, or can be exact paths (including
    leading ``./``), and all searching is case-insensitive.
    """

    out = {}
    stack = [(convert_path(where), '', package, only_in_packages)]
    while stack:
        where, prefix, package, only_in_packages = stack.pop(0)
        for name in os.listdir(where):
            fn = os.path.join(where, name)
            if os.path.isdir(fn):
                bad_name = False
                for pattern in exclude_directories:
                    if (fnmatchcase(name, pattern)
                            or fn.lower() == pattern.lower()):
                        bad_name = True
                        if show_ignored:
                            print >> sys.stderr, (
                                "Directory %s ignored by pattern %s"
                                % (fn, pattern))
                        break
                if bad_name:
                    continue
                if (os.path.isfile(os.path.join(fn, '__init__.py'))
                        and not prefix):
                    if not package:
                        new_package = name
                    else:
                        new_package = package + '.' + name
                    stack.append((fn, '', new_package, False))
                else:
                    stack.append((fn, prefix + name + '/',
                                  package, only_in_packages))
            elif package or not only_in_packages:
                # is a file
                bad_name = False
                for pattern in exclude:
                    if (fnmatchcase(name, pattern)
                            or fn.lower() == pattern.lower()):
                        bad_name = True
                        if show_ignored:
                            print >> sys.stderr, (
                                "File %s ignored by pattern %s"
                                % (fn, pattern))
                        break
                if bad_name:
                    continue
                out.setdefault(package, []).append(prefix + name)
    return out


setup(name='Nikola',
      version='6.1.0',
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
                'nikola.plugins.compile.misaka',
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
      package_data=find_package_data(),
      cmdclass={'install': nikola_install},
      data_files=[
              ('share/doc/nikola', [
               'docs/manual.txt',
               'docs/theming.txt',
               'docs/extending.txt']),
      ],
      )
