#!/bin/bash
# Generate a list of symlinked files and directories.
# Each line must be the file path, relative to the git root.

WDir="${PWD##*/}"
[[ $WDir == 'scripts' ]] && cd ..

dst='nikola/data/symlinked.txt'
git ls-files -s | awk '/120000/{print $4}' > $dst
