#!/usr/bin/env python
import subprocess
import sys
import os

if not os.path.exists('.pypt/gh-token'):
    print("To use this script, you must create a GitHub token first.")
    print("Get a token here: https://github.com/settings/tokens")
    print("Then, put it in a file named .pypt/gh-token")
    exit(1)

inpf = input if sys.version_info[0] == 3 else raw_input

FILE = inpf("Markdown file to use: ")
BASEDIR = os.getcwd()
REPO = 'getnikola/nikola'
TAG = inpf("Tag name (usually vX.Y.Z): ")

subprocess.call(['.pypt/ghrel', FILE, BASEDIR, REPO, TAG])
