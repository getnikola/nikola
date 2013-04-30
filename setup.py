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

dependencies = [
    'doit>=0.20.0',
    'pygments',
    'pillow',
    'docutils',
    'mako>=0.6',
    'unidecode',
    'lxml',
    'yapsy',
    'PyRSS2Gen',
    'pytz',
]

########### platform specific stuff #############
import platform
platform_system = platform.system()

scripts = ['scripts/nikola']
# platform specific scripts
if platform_system == "Windows":
    scripts.append('scripts/nikola.bat')

##################################################

if sys.version_info[0] == 2:
    # in Python 3 this becomes a builtin, for Python 2 we need the backport
    dependencies.append('configparser')
elif sys.version_info[0] == 3:
    # Pillow introduced support for Python 3 with 2.0.0
    dependencies.remove('pillow')
    dependencies.append('pillow>=2.0.0')

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
      version='5.4.4',
      description='Static blog/website generator',
      author='Roberto Alsina and others',
      author_email='ralsina@netmanagers.com.ar',
      url='http://nikola.ralsina.com.ar/',
      packages=['nikola',
                'nikola.plugins',
                'nikola.plugins.command_planetoid',
                'nikola.plugins.compile_ipynb',
                'nikola.plugins.compile_markdown',
                'nikola.plugins.compile_misaka',
                'nikola.plugins.compile_rest',
                'nikola.plugins.task_localsearch',
                'nikola.plugins.task_mustache',
                'nikola.plugins.task_sitemap',
                ],
      scripts=scripts,
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
