#!/bin/bash
# generates a list of symlinked files and directories.
# each line must be the file path relative to the git root 
WDir="${PWD##*/}"
if [ $WDir != scripts ]; then
	echo "Error, Script must be run from scripts directory. Nothing done."
	exit 1
fi	
cd ..
dst='nikola/data/symlinked.txt'
git ls-files -s | awk '/120000/{print $4}' > $dst
