#!/bin/bash
# Generate a list of symlinked files and directories.
# Each line must be the file path, relative to the git root.

WDir="${PWD##*/}"
[[ $WDir == 'scripts' ]] && cd ..

dst='nikola/data/symlinked.txt'

# Remove stale symlinks
for f in $(git ls-files -s | awk '/120000/{print $4}'); do
    if [[ ! -e $f ]]; then
        git rm -f $f
    fi
done

git ls-files -s | awk '/120000/{print $4}' > $dst
