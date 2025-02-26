#!/usr/bin/env python

from pathlib import Path
import sys
import shutil
from setuptools import setup
from setuptools.command.install import install
from setuptools.command.build_py import build_py


def expands_symlinks_for_windows():
    """replaces the symlinked files with a copy of the original content.

    In windows (msysgit), a symlink is converted to a text file with a
    path to the file it points to. If not corrected, installing from a git
    clone will end with some files with bad content

    After install the working copy will be dirty (symlink markers overwritten
    with real content)
    """
    if sys.platform != "win32":
        return

    # apply the fix
    localdir = Path(__file__).resolve().parent
    oldpath = sys.path[:]
    sys.path.insert(0, str(localdir / 'nikola'))
    winutils = __import__('winutils')
    failures = winutils.fix_all_git_symlinked(localdir)
    sys.path = oldpath
    del sys.modules['winutils']
    if failures != -1:
        print(
            'WARNING: your working copy is now dirty by changes in '
            'samplesite, sphinx and themes'
        )
    if failures > 0:
        raise Exception(
            'Error: \n'
            '\tnot all symlinked files could be fixed.\n'
            '\tYour best bet is to start again from clean.'
        )


def remove_old_files(self):
    tree = Path(self.install_lib) / 'nikola'
    try:
        shutil.rmtree(tree, ignore_errors=True)
    except Exception:
        pass


class nikola_install(install):
    def run(self):
        expands_symlinks_for_windows()
        remove_old_files(self)
        install.run(self)


class nikola_build_py(build_py):
    def run(self):
        expands_symlinks_for_windows()
        build_py.run(self)

setup(
     cmdclass={'install': nikola_install, 'build_py': nikola_build_py},
)
